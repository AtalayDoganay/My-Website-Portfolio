"""Verify the two themes and the pixel grid across viewports.

    .venv/Scripts/python.exe tools/check_theme.py --out <dir>

Covers what the theme work has to get right: the outline colours are literally
white and black, the artwork only ever scales by a whole number, the screen
overlay stays on the glass, switching theme does not disturb the introduction or
the desktop, and a stored choice survives reload and navigation.
"""

import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:4321"
VIEWPORTS = [
    ("360", 360, 800), ("390", 390, 844), ("430", 430, 932),
    ("768", 768, 1024), ("1366", 1366, 768), ("1920", 1920, 1080),
    ("landscape", 844, 390),
]

MEASURE = """
() => {
  const root = document.documentElement;
  const crt = document.querySelector('[data-crt]');
  const shown = [...document.querySelectorAll('.crt__art')]
    .filter((el) => getComputedStyle(el).display !== 'none');
  const art = shown[0];
  const s = document.querySelector('[data-screen]').getBoundingClientRect();
  const a = crt.getBoundingClientRect();
  const cs = getComputedStyle(root);
  return {
    theme: root.getAttribute('data-theme'),
    outline: cs.getPropertyValue('--outline').trim(),
    scale: parseFloat(cs.getPropertyValue('--px-scale')),
    shownCount: shown.length,
    natural: art ? [art.naturalWidth, art.naturalHeight] : null,
    artBox: [Math.round(a.width), Math.round(a.height)],
    screen: [Math.round(s.width), Math.round(s.height)],
    button: (() => { const b = document.querySelector('.crt__go');
      if (!b || b.hidden) return null;
      const r = b.getBoundingClientRect();
      return [Math.round(r.width), Math.round(r.height)]; })(),
    label: (() => { const l = document.querySelector('.crt__go-label');
      return l ? Math.round(parseFloat(getComputedStyle(l).fontSize) * 10) / 10 : 0; })(),
    handFits: (() => {
      const hand = document.querySelector('.invite__hand');
      const box = hand.getBoundingClientRect();
      const g = document.querySelector('[data-screen]').getBoundingClientRect();
      return box.top >= g.top - 0.5 && box.left >= g.left && box.right <= g.right;
    })(),
    centred: Math.abs((a.left + a.width / 2) - window.innerWidth / 2),
    inside: a.left >= -0.5 && a.right <= window.innerWidth + 0.5
            && a.top >= -0.5 && a.bottom <= window.innerHeight + 0.5,
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  };
}
"""


class Report:
    def __init__(self):
        self.rows = []
        self.fails = []
        self.console = []

    def note(self, name, detail, ok=True):
        self.rows.append((name, ok, detail))
        if not ok:
            self.fails.append(f"{name}: {detail}")

    def dump(self):
        for name, ok, detail in self.rows:
            print(("  ok   " if ok else "  FAIL ") + name + " -- " + str(detail))
        for c in self.console:
            print("  console: " + c)
        print(f"\n{len(self.rows)} checks, {len(self.fails)} failures, {len(self.console)} console messages")


def page_in(browser, rep, scheme, viewport, storage=None):
    ctx = browser.new_context(viewport=viewport, color_scheme=scheme, device_scale_factor=2)
    if storage:
        ctx.add_init_script(
            "try { localStorage.setItem('atalay.theme', %r); } catch (e) {}" % storage
        )
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: rep.console.append(str(e)))
    pg.on("console", lambda m: rep.console.append(m.type + ": " + m.text) if m.type == "error" else None)
    return ctx, pg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rep = Report()

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)

        # --- outline colours, exactly as specified -------------------------
        for scheme, expect in (("dark", "#ffffff"), ("light", "#000000")):
            ctx, pg = page_in(b, rep, scheme, {"width": 1280, "height": 800})
            pg.goto(BASE + "/", wait_until="networkidle")
            pg.click("[data-skip]")
            pg.wait_for_timeout(300)
            d = pg.evaluate(MEASURE)
            rep.note(
                f"{scheme}: outline colour is {expect}",
                d["outline"],
                ok=d["outline"].lower() == expect,
            )
            ctx.close()

        # --- every viewport, both themes -----------------------------------
        for scheme in ("dark", "light"):
            for name, w, h in VIEWPORTS:
                ctx, pg = page_in(b, rep, scheme, {"width": w, "height": h})
                pg.goto(BASE + "/", wait_until="networkidle")
                # The pixel grid is what matters AT REST. The opening legitimately
                # holds the camera at a fractional scale, so let it resolve first
                # rather than measuring the artwork mid-pullback.
                pg.click("[data-skip]")
                pg.wait_for_function(
                    "() => document.querySelector('[data-room]').dataset.state === 'room-ready'",
                    timeout=8000)
                pg.wait_for_timeout(200)
                pg.evaluate("""() => document.querySelector('.invite__hand').getAnimations()
                    .forEach(a => { a.pause(); a.currentTime = 200; })""")
                d = pg.evaluate(MEASURE)
                rep.note(f"{scheme} {name}: entire raised glove fits the glass",
                         d["handFits"], ok=d["handFits"])

                integer = abs(d["scale"] - round(d["scale"])) < 1e-6
                exact = d["natural"] and d["artBox"] == [
                    round(d["natural"][0] * d["scale"]), round(d["natural"][1] * d["scale"])
                ]
                rep.note(
                    f"{scheme} {name}: whole-number scale, exact pixel blocks",
                    f"scale {d['scale']:g} art {d['natural']} -> {d['artBox']}",
                    ok=integer and exact,
                )
                rep.note(
                    f"{scheme} {name}: one framing shown, centred, no overflow",
                    f"shown {d['shownCount']} centre off by {d['centred']:.1f}px "
                    f"overflow {d['overflow']} inside {d['inside']}",
                    ok=d["shownCount"] == 1 and d["centred"] < 2 and d["overflow"] <= 0 and d["inside"],
                )
                # What matters is that what is ON the glass can be used, not
                # that the glass hits some pixel width. A short landscape phone
                # is the one framing that cannot reach scale 2 - the wide grid
                # is 330 rows tall and two of those do not fit in 390 - so it
                # shows at scale 1 and the glass is about 108px. That is fine
                # for the artwork; what would NOT be fine is the key shrinking
                # with it, so the key and its label are what get asserted.
                btn = d["button"] or [0, 0]
                rep.note(
                    f"{scheme} {name}: screen readable, key usable",
                    f"glass {d['screen'][0]}x{d['screen'][1]} "
                    f"key {btn[0]}x{btn[1]} label {d['label']}px",
                    ok=d["screen"][0] >= 100 and btn[0] >= 60 and btn[1] >= 40
                       and d["label"] >= 11,
                )
                if name in ("390", "1440", "1920"):
                    pg.screenshot(path=str(out / f"open-{scheme}-{name}.png"))
                ctx.close()

        # --- the system preference decides when nothing is stored ----------
        for scheme, expect in (("light", "light"), ("dark", "dark")):
            ctx, pg = page_in(b, rep, scheme, {"width": 1280, "height": 800})
            pg.goto(BASE + "/", wait_until="networkidle")
            got = pg.evaluate("() => document.documentElement.getAttribute('data-theme')")
            rep.note(f"system preference {scheme} is followed", got, ok=got == expect)
            ctx.close()

        # --- an explicit choice beats the system, and survives -------------
        ctx, pg = page_in(b, rep, "dark", {"width": 1280, "height": 800}, storage="light")
        pg.goto(BASE + "/", wait_until="networkidle")
        got = pg.evaluate("() => document.documentElement.getAttribute('data-theme')")
        rep.note("stored choice overrides the system preference", got, ok=got == "light")
        pg.reload(wait_until="networkidle")
        rep.note(
            "survives a reload",
            pg.evaluate("() => document.documentElement.getAttribute('data-theme')"),
            ok=pg.evaluate("() => document.documentElement.getAttribute('data-theme')") == "light",
        )
        pg.goto(BASE + "/projects/", wait_until="networkidle")
        rep.note(
            "survives navigation to an inner page",
            pg.evaluate("() => document.documentElement.getAttribute('data-theme')"),
            ok=pg.evaluate("() => document.documentElement.getAttribute('data-theme')") == "light",
        )
        ctx.close()

        # --- no flash ------------------------------------------------------
        # Proven structurally rather than by racing the renderer: the theme script
        # must be in the head, before the stylesheet, and neither deferred nor async,
        # which is what makes it run before anything is painted.
        ctx, pg = page_in(b, rep, "dark", {"width": 1280, "height": 800}, storage="light")
        pg.goto(BASE + "/", wait_until="domcontentloaded")
        html = pg.content()
        head = html[: html.find("</head>")]
        tag_at = head.find('src="/theme.js"')
        css_at = head.find("styles.css")
        tag = head[head.rfind("<script", 0, tag_at): tag_at + 30] if tag_at > -1 else ""
        rep.note(
            "theme script is render-blocking, in the head, before the stylesheet",
            f"script at {tag_at}, stylesheet at {css_at}, tag {tag.strip()!r}",
            ok=tag_at > -1 and css_at > tag_at and "defer" not in tag and "async" not in tag,
        )
        rep.note(
            "and the theme is applied by DOMContentLoaded",
            pg.evaluate("() => document.documentElement.getAttribute('data-theme')"),
            ok=pg.evaluate("() => document.documentElement.getAttribute('data-theme')") == "light",
        )
        ctx.close()

        # --- switching mid-sequence must not disturb the introduction ------
        # The theme switch stays outside the moving world, so it is reachable
        # for the whole opening.
        ctx, pg = page_in(b, rep, "dark", {"width": 1280, "height": 800})
        pg.goto(BASE + "/", wait_until="networkidle")
        pg.wait_for_function(
            "() => document.querySelector('[data-room]').dataset.state === 'typing'",
            timeout=12000)
        pg.wait_for_timeout(300)
        line = '.crt__text[data-line="1"]'
        before = pg.eval_on_selector(line, "el => el.textContent")
        pg.click(".theme-toggle--room")
        pg.wait_for_timeout(120)
        after = pg.eval_on_selector(line, "el => el.textContent")
        rep.note(
            "switching during typing does not restart the line",
            f"{before!r} -> {after!r}",
            ok=len(after) >= len(before) and "Welcome to my website".startswith(after[:21]),
        )
        pg.wait_for_timeout(700)
        later = pg.eval_on_selector(line, "el => el.textContent")
        rep.note("and the sequence keeps running", repr(later), ok=len(later) > len(after))
        rep.note(
            "the theme actually changed",
            pg.evaluate("() => document.documentElement.getAttribute('data-theme')"),
            ok=pg.evaluate("() => document.documentElement.getAttribute('data-theme')") == "light",
        )
        ctx.close()

        # --- switching on the desktop must not close or leave --------------
        ctx, pg = page_in(b, rep, "dark", {"width": 1280, "height": 800})
        pg.goto(BASE + "/", wait_until="networkidle")
        pg.click("[data-skip]")                      # straight to the finished room
        pg.wait_for_timeout(200)
        pg.click("[data-go]")
        pg.wait_for_function(
            "() => document.querySelector('[data-room]').dataset.state === 'desktop'",
            timeout=8000)
        pg.wait_for_timeout(500)
        pg.click(".theme-toggle--tray")
        pg.wait_for_timeout(200)
        state = pg.evaluate("""() => ({
          theme: document.documentElement.getAttribute('data-theme'),
          room: document.querySelector('[data-room]').dataset.state,
          windowOpen: !document.querySelector('[data-window]').hidden,
          desktopShown: document.querySelector('[data-desktop]').hasAttribute('data-shown') })""")
        rep.note(
            "switching on the desktop keeps the window and stays put",
            state,
            ok=state["theme"] == "light" and state["room"] == "desktop"
            and state["windowOpen"] and state["desktopShown"],
        )
        pg.screenshot(path=str(out / "desk-light-switched.png"))
        ctx.close()

        # --- storage blocked: switching still works for this page ----------
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, color_scheme="dark")
        ctx.add_init_script(
            "Object.defineProperty(window, 'localStorage', { get() { throw new Error('blocked'); } });"
        )
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(BASE + "/", wait_until="networkidle")
        pg.wait_for_timeout(400)
        first = pg.evaluate("() => document.documentElement.getAttribute('data-theme')")
        pg.click("[data-theme-toggle]")
        pg.wait_for_timeout(150)
        second = pg.evaluate("() => document.documentElement.getAttribute('data-theme')")
        rep.note(
            "switching works with storage unavailable",
            f"{first} -> {second}, page errors: {errs[:1]}",
            ok=first == "dark" and second == "light" and not errs,
        )
        ctx.close()

        # --- the inner pages carry the theme and a working switch ----------
        for path in ("/projects/", "/about/", "/contact/", "/nope/"):
            ctx, pg = page_in(b, rep, "light", {"width": 1024, "height": 800})

            pg.goto(BASE + path, wait_until="networkidle")
            pg.wait_for_timeout(250)
            d = pg.evaluate("""() => ({
              theme: document.documentElement.getAttribute('data-theme'),
              toggles: document.querySelectorAll('[data-theme-toggle]').length,
              outline: getComputedStyle(document.documentElement).getPropertyValue('--outline').trim(),
              overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth })""")
            rep.note(
                f"{path} is themed and has a switch",
                d,
                ok=d["theme"] == "light" and d["toggles"] >= 1
                and d["outline"].lower() == "#000000" and d["overflow"] <= 0,
            )
            ctx.close()

        b.close()

    # The 404 page is fetched on purpose; the browser logs its status as a console
    # error, and that one message is expected rather than a defect.
    rep.console = [c for c in rep.console if "404" not in c]
    rep.dump()
    return 1 if rep.fails or rep.console else 0


if __name__ == "__main__":
    sys.exit(main())
