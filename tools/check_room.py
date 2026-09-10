"""Drive the opening scene in a real browser and report what actually happened.

Walks the whole sequence: typing, the three periods, deletion, the name, hover
during typing, pointer leave, keyboard entry, touch entry, repeated clicks mid
transition, desktop arrival, return, replay, mobile layout and reduced motion.

    .venv/Scripts/python.exe tools/check_room.py --out <dir> [--only NAME]

Written for the project-local `webapp-testing` skill. It reports observations; it
does not assert anything it did not measure.
"""

import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:4321"
DESKTOP = {"width": 1440, "height": 900}
PHONE = {"width": 390, "height": 844}

READOUT = "[data-line]"
SCREEN = "[data-screen]"


def line_text(page):
    return page.eval_on_selector(READOUT, "el => el.textContent")


def state(page):
    return page.eval_on_selector("[data-room]", "el => el.dataset.state")


def screen_box(page):
    return page.eval_on_selector(
        SCREEN, "el => { const r = el.getBoundingClientRect();"
        " return {x: r.x, y: r.y, w: r.width, h: r.height}; }"
    )


class Report:
    def __init__(self):
        self.rows = []
        self.console = []
        self.failures = []

    def note(self, name, detail, ok=True):
        self.rows.append({"check": name, "ok": ok, "detail": detail})
        if not ok:
            self.failures.append(f"{name}: {detail}")

    def dump(self):
        for r in self.rows:
            print(("  ok   " if r["ok"] else "  FAIL ") + r["check"] + " -- " + str(r["detail"]))
        if self.console:
            print("\nconsole:")
            for c in self.console:
                print("   " + c)
        print(
            "\n{} checks, {} failures, {} console messages".format(
                len(self.rows), len(self.failures), len(self.console)
            )
        )


def open_page(ctx, rep, path="/"):
    page = ctx.new_page()
    page.on(
        "console",
        lambda m: rep.console.append("{}: {}".format(m.type, m.text))
        if m.type in ("error", "warning")
        else None,
    )
    page.on("pageerror", lambda e: rep.console.append("pageerror: {}".format(e)))
    page.goto(BASE + path, wait_until="networkidle")
    return page


# Installed before any page script runs, so every frame of the sequence is recorded
# with a timestamp. Sampling from the test process would measure the test's own
# latency instead of the animation's.
RECORDER = """
window.__frames = [];
document.addEventListener('DOMContentLoaded', () => {
  const el = document.querySelector('[data-line]');
  if (!el) return;
  const push = () => window.__frames.push([performance.now(), el.textContent]);
  new MutationObserver(push).observe(el, { childList: true, characterData: true, subtree: true });
  push();
});
"""


def median(xs):
    s = sorted(xs)
    return s[len(s) // 2] if s else 0


def check_sequence(ctx, rep, out):
    """Typing, the three periods, the hold, deletion, and the name -- measured."""
    page = ctx.new_page()
    page.on(
        "console",
        lambda m: rep.console.append("{}: {}".format(m.type, m.text))
        if m.type in ("error", "warning")
        else None,
    )
    page.on("pageerror", lambda e: rep.console.append("pageerror: {}".format(e)))
    page.add_init_script(RECORDER)
    page.goto(BASE + "/", wait_until="networkidle")

    page.wait_for_timeout(500)
    page.screenshot(path=str(out / "01-opening.png"))

    page.wait_for_function(
        "() => document.querySelector('[data-line]').textContent === 'Welcome to my website...'",
        timeout=10000,
    )
    page.screenshot(path=str(out / "02-periods.png"))

    page.wait_for_function(
        "() => document.querySelector('[data-line]').textContent === 'Hii, my name is Atalay Doganay...'",
        timeout=20000,
    )
    page.wait_for_timeout(300)
    page.screenshot(path=str(out / "03-introduced.png"))

    frames = page.evaluate("() => window.__frames")
    values = [v for _, v in frames]
    line1 = "Welcome to my website"
    full1 = line1 + "..."
    line2 = "Hii, my name is Atalay Doganay..."

    # The hold is a real step in the sequence, and re-setting textContent to the same
    # string still fires a mutation, so it shows up as a repeated frame. That repeat
    # is exactly where the 900 ms pause lives.
    expected = (
        [line1[:i] for i in range(1, len(line1) + 1)]
        + [line1 + ".", line1 + "..", full1]
        + [full1]  # the hold
        + [full1[:i] for i in range(len(full1) - 1, -1, -1)]
        + [line2[:i] for i in range(1, len(line2) + 1)]
    )
    # Drop the initial empty frame the recorder pushes on attach.
    observed = [v for v in values if v != ""] if values and values[0] == "" else values
    observed_core = observed[: len(expected)]
    exp_core = [v for v in expected if v != ""]

    rep.note(
        "every frame of the sequence is exactly right",
        "{} frames recorded, first mismatch: {}".format(
            len(observed),
            next(
                (
                    "#{} {!r} != {!r}".format(i, a, b)
                    for i, (a, b) in enumerate(zip(observed_core, exp_core))
                    if a != b
                ),
                "none",
            ),
        ),
        ok=observed_core[: len(exp_core)] == exp_core,
    )

    # Measured intervals, by phase.
    def deltas(pred):
        out_ = []
        for i in range(1, len(frames)):
            if pred(values[i - 1], values[i]):
                out_.append(frames[i][0] - frames[i - 1][0])
        return out_

    typing = deltas(lambda a, b: line1.startswith(b) and len(b) == len(a) + 1)
    typing2 = deltas(lambda a, b: line2.startswith(b) and len(b) == len(a) + 1 and len(a) > 0)
    periods = deltas(lambda a, b: b.startswith(line1) and b.endswith(".") and len(b) == len(a) + 1 and len(a) >= len(line1))
    deleting = deltas(lambda a, b: len(b) == len(a) - 1 and full1.startswith(a))
    holds = deltas(lambda a, b: a == full1 and b == full1)

    rep.note(
        "typing runs at about 85 ms per character",
        "line 1 median {:.0f} ms (n={}), line 2 median {:.0f} ms (n={})".format(
            median(typing), len(typing), median(typing2), len(typing2)
        ),
        ok=60 <= median(typing) <= 130 and 60 <= median(typing2) <= 130,
    )
    rep.note(
        "each trailing period takes about 450 ms",
        "median {:.0f} ms (n={})".format(median(periods), len(periods)),
        ok=len(periods) == 3 and 380 <= median(periods) <= 560,
    )
    rep.note(
        "the finished line is held before erasing",
        "{:.0f} ms".format(median(holds)),
        ok=700 <= median(holds) <= 1200,
    )
    rep.note(
        "deletion runs at about 45 ms per character",
        "median {:.0f} ms (n={})".format(median(deleting), len(deleting)),
        ok=25 <= median(deleting) <= 90,
    )
    rep.note(
        "caret blinks once the machine is resting",
        page.eval_on_selector("[data-room]", "el => el.dataset.typing"),
        ok=page.eval_on_selector("[data-room]", "el => el.dataset.typing") == "resting",
    )

    # No wrapping and no overflow inside the glass.
    fits = page.eval_on_selector(
        "[data-line]",
        "el => { const r = el.getBoundingClientRect();"
        " const g = el.closest('.crt__glass').getBoundingClientRect();"
        " return { lines: Math.round(r.height / parseFloat(getComputedStyle(el).lineHeight)),"
        "          overflowRight: Math.round(r.right - g.right) }; }",
    )
    rep.note(
        "introduction stays on one line inside the glass",
        fits,
        ok=fits["lines"] <= 1 and fits["overflowRight"] < 0,
    )
    page.close()


def check_hover(ctx, rep, out):
    """Hover mid-sequence swaps the message, pauses, and resumes from the same point."""
    page = open_page(ctx, rep)
    page.wait_for_timeout(700)

    before = line_text(page)
    page.hover(SCREEN)
    page.wait_for_timeout(220)
    hovered = line_text(page)
    rep.note(
        "hover replaces the message with the invitation",
        repr(hovered),
        ok=hovered == "Click to know about me",
    )
    page.screenshot(path=str(out / "04-hover.png"))

    # Held: the sequence must not advance underneath.
    page.wait_for_timeout(1200)
    still = line_text(page)
    rep.note("sequence is paused while hovered", repr(still), ok=still == "Click to know about me")

    page.mouse.move(10, 10)
    page.wait_for_timeout(120)
    restored = line_text(page)
    rep.note(
        "pointer leave restores the previous text, not a restart",
        "before={!r} after={!r}".format(before, restored),
        ok=restored.startswith(before) and len(restored) >= len(before),
    )

    page.wait_for_timeout(500)
    resumed = line_text(page)
    rep.note(
        "resumes from the same point",
        repr(resumed),
        ok=len(resumed) > len(restored) and "Welcome to my website".startswith(resumed[:21]),
    )

    # Hover during deletion, too.
    page.wait_for_function(
        "() => { const t = document.querySelector('[data-line]').textContent;"
        " return t.length > 5 && t.length < 20 && 'Welcome to my website...'.startsWith(t); }",
        timeout=20000,
    )
    during_delete = line_text(page)
    page.hover(SCREEN)
    page.wait_for_timeout(250)
    rep.note(
        "hover during deletion also holds",
        repr(line_text(page)),
        ok=line_text(page) == "Click to know about me",
    )
    page.mouse.move(10, 10)
    page.wait_for_timeout(80)
    rep.note(
        "deletion resumes where it stopped",
        "held={!r} back={!r}".format(during_delete, line_text(page)),
        ok=len(line_text(page)) <= len(during_delete),
    )
    page.close()


def check_enter(ctx, rep, out, label="desktop"):
    """The flight into the screen, midpoint included."""
    page = open_page(ctx, rep)
    page.wait_for_timeout(600)

    box = screen_box(page)
    view = page.viewport_size
    rep.note(
        "screen sits on the left of the scene",
        "screen centre x={:.0f} of {}".format(box["x"] + box["w"] / 2, view["width"]),
        ok=(box["x"] + box["w"] / 2) < view["width"] * 0.55,
    )

    page.click(SCREEN)
    page.wait_for_timeout(60)
    rep.note("click moves to the entering state", state(page), ok=state(page) == "entering")

    # Sample the live transform while the flight is running. Anything that takes
    # time (screenshots, extra clicks) has to happen after this, or the transition
    # has already landed and the measurement is of nothing.
    scale_js = (
        "() => { const el = document.querySelector('[data-world]');"
        " const t = getComputedStyle(el).transform;"
        " if (!t || t === 'none') return { scale: 1, raw: t };"
        " const m = new DOMMatrixReadOnly(t); return { scale: m.a, tx: m.e, ty: m.f }; }"
    )
    # Sample only. A screenshot here takes long enough for the flight to land, and
    # the samples after it would then be reading the cleared transform.
    samples = []
    for _ in range(7):
        samples.append(page.evaluate(scale_js)["scale"])
        page.wait_for_timeout(130)
    rep.note(
        "the room scales up around the screen, continuously",
        "scale over ~900 ms: " + ", ".join("{:.2f}".format(s) for s in samples),
        ok=all(a <= b for a, b in zip(samples, samples[1:])) and samples[-1] > 2.0,
    )

    # Repeated activation during the transition must not start a second one.
    for _ in range(4):
        page.click(SCREEN, force=True)
    rep.note(
        "repeated clicks during the transition are ignored",
        state(page),
        ok=state(page) in ("entering", "gone"),
    )

    page.wait_for_function("() => document.querySelector('[data-room]').dataset.state === 'gone'",
                           timeout=6000)
    page.wait_for_timeout(500)
    rep.note("arrives at the desktop", state(page), ok=state(page) == "gone")
    shown = page.eval_on_selector(
        "[data-desktop]",
        "el => ({ hidden: el.hidden, inert: el.hasAttribute('inert'),"
        " opacity: getComputedStyle(el).opacity })",
    )
    rep.note(
        "desktop is visible and interactive",
        shown,
        ok=not shown["hidden"] and not shown["inert"] and float(shown["opacity"]) > 0.95,
    )
    page.screenshot(path=str(out / "06-desktop-{}.png".format(label)))

    clock = page.eval_on_selector("[data-clock]", "el => el.textContent")
    rep.note("taskbar clock shows a real time", repr(clock), ok=bool(clock and ":" in clock))

    # No leftover transform, so nothing is left scaled and blurry.
    left_over = page.eval_on_selector("[data-world]", "el => el.style.transform")
    rep.note("scaled layer is released on arrival", repr(left_over), ok=left_over == "")

    # Start menu, then back to the room.
    page.click("[data-start]")
    page.wait_for_timeout(150)
    rep.note(
        "Start opens a real menu",
        page.eval_on_selector("[data-start]", "el => el.getAttribute('aria-expanded')"),
        ok=page.eval_on_selector("[data-start-menu]", "el => !el.hidden"),
    )
    page.screenshot(path=str(out / "07-start-menu.png"))

    page.click("[data-leave]")
    page.wait_for_timeout(200)
    rep.note("Back to the room returns", state(page), ok=state(page) == "intro")
    rep.note(
        "the introduction restarts cleanly",
        repr(line_text(page)),
        ok=len(line_text(page)) < 8,
    )

    page.wait_for_timeout(900)
    replay = line_text(page)
    rep.note(
        "and replays",
        repr(replay),
        ok=bool(replay) and "Welcome to my website".startswith(replay),
    )

    # Second entry works.
    page.click(SCREEN)
    page.wait_for_function("() => document.querySelector('[data-room]').dataset.state === 'gone'",
                           timeout=6000)
    rep.note("can be entered a second time", state(page), ok=state(page) == "gone")
    page.close()

    # A frame from mid-flight, captured on its own page at a light device scale so
    # the screenshot itself does not outlast the transition it is meant to show.
    shot_ctx = ctx.browser.new_context(viewport=DESKTOP, device_scale_factor=1)
    shot = open_page(shot_ctx, rep)
    shot.wait_for_timeout(500)
    shot.click(SCREEN)
    shot.wait_for_timeout(560)  # before the desktop begins to fade in at 60%
    mid = shot.evaluate(scale_js)
    shot.screenshot(path=str(out / "05-transition-{}.png".format(label)))
    rep.note(
        "midpoint frame captured mid-flight",
        "scale {:.2f} when the frame was taken".format(mid["scale"]),
        ok=1.2 < mid["scale"] < 6,
    )
    shot.close()
    shot_ctx.close()


def check_keyboard(ctx, rep, out):
    page = open_page(ctx, rep)
    page.wait_for_timeout(500)
    page.keyboard.press("Tab")
    page.wait_for_timeout(200)
    focused = page.evaluate("() => document.activeElement.getAttribute('aria-label')")
    rep.note("the screen is the first tab stop", repr(focused), ok=focused == "Enter the computer")
    rep.note(
        "keyboard focus shows the same invitation",
        repr(line_text(page)),
        ok=line_text(page) == "Click to know about me",
    )
    ring = page.eval_on_selector(
        SCREEN, "el => getComputedStyle(el).outlineWidth + ' ' + getComputedStyle(el).outlineColor"
    )
    rep.note("focus ring is visible", ring, ok=not ring.startswith("0px"))
    page.screenshot(path=str(out / "08-keyboard-focus.png"))

    page.keyboard.press("Enter")
    page.wait_for_function("() => document.querySelector('[data-room]').dataset.state === 'gone'",
                           timeout=6000)
    rep.note("Enter activates it", state(page), ok=state(page) == "gone")

    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    rep.note("Escape returns to the room", state(page), ok=state(page) == "intro")
    page.close()

    # Space, on a fresh page.
    page2 = open_page(ctx, rep)
    page2.wait_for_timeout(400)
    page2.keyboard.press("Tab")
    page2.keyboard.press(" ")
    page2.wait_for_function("() => document.querySelector('[data-room]').dataset.state === 'gone'",
                            timeout=6000)
    rep.note("Space activates it", state(page2), ok=state(page2) == "gone")
    page2.close()


def check_touch(browser, rep, out):
    ctx = browser.new_context(
        viewport=PHONE, has_touch=True, is_mobile=True, device_scale_factor=2
    )
    page = open_page(ctx, rep)
    page.wait_for_timeout(600)
    hint = page.eval_on_selector("[data-hint]", "el => el.textContent")
    shown = page.eval_on_selector(
        "[data-hint]", "el => getComputedStyle(el).opacity"
    )
    rep.note(
        "touch shows a persistent invitation",
        "{!r} at opacity {}".format(hint, shown),
        ok=hint == "Tap to know about me" and float(shown) > 0.5,
    )
    overflow = page.evaluate(
        "() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth })"
    )
    rep.note(
        "no horizontal overflow on a phone",
        overflow,
        ok=overflow["sw"] <= overflow["cw"] + 1,
    )
    box = screen_box(page)
    rep.note(
        "screen is a comfortable tap target",
        "{:.0f}x{:.0f}".format(box["w"], box["h"]),
        ok=box["w"] >= 120 and box["h"] >= 90,
    )
    page.screenshot(path=str(out / "09-phone-opening.png"), full_page=False)

    page.tap(SCREEN)
    page.wait_for_function("() => document.querySelector('[data-room]').dataset.state === 'gone'",
                           timeout=6000)
    page.wait_for_timeout(400)
    rep.note("a single tap enters", state(page), ok=state(page) == "gone")
    bar = page.eval_on_selector(
        ".taskbar", "el => { const r = el.getBoundingClientRect();"
        " return { bottom: Math.round(r.bottom), vh: window.innerHeight }; }"
    )
    rep.note("taskbar sits on the bottom edge", bar, ok=abs(bar["bottom"] - bar["vh"]) <= 1)
    page.screenshot(path=str(out / "10-phone-desktop.png"))
    page.close()
    ctx.close()


def check_reduced_motion(browser, rep, out):
    ctx = browser.new_context(viewport=DESKTOP, reduced_motion="reduce")
    page = open_page(ctx, rep)
    page.wait_for_timeout(700)
    rep.note(
        "reduced motion shows the introduction without typing",
        repr(line_text(page)),
        ok=line_text(page) == "Hii, my name is Atalay Doganay...",
    )
    caret = page.eval_on_selector(".crt__caret", "el => getComputedStyle(el).animationName")
    rep.note("caret does not blink under reduced motion", caret, ok=caret == "none")
    page.screenshot(path=str(out / "11-reduced-motion.png"))

    page.click(SCREEN)
    page.wait_for_function("() => document.querySelector('[data-room]').dataset.state === 'gone'",
                           timeout=4000)
    rep.note("reduced motion arrives without the zoom", state(page), ok=state(page) == "gone")
    page.close()
    ctx.close()


def check_other_pages(ctx, rep):
    """The rest of the site must be untouched by this work."""
    for path, marker in [("/projects/", "BALL FIGHTERS"), ("/about/", "Orange Coast College"),
                         ("/contact/", "GitHub")]:
        page = open_page(ctx, rep, path)
        has_nav = page.eval_on_selector_all(".nav__link", "els => els.length")
        body = page.eval_on_selector("main", "el => el.textContent")
        rep.note(
            "{} still renders with site chrome".format(path),
            "{} nav links, marker present: {}".format(has_nav, marker in body),
            ok=has_nav == 4 and marker in body,
        )
        page.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rep = Report()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=DESKTOP, device_scale_factor=2)

        runs = {
            "sequence": lambda: check_sequence(ctx, rep, out),
            "hover": lambda: check_hover(ctx, rep, out),
            "enter": lambda: check_enter(ctx, rep, out),
            "keyboard": lambda: check_keyboard(ctx, rep, out),
            "touch": lambda: check_touch(browser, rep, out),
            "reduced": lambda: check_reduced_motion(browser, rep, out),
            "others": lambda: check_other_pages(ctx, rep),
        }
        for name, fn in runs.items():
            if args.only and args.only != name:
                continue
            try:
                fn()
            except Exception as err:  # keep going; a stuck check should not hide the rest
                rep.note(name, "raised {}: {}".format(type(err).__name__, err), ok=False)

        ctx.close()
        browser.close()

    rep.dump()
    return 1 if rep.failures or rep.console else 0


if __name__ == "__main__":
    sys.exit(main())
