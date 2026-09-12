"""Verify that the portfolio lamps light on the demonstrated press, and capture them.

    .venv/Scripts/python.exe tools/check_lamps.py --out artifacts/lamps \
        --evidence docs/evidence/lamps/after

What it measures, rather than assumes:

  - the lamp animations share the hand animation's start time and duration,
    so they run on the press's own clock;
  - in REAL TIME, the frame the key goes down is the frame the lamps begin to
    light, and across three consecutive cycles that offset does not drift;
  - the lit hold lasts about 200ms and the fade is done about 200ms later;
  - a real activation lights them too;
  - hover and keyboard focus keep a lamp lit; the rest state passes contrast;
  - after entering the desktop no lamp can take focus; under reduced motion
    they are steady and usable, with no animation running.

It writes the captures the review needs: rest, peak and faded, both themes,
desktop and phone, and three peaks taken from live cycles. Run `node serve.mjs`
first.
"""
import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:4321"
PARK = """ms => document.querySelectorAll(
      '.invite, .invite *, .crt__fx, .crt__fx *, .crt__go, .crt__go-face, .lamp')
    .forEach(el => el.getAnimations({subtree: true}).forEach(a => { a.pause(); a.currentTime = ms; }))"""
LIT = "sel => parseFloat(getComputedStyle(document.querySelector(sel)).getPropertyValue('--lit')) || 0"
SAMPLE = """ms => new Promise(done => {
  const face = document.querySelector('.crt__go-face');
  const lamp = document.querySelector('.lamp--projects');
  const hand = document.querySelector('.invite__hand');
  const out = [];
  const t0 = performance.now();
  function tick(now) {
    const tr = getComputedStyle(face).translate.split(' ');
    const m = new DOMMatrixReadOnly(getComputedStyle(hand).transform);
    out.push([Math.round(now - t0), parseFloat(tr[1] || tr[0]) || 0,
              parseFloat(getComputedStyle(lamp).getPropertyValue('--lit')) || 0,
              Math.round(m.f)]);
    if (now - t0 < ms) requestAnimationFrame(tick); else done(out);
  }
  requestAnimationFrame(tick);
})"""


def luminance(rgb):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def parse_rgb(s):
    """rgb()/rgba() with 0-255 channels, or color(srgb r g b) with 0-1 channels."""
    body = s[s.index("(") + 1:s.rindex(")")].replace(",", " ").replace("/", " ").split()
    if s.startswith("color("):
        body = body[1:]                          # the colour space name
        return tuple(float(v) * 255 for v in body[:3])
    return tuple(float(v) for v in body[:3])


class Report:
    def __init__(self):
        self.notes = []
        self.fails = 0

    def note(self, name, detail, ok):
        self.notes.append({"check": name, "ok": bool(ok), "detail": detail})
        print(("  ok   " if ok else "  FAIL ") + name + " -- " + json.dumps(detail, default=str)[:220])
        if not ok:
            self.fails += 1


def open_room(ctx, rep):
    page = ctx.new_page()
    page.add_init_script("sessionStorage.setItem('atalay.intro','1')")
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_function("document.querySelector('[data-room]').dataset.state === 'room-ready'")
    page.wait_for_function("document.querySelector('[data-room]').dataset.invite === 'on'")
    page.wait_for_timeout(120)
    return page


def rising_edges(samples, index, threshold):
    """Times at which a sampled value crosses up through the threshold.

    A run that is already high at the first sample is not an edge - the
    sampling can start anywhere in the cycle - so it is skipped.
    """
    edges = []
    below = samples[0][index] <= threshold if samples else True
    for t, *vals in samples:
        v = vals[index - 1]
        if below and v > threshold:
            edges.append(t)
            below = False
        elif v <= threshold:
            below = True
    return edges


def episode(samples, start, index, threshold):
    """The first contiguous run above the threshold at or after `start`: (t0, t1)."""
    t0 = None
    for t, *vals in samples:
        v = vals[index - 1]
        if t < start:
            continue
        if v > threshold:
            if t0 is None:
                t0 = t
            t1 = t
        elif t0 is not None:
            return t0, t1
    return (t0, t1) if t0 is not None else None


def check_sync(ctx, rep, out):
    page = open_room(ctx, rep)
    clock = page.evaluate("""() => {
      const a = document.querySelector('.invite__hand').getAnimations()[0];
      const ls = [...document.querySelectorAll('.lamp')].map(l => l.getAnimations()[0]);
      return {hand: a ? [a.startTime, a.effect.getTiming().duration] : null,
              lamps: ls.map(l => l ? [l.startTime, l.effect.getTiming().duration] : null)};
    }""")
    same = clock["hand"] and all(l and abs(l[0] - clock["hand"][0]) <= 20 and l[1] == clock["hand"][1]
                                 for l in clock["lamps"])
    rep.note("the four lamps run on the hand's own animation clock",
             {"hand": clock["hand"], "lamps": clock["lamps"]}, same and len(clock["lamps"]) == 4)

    samples = page.evaluate(SAMPLE, 6400)
    presses = rising_edges(samples, 1, 0.3)
    lights = rising_edges(samples, 2, 0.05)
    pairs = []
    for tp in presses:
        near = min(lights, key=lambda tl: abs(tl - tp)) if lights else None
        pairs.append([tp, near, None if near is None else near - tp])
    frame = max(17, max((b[0] - a[0]) for a, b in zip(samples, samples[1:])) if len(samples) > 1 else 17)
    rep.note("in real time the lamps begin to light on the frame the key goes down, three cycles",
             {"press->light ms": pairs, "frame ms": frame},
             len(pairs) >= 3 and all(p[2] is not None and abs(p[2]) <= frame + 1 for p in pairs[:3]))
    gaps = [b - a for a, b in zip(presses, presses[1:])]
    rep.note("and the cycles keep the demonstration's cadence (2000ms)", gaps,
             len(gaps) >= 2 and all(abs(g - 2000) <= 60 for g in gaps))
    holds = []
    fades = []
    for tl in lights[:3]:
        run = episode(samples, tl, 2, 0.95)
        if run:
            holds.append(run[1] - run[0])
        end = [t for t, _, l, _ in samples if t > tl + 60 and l < 0.05]
        if end:
            fades.append(end[0] - tl)
    rep.note("lit for about 200ms, dark again about 440ms after the press (40 up, 200 hold, 200 down)",
             {"hold ms": holds, "press->dark ms": fades},
             len(holds) >= 3 and all(140 <= h <= 260 for h in holds[:3])
             and len(fades) >= 3 and all(380 <= f <= 520 for f in fades[:3]))
    (out / "samples.json").write_text(json.dumps(samples), encoding="utf-8")

    # hover and focus keep a lamp lit even in the cycle's dark phase
    page.evaluate(PARK, 100)
    page.hover(".lamp--github")
    page.wait_for_timeout(60)
    lit = page.evaluate(LIT, ".lamp--github")
    rep.note("hovering a lamp keeps it fully lit while the cycle is dark", lit, lit >= 0.99)
    page.mouse.move(5, 5)
    page.evaluate("() => document.querySelector('[data-go]').focus()")
    page.keyboard.press("Tab")
    focused = page.evaluate("() => document.activeElement.className")
    lit = page.evaluate(LIT, ".lamp--github")
    ring = page.evaluate("""() => { const s = getComputedStyle(document.activeElement);
        return s.outlineWidth + ' ' + s.outlineColor; }""")
    rep.note("Tab from the key reaches the first lamp, lit, with a visible ring",
             {"focused": focused, "lit": lit, "ring": ring},
             "lamp--github" in focused and lit >= 0.99 and ring.split()[0] != "0px")
    page.evaluate("() => document.activeElement.blur()")

    # the resting state is readable: contrast of the label text on the wall
    page.evaluate(PARK, 100)
    page.wait_for_timeout(60)
    cols = page.evaluate("""() => {
      const cs = getComputedStyle(document.querySelector('.lamp--social'));
      const bg = getComputedStyle(document.querySelector('.room__wall')).backgroundColor;
      return {text: cs.color, wall: bg, lit: cs.getPropertyValue('--lit')};
    }""")
    ratio = contrast(parse_rgb(cols["text"]), parse_rgb(cols["wall"]))
    rep.note("at rest the label text reads on the wall (>= 4.5:1)",
             {**cols, "ratio": round(ratio, 2)}, ratio >= 4.5)
    page.close()


def check_activation(ctx, rep, out):
    page = open_room(ctx, rep)
    page.evaluate(PARK, 100)
    page.evaluate("""() => document.querySelectorAll('.invite, .invite *, .crt__fx, .crt__fx *, .crt__go, .crt__go-face, .lamp')
        .forEach(el => el.getAnimations({subtree: true}).forEach(a => a.play()))""")
    page.click("[data-go]")
    peak = page.evaluate("""() => new Promise(done => {
      const lamp = document.querySelector('.lamp--about');
      const t0 = performance.now(); let best = 0, at = null;
      function tick(now) {
        const v = parseFloat(getComputedStyle(lamp).getPropertyValue('--lit')) || 0;
        if (v > best) { best = v; at = Math.round(now - t0); }
        if (now - t0 < 260) requestAnimationFrame(tick); else done({best, at});
      }
      requestAnimationFrame(tick);
    })""")
    rep.note("a real activation lights the lamps at once", peak, peak["best"] >= 0.95 and peak["at"] <= 120)
    page.wait_for_function("document.querySelector('[data-room]').dataset.state === 'desktop'", timeout=15000)
    page.wait_for_timeout(200)
    state = page.evaluate("""() => ({
      inert: document.querySelector('[data-lamps]').inert,
      hidden: getComputedStyle(document.querySelector('[data-room]')).visibility,
    })""")
    stray = []
    for _ in range(10):
        page.keyboard.press("Tab")
        hit = page.evaluate("() => (document.activeElement.closest && document.activeElement.closest('.lamp')) ? document.activeElement.className : null")
        if hit:
            stray.append(hit)
    rep.note("on the desktop the lamps are inert and never take focus",
             {**state, "focused lamps over 10 tabs": stray},
             state["inert"] is True and state["hidden"] == "hidden" and not stray)
    page.keyboard.press("Escape")
    page.wait_for_function("document.querySelector('[data-room]').dataset.state === 'room-ready'")
    back = page.evaluate("() => document.querySelector('[data-lamps]').inert")
    rep.note("back in the room they are usable again", {"inert": back}, back is False)
    page.close()


def check_reduced(browser, rep, out):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce",
                              color_scheme="dark", device_scale_factor=1)
    page = ctx.new_page()
    page.add_init_script("sessionStorage.setItem('atalay.intro','1')")
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_function("document.querySelector('[data-room]').dataset.state === 'room-ready'")
    page.wait_for_timeout(300)
    d = page.evaluate("""() => ({
      running: [...document.querySelectorAll('.lamp')].flatMap(l => l.getAnimations()).length,
      boxes: [...document.querySelectorAll('.lamp')].map(l => { const r = l.getBoundingClientRect();
        return [l.dataset.lamp, Math.round(r.width), Math.round(r.height), getComputedStyle(l).visibility]; }),
    })""")
    rep.note("reduced motion: a steady arrangement, no illumination loop, links present",
             d, d["running"] == 0 and len(d["boxes"]) == 4 and all(b[1] >= 44 and b[2] >= 44 and b[3] == "visible" for b in d["boxes"]))
    page.screenshot(path=str(out / "reduced-motion-dark.png"))
    ctx.close()


def capture(browser, rep, out, evidence):
    """The requested stills: rest / peak / faded, both themes, desktop and phone."""
    layouts = []
    for device, (w, h) in (("desktop", (1440, 900)), ("phone", (390, 844))):
        for theme in ("dark", "light"):
            ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=theme,
                                      device_scale_factor=1, has_touch=device == "phone", is_mobile=device == "phone")
            page = open_room(ctx, rep)
            for name, ms in (("rest", 100), ("peak", 700), ("faded", 1200)):
                page.evaluate(PARK, ms)
                page.wait_for_timeout(80)
                page.screenshot(path=str(evidence / f"{device}-{theme}-{name}.png"))
            boxes = page.evaluate("""() => [...document.querySelectorAll('.lamp')].map(l => {
                const r = l.getBoundingClientRect();
                return {id: l.dataset.lamp, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)}; })""")
            art = page.evaluate("""() => { const r = document.querySelector('.crt__art:not([style*="none"])') ?
                [...document.querySelectorAll('.crt__art')].find(e => e.getBoundingClientRect().width > 0).getBoundingClientRect() : null;
                return r ? {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)} : null; }""")
            inside = all(0 <= b["x"] and b["x"] + b["w"] <= w and 0 <= b["y"] for b in boxes)
            big = all(b["w"] >= 44 and b["h"] >= 44 for b in boxes)
            overlap = []
            for i, a in enumerate(boxes):
                for b in boxes[i + 1:]:
                    if a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"] and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]:
                        overlap.append((a["id"], b["id"]))
            rep.note(f"{device} {theme}: four lamps inside the window, at least 44px, not overlapping each other",
                     {"boxes": boxes, "art": art, "overlap": overlap}, inside and big and not overlap and len(boxes) == 4)
            layouts.append({"device": device, "theme": theme, "boxes": boxes, "art": art})
            if device == "desktop" and theme == "dark":
                # three peaks from LIVE cycles, not parked frames
                page.evaluate("""() => document.querySelectorAll('.invite, .invite *, .crt__fx, .crt__fx *, .crt__go, .crt__go-face, .lamp')
                    .forEach(el => el.getAnimations({subtree: true}).forEach(a => a.play()))""")
                for k in range(3):
                    page.wait_for_function(LIT.replace("sel =>", "() =>").replace("document.querySelector(sel)", "document.querySelector('.lamp--projects')") + " > 0.9")
                    page.screenshot(path=str(evidence / f"live-cycle-{k + 1}.png"))
                    page.wait_for_function(LIT.replace("sel =>", "() =>").replace("document.querySelector(sel)", "document.querySelector('.lamp--projects')") + " < 0.05")
                page.evaluate(PARK, 700)
                page.wait_for_timeout(80)
                for lamp in ("github", "about", "projects", "social"):
                    page.locator(f".lamp--{lamp}").screenshot(path=str(evidence / f"lamp-{lamp}-peak.png"))
                page.evaluate(PARK, 100)
                page.wait_for_timeout(80)
                page.locator(".lamp--projects").screenshot(path=str(evidence / "lamp-projects-rest.png"))
            ctx.close()
    (out / "layouts.json").write_text(json.dumps(layouts, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="artifacts/lamps")
    ap.add_argument("--evidence", default="docs/evidence/lamps/after")
    args = ap.parse_args()
    out, evidence = Path(args.out), Path(args.evidence)
    out.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    rep = Report()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="dark", device_scale_factor=1)
        print("synchronization")
        check_sync(ctx, rep, out)
        print("activation, desktop, return")
        check_activation(ctx, rep, out)
        ctx.close()
        print("reduced motion")
        check_reduced(browser, rep, out)
        print("captures")
        capture(browser, rep, out, evidence)
        browser.close()
    (out / "report.json").write_text(json.dumps(rep.notes, indent=2), encoding="utf-8")
    print(f"\n{len(rep.notes)} checks, {rep.fails} failures")
    sys.exit(1 if rep.fails else 0)


if __name__ == "__main__":
    main()
