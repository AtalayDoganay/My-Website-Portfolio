"""Drive the opening scene in a real browser and report what actually happened.

Walks the whole journey: the boot wait, the two printed lines, the carriage
return that keeps the first one, the zoom out into the physical monitor, the
invitation cycle, entering the desktop, and coming back. Then Skip from each
phase, touch, keyboard, reduced motion, a theme change mid-introduction, a
resize mid-transition, and a second visit.

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

SCREEN = "[data-screen]"
GO = "[data-go]"
# The contact point is exported by the sprite into data-tip-x/y in the markup.
LINE_ONE = "Welcome to my website..."
LINE_TWO = "Hi, my name is Atalay Doganay..."


def state(page):
    return page.eval_on_selector("[data-room]", "el => el.dataset.state")


def finished(page):
    """The finished room: the introduction has cleared and the button is up."""
    return page.evaluate("""() => {
      const go = document.querySelector('[data-go]');
      return {state: document.querySelector('[data-room]').dataset.state,
              lines: [...document.querySelectorAll('.crt__text')].map(e => e.textContent),
              button: !go.hidden, label: go.textContent.trim(),
              invite: document.querySelector('[data-room]').dataset.invite};
    }""")


def is_finished(got):
    return (got["state"] == "room-ready" and got["lines"] == ["", ""]
            and got["button"] and got["label"] in ("CLICK!", "TAP!"))


def glass_lines(page):
    """What the real monitor is showing - not the fullscreen boot copy."""
    return page.eval_on_selector_all(".crt__text", "els => els.map(e => e.textContent)")


def camera(page):
    """The camera pose, and whether the whole scene is moving with it."""
    return page.evaluate("""() => {
      const w = document.querySelector('[data-world]');
      const m = new DOMMatrixReadOnly(getComputedStyle(w).transform);
      const r = el => { const b = el.getBoundingClientRect();
        return [Math.round(b.width), Math.round(b.height)]; };
      // The desk's height. The narrow framing continues its tabletop past the
      // artwork with a CSS band; the wide framing draws a finite desk INSIDE
      // the artwork and its band is empty, so the drawn image stands in.
      const band = r(document.querySelector('.room__desk'))[1];
      const art = [...document.querySelectorAll('.crt__art')]
        .find(e => e.getBoundingClientRect().height > 0);
      return {k: Math.round(m.a * 1000) / 1000,
              crt: r(document.querySelector('[data-crt]')),
              glass: r(document.querySelector('[data-screen]')),
              desk: band || (art ? r(art)[1] : 0)};
    }""")


def cycle_info(page):
    """The demonstration's clock, read from its own keyframes: the cycle's
    duration, the contact beat and the release beat, in milliseconds. The
    parked frames below are taken relative to these, so retiming the CSS
    retimes the check with it."""
    return page.evaluate("""() => {
      const a = document.querySelector('.invite__hand').getAnimations()
        .find(x => x.animationName === 'invite-hand');
      const d = a.effect.getTiming().duration, k = a.effect.getKeyframes();
      return {duration: d, contact: k[2].computedOffset * d, release: k[4].computedOffset * d};
    }""")


def screen_box(page):
    return page.eval_on_selector(
        SCREEN, "el => { const r = el.getBoundingClientRect();"
        " return {x: r.x, y: r.y, w: r.width, h: r.height}; }"
    )


def wait_state(page, want, timeout=20000):
    page.wait_for_function(
        "want => document.querySelector('[data-room]').dataset.state === want",
        arg=want, timeout=timeout,
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


def open_page(ctx, rep, path="/", record=False, fresh=True):
    page = ctx.new_page()
    page.on(
        "console",
        lambda m: rep.console.append("{}: {}".format(m.type, m.text))
        if m.type in ("error", "warning")
        else None,
    )
    page.on("pageerror", lambda e: rep.console.append("pageerror: {}".format(e)))
    if fresh:
        # A second visit in the same session is meant to skip the introduction,
        # so anything that wants to watch it has to arrive as a first visit.
        page.add_init_script("try { sessionStorage.removeItem('atalay.intro'); } catch (e) {}")
    if record:
        page.add_init_script(RECORDER)
    page.goto(BASE + path, wait_until="networkidle")
    return page


# Installed before any page script runs, so every frame of the introduction is
# recorded with a timestamp. Sampling from the test process would measure the
# test's own latency instead of the animation's.
RECORDER = """
window.__frames = [];
document.addEventListener('DOMContentLoaded', () => {
  const rows = document.querySelectorAll('.crt__text');
  const wait = document.querySelector('[data-line="1"]');
  if (!rows.length) return;
  const push = () => window.__frames.push([
    performance.now(),
    wait ? wait.textContent : '',
    rows[0].textContent,
    rows[1].textContent,
  ]);
  rows.forEach((el) =>
    new MutationObserver(push).observe(el, { childList: true, characterData: true, subtree: true }));
  if (wait) new MutationObserver(push).observe(wait, { childList: true, characterData: true, subtree: true });
  push();
});
"""


# The burst lives OUTSIDE the glass now, in .crt__fx, so parking the cycle has
# to reach it there as well as the hand and the button inside.
PARK = """ms => document.querySelectorAll(
      '.invite, .invite *, .crt__fx, .crt__fx *, .crt__go, .crt__go-face')
    .forEach(el => el.getAnimations({subtree: true})
    .forEach(a => { a.pause(); a.currentTime = ms; }))"""

RESUME = """() => document.querySelectorAll(
      '.invite, .invite *, .crt__fx, .crt__fx *, .crt__go, .crt__go-face')
    .forEach(el => el.getAnimations({subtree: true}).forEach(a => a.play()))"""


def median(xs):
    s = sorted(xs)
    return s[len(s) // 2] if s else 0


# ---------------------------------------------------------------- A, B and C


def check_opening(ctx, rep, out):
    """The boot wait, both printed lines, and the pull back into the monitor."""
    page = open_page(ctx, rep, record=True)

    page.wait_for_timeout(600)
    page.screenshot(path=str(out / "01-boot.png"))
    cam = camera(page)
    rep.note("A: the page opens INSIDE the display - the camera is pushed in on the glass",
             {"state": state(page), **cam},
             state(page) in ("boot", "typing") and cam["k"] > 2
             and cam["glass"][0] >= DESKTOP["width"])

    # The three dots are only on screen for 400ms each, so they are checked
    # against the recorded frames rather than by polling for a transient state.
    page.screenshot(path=str(out / "02-dots.png"))

    # The tube holds EMPTY first, then the dots arrive evenly. The frames are
    # recorded by a MutationObserver installed before the script runs, so these
    # are the moments the glass actually changed, not a poll that might miss one.
    wait_state(page, "typing")
    frames = page.evaluate("() => window.__frames || []")
    t0 = frames[0][0] if frames else 0
    marks = {}
    for t, _wait, one, _two in frames:
        if one in (".", "..", "...") and one not in marks:
            marks[one] = round(t - t0)
    cleared = next((round(t - t0) for t, _w, one, _x in frames
                    if one == "" and "..." in marks and round(t - t0) > marks["..."]), None)
    want = {".": 650, "..": 1050, "...": 1450}
    # A chained setTimeout cannot run early, and a busy main thread makes it
    # late, so the tolerance is one-sided and generous on the late side only.
    on_time = all(k in marks and -20 <= marks[k] - v <= 260 for k, v in want.items())
    rep.note("A: the tube holds empty, then three dots at 650 / 1050 / 1450ms",
             {"observed": marks, "dots cleared at": cleared, "wanted": want},
             on_time and cleared is not None)

    wait_state(page, "typing")
    page.wait_for_function(
        "one => document.querySelectorAll('.crt__text')[0].textContent === one",
        arg=LINE_ONE, timeout=20000,
    )
    page.screenshot(path=str(out / "03-line-one.png"))

    # The carriage return: the second line starts while the first one stands.
    page.wait_for_function(
        "() => document.querySelectorAll('.crt__text')[1].textContent.length > 3",
        timeout=20000,
    )
    kept = glass_lines(page)
    page.screenshot(path=str(out / "04-second-line.png"))
    rep.note("B: the cursor moves to a new line and the first line is KEPT",
             kept, kept[0] == LINE_ONE and 3 < len(kept[1]) < len(LINE_TWO))
    caret = page.eval_on_selector_all(
        ".crt__caret.is-on", "els => els.map(e => e.getAttribute('data-caret'))")
    caret = [c for c in caret if c]
    rep.note("B: the caret is on the second row while it types", caret, caret == ["2"])

    page.wait_for_function(
        "two => document.querySelectorAll('.crt__text')[1].textContent === two",
        arg=LINE_TWO, timeout=20000,
    )
    page.screenshot(path=str(out / "05-both-lines.png"))
    rep.note("B: both lines are printed, neither erased", glass_lines(page),
             glass_lines(page) == [LINE_ONE, LINE_TWO])

    # C: the display shrinks into the real bezel.
    # C: ONE camera through the whole scene. Seek the move to fixed points
    # rather than racing it, and check the equipment and the desk change size
    # TOGETHER - a separate shrinking panel would not.
    wait_state(page, "revealing-room")
    page.evaluate("""() => { const a = document.querySelector('[data-world]').getAnimations()[0];
        if (a) { a.pause(); window.__cam = a; } }""")
    poses = []
    for pct in (0, 25, 50, 75, 100):
        page.evaluate("p => { if (window.__cam) window.__cam.currentTime ="
                      " window.__cam.effect.getTiming().duration * p / 100; }", pct)
        page.wait_for_timeout(70)
        c = camera(page)
        c["pct"] = pct
        poses.append(c)
        page.screenshot(path=str(out / f"06-pullback-{pct:03d}.png"))
    ratios = []
    for c in poses:
        ratios.append(round(c["crt"][0] / poses[-1]["crt"][0], 2))
        for part in ("crt", "glass"):
            got = c[part][0] / poses[-1][part][0]
            if abs(got - c["k"]) > 0.02:
                rep.note("C: " + part + " tracks the camera", f"{got} vs k={c['k']}", False)
    same = all(
        abs(c["crt"][0] / poses[-1]["crt"][0] - c["desk"] / poses[-1]["desk"]) < 0.03
        for c in poses)
    rep.note("C: equipment and desk change size TOGETHER through the pullback",
             {"scales": [c["k"] for c in poses],
              "crt x": ratios,
              "desk x": [round(c["desk"] / poses[-1]["desk"], 2) for c in poses]},
             same)
    rep.note("C: the midpoint shows enlarged equipment, not a settled room",
             f"scale {poses[2]['k']} at 50%", poses[2]["k"] >= 1.8)
    dur = page.evaluate("() => window.__cam ? window.__cam.effect.getTiming().duration : 0")
    rep.note("C: the pullback lasts 1.3-1.7s", f"{dur}ms", 1300 <= dur <= 1700)
    page.evaluate("() => { if (window.__cam) window.__cam.finish(); }")

    wait_state(page, "room-ready")
    page.wait_for_timeout(200)
    page.screenshot(path=str(out / "07-room-ready.png"))
    rep.note("C: it lands and the room is revealed around it",
             {"state": state(page),
              "skip hidden": page.eval_on_selector("[data-skip]", "el => el.hidden"),
              "sound offered": page.eval_on_selector("[data-sound]", "el => !el.hidden")},
             state(page) == "room-ready"
             and page.eval_on_selector("[data-skip]", "el => el.hidden")
             and page.eval_on_selector("[data-sound]", "el => !el.hidden"))
    got = page.evaluate("""() => {
      const go = document.querySelector('[data-go]');
      const r = go.getBoundingClientRect();
      const g = document.querySelector('[data-screen]').getBoundingClientRect();
      return {lines: [...document.querySelectorAll('.crt__text')].map(e => e.textContent),
              label: go.textContent.trim(), hidden: go.hidden,
              centredX: Math.abs((r.x + r.width / 2) - (g.x + g.width / 2)) < 2,
              downPct: Math.round((r.y + r.height / 2 - g.y) / g.height * 100),
              tag: go.tagName, nested: !!go.closest('button:not([data-go])')};
    }""")
    rep.note("C: the introduction clears and a real button takes the glass", got,
             got["lines"] == ["", ""] and got["tag"] == "BUTTON" and not got["nested"]
             and not got["hidden"] and got["centredX"] and 62 <= got["downPct"] <= 68)

    frames = page.evaluate("() => window.__frames")
    rep.note("the whole introduction is one run of frames, in order",
             f"{len(frames)} frames recorded", len(frames) > 50)

    # A: three dots, the existing hold, then individual 120ms backspaces.
    dots = [(t, a) for t, w, a, b in frames if a in ('.', '..', '...')]
    seen = []
    for t, a in dots:
        if not seen or seen[-1][1] != a:
            seen.append((t, a))
    gaps = [round(seen[i + 1][0] - seen[i][0]) for i in range(len(seen) - 1)]
    cleared = next((t for t, w, a, b in frames if a == '' and t > seen[-1][0]), None)
    if cleared:
        gaps.append(round(cleared - seen[-1][0]))
    rep.note("A: three dots, a 400ms hold, then three individual backspaces",
             {"sequence": [a for _, a in seen], "gaps": gaps},
             [a for _, a in seen] == ['.', '..', '...', '..', '.']
             and len(gaps) == 5 and all(330 <= g <= 480 for g in gaps[:3])
             and all(105 <= g <= 185 for g in gaps[3:]))
    wanted_clear = 650 + 2 * 400 + 400 + 2 * 120
    rep.note("A: deletion extends the intro budget by 240ms",
             {"expected clear": wanted_clear, "observed clear": round(cleared - t0)},
             cleared is not None and wanted_clear - 20 <= cleared - t0 <= wanted_clear + 300)

    # Per-character cadence of the first line, measured between frames.
    typed = [t for t, w, a, b in frames if a and a != LINE_ONE and len(a) > 1]
    gaps = [round(typed[i + 1] - typed[i]) for i in range(len(typed) - 1)]
    gaps = [g for g in gaps if 0 < g < 200]  # paint() writes both rows per step
    rep.note("B: characters arrive at a steady cadence",
             f"median {median(gaps)}ms over {len(gaps)} gaps", 20 <= median(gaps) <= 90)

    first = frames[0][0]
    done = next((t for t, w, a, b in frames if b == LINE_TWO), None)
    printing_budget = (650 + 2 * 400 + 400 + 2 * 120
                       + (len(LINE_ONE) + len(LINE_TWO)) * 42 + 240 + 290)
    rep.note("the introduction finishes inside its budget",
             {"printing ms": round(done - first), "nominal printing ms": printing_budget,
              "nominal full intro ms": printing_budget + 480 + 1500},
             done is not None and printing_budget - 20 <= done - first <= printing_budget + 1200)

    page.close()


def check_reveal_geometry(browser, rep, out):
    """The display has to land ON the glass, at every size, in both framings."""
    for label, vp in (("desktop", DESKTOP), ("phone", PHONE)):
        ctx2 = browser.new_context(viewport=vp, device_scale_factor=1)
        page = open_page(ctx2, rep)
        wait_state(page, "room-ready", timeout=25000)
        page.wait_for_timeout(150)
        got = page.evaluate("""() => {
          const img = [...document.querySelectorAll('.crt__art')]
            .find(e => e.getBoundingClientRect().width > 0);
          const btn = document.querySelector('[data-screen]');
          const ir = img.getBoundingClientRect(), sr = btn.getBoundingClientRect();
          const k = img.naturalWidth / ir.width;
          return {
            file: img.currentSrc.split('/').pop(),
            rect: [Math.round((sr.x - ir.x) * k), Math.round((sr.y - ir.y) * k),
                   Math.round(sr.width * k), Math.round(sr.height * k)],
            readable: Math.round(sr.width) + 'x' + Math.round(sr.height),
            overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          };
        }""")
        page.screenshot(path=str(out / f"08-landed-{label}.png"))
        rep.note(f"{label}: the introduction is readable on the glass after shrinking",
                 got, got["overflow"] == 0 and got["rect"][2] >= 60)
        page.close()
        ctx2.close()


# ------------------------------------------------------------------------ D


def check_invitation(ctx, rep, out):
    """The hand, the label, the burst, and what they must not do."""
    page = open_page(ctx, rep)
    wait_state(page, "room-ready", timeout=25000)
    page.wait_for_timeout(300)

    rep.note("D: the invitation starts once the room has settled",
             page.eval_on_selector("[data-room]", "el => el.dataset.invite"),
             page.eval_on_selector("[data-room]", "el => el.dataset.invite") == "on")

    say = page.eval_on_selector("[data-go-label]", "el => el.textContent")
    rep.note("D: a pointer layout is invited to CLICK", say, say == "CLICK!")

    running = page.evaluate(
        "() => document.querySelector('.invite').getAnimations({subtree: true}).length")
    rep.note("D: CSS owns the visual cycle", f"{running} animations", running > 0)

    # Park the cycle inside the press - 60ms after contact, with the key down -
    # and measure the fingertip against the button's own rect rather than
    # against an unrelated offset.
    beat = cycle_info(page)
    page.evaluate(PARK, beat["contact"] + 60)
    page.wait_for_timeout(90)
    touch = page.evaluate("""() => {
      const hand = document.querySelector('.invite__hand');
      const h = hand.getBoundingClientRect();
      const faceEl = document.querySelector('.crt__go-face');
      const f = faceEl.getBoundingClientRect();
      const tip = {x: h.left + h.width * Number(hand.dataset.tipX),
                   y: h.top + h.height * Number(hand.dataset.tipY)};
      return {tip: [Math.round(tip.x), Math.round(tip.y)],
              face: [Math.round(f.left), Math.round(f.top),
                     Math.round(f.right), Math.round(f.bottom)],
              onButton: Math.abs(tip.x - (f.left + f.right) / 2) < 0.1
                     && Math.abs(tip.y - f.top) < 0.1,
              pressed: getComputedStyle(faceEl).translate};
    }""")
    rep.note("D: the fingertip meets the button on the press", touch, touch["onButton"])
    rep.note("D: and the button is down at that moment", touch["pressed"],
             touch["pressed"] not in ("none", "0px"))

    # A press is ONE axis. Sampled right across the cycle rather than at the two
    # ends, because a sideways drift that returns to centre would pass a
    # two-point check while still reading as a diagonal swipe on screen.
    travel = []
    for ms in range(0, int(beat["duration"]) + 1, 100):
        page.evaluate(PARK, ms)
        page.wait_for_timeout(16)
        travel.append(page.evaluate("""() => {
          const hand = document.querySelector('.invite__hand');
          const h = hand.getBoundingClientRect();
          const f = document.querySelector('.crt__go-face').getBoundingClientRect();
          const s = getComputedStyle(document.querySelector('.invite__hand'));
          return {dx: h.left + h.width * Number(hand.dataset.tipX) - (f.left + f.right) / 2,
                  y: h.top, tf: s.transform, rot: s.rotate};
        }"""))
    drift = max(t["dx"] for t in travel) - min(t["dx"] for t in travel)
    rise = max(t["y"] for t in travel) - min(t["y"] for t in travel)
    skewed = [t["tf"] for t in travel
              if t["tf"] != "none" and not t["tf"].startswith("matrix(1, 0, 0, 1,")]
    spun = [t["rot"] for t in travel if t["rot"] not in ("none", "0deg", "")]
    rep.note("D: the hand travels STRAIGHT DOWN - no sideways drift, no rotation",
             {"horizontal drift": round(drift, 3), "vertical travel": round(rise, 1),
              "offset from the button's centre": round(travel[0]["dx"], 3),
              "skewed frames": len(skewed), "rotated frames": len(spun)},
             drift < 0.5 and rise > 8 and abs(travel[0]["dx"]) < 0.5
             and not skewed and not spun)
    page.evaluate(PARK, beat["contact"] + 620)       # mid-flight
    page.wait_for_timeout(90)
    page.screenshot(path=str(out / "09-invite-burst.png"))
    # The marks are meant to LEAVE. Mid-flight most of them should be outside
    # the glass entirely, and the layer that carries them must not be clipped
    # by it - which is the whole reason they live outside .crt__glass.
    lit = page.evaluate("""() => {
      const g = document.querySelector('[data-screen]').getBoundingClientRect();
      const vis = [...document.querySelectorAll('.burst__bit')]
        .filter(e => parseFloat(getComputedStyle(e).opacity) > 0.5);
      const outside = vis.filter(e => { const r = e.getBoundingClientRect();
        return r.left < g.left || r.right > g.right
            || r.top < g.top || r.bottom > g.bottom; }).length;
      const colours = [...new Set(vis.map(e => getComputedStyle(e).color))];
      // Nothing BETWEEN a mark and the room may clip it. The room itself does
      // clip, to the viewport, and always has - that is not what this is about.
      let clipper = null;
      for (let el = document.querySelector('.burst__bit');
           el && !el.classList.contains('room'); el = el.parentElement) {
        if (getComputedStyle(el).overflow !== 'visible') {
          clipper = el.className || el.tagName;
          break;
        }
      }
      return {pieces: vis.length, total: document.querySelectorAll('.burst__bit').length,
              outside: outside, colours: colours.length, clipper: clipper,
              marks: vis.filter(e => e.classList.contains('burst__mark')).length,
              stars: vis.filter(e => e.classList.contains('burst__star')).length};
    }""")
    rep.note("D: the burst is colourful, bounded, and ESCAPES the glass", lit,
             lit["pieces"] >= 8 and lit["total"] == 10 and lit["outside"] >= 6
             and lit["colours"] >= 4 and lit["marks"] >= 4 and lit["stars"] >= 3
             and lit["clipper"] is None)

    # Nothing decorative may be over the glass, and none of it may take a click.
    # The hand and its label belong ON the glass now - anchored just inside its
    # upper-left corner - so what matters is that they clear the printed lines,
    # and that the burst travels OUTSIDE the bezel rather than over the text.
    page.evaluate(PARK, beat["contact"] + 40)        # the launch beat
    page.wait_for_timeout(90)
    clear = page.evaluate("""() => {
      const faceEl = document.querySelector('.crt__go-face');
      const f = faceEl.getBoundingClientRect();
      const origin = {x: f.left + f.width / 2, y: f.top};
      // At the launch beat every piece should still be near the press point:
      // the burst has to START at the button, wherever it ends up.
      const far = [...document.querySelectorAll('.burst__bit')].filter(e => {
        const r = e.getBoundingClientRect();
        return Math.hypot(r.left + r.width / 2 - origin.x,
                          r.top + r.height / 2 - origin.y) > f.width * 1.8; }).length;
      const mid = document.elementFromPoint(f.left + f.width / 2, f.top + f.height / 2);
      const h = document.querySelector('.invite__hand').getBoundingClientRect();
      const overHand = document.elementFromPoint(h.left + h.width / 2, h.top + h.height / 2);
      return {strayPieces: far,
              buttonTakesClick: !!(mid && mid.closest('[data-go]')),
              throughHand: overHand ? overHand.tagName + '.' + (overHand.className || '') : 'none'};
    }""")
    rep.note("D: every piece launches from the button's press point",
             clear["strayPieces"], clear["strayPieces"] == 0)
    rep.note("D: the button itself takes the click", clear["buttonTakesClick"],
             clear["buttonTakesClick"] is True)
    rep.note("D: the hand and particles take no pointer events",
             clear["throughHand"], "invite" not in clear["throughHand"]
             and "burst" not in clear["throughHand"])
    # Resume EVERYTHING that PARK paused, the burst included. Leaving the burst
    # parked at 700ms - an invisible frame, held by the 31% step until 37% -
    # made the next check depend on the click landing more than 40ms after
    # the hand resumed: the page rewinds a held press to its current phase
    # without unpausing it, so a fast click found no piece showing.
    page.evaluate(RESUME)

    # Entering must stop it, and nothing may be left running.
    before = page.evaluate("() => document.getAnimations().length")
    page.click(GO)
    page.wait_for_timeout(160)
    linger = page.evaluate("""() => ({
      state: document.querySelector('[data-room]').dataset.state,
      invite: document.querySelector('[data-room]').dataset.invite,
      showing: [...document.querySelectorAll('.burst__bit')]
        .filter(e => parseFloat(getComputedStyle(e).opacity) > 0.4).length,
    })""")
    rep.note("E: the burst is still on screen as entry begins", linger,
             linger["state"] == "entering-desktop" and linger["showing"] > 0)
    wait_state(page, "desktop")
    page.wait_for_timeout(200)
    after = page.evaluate("""() => ({
      invite: document.querySelector('[data-room]').dataset.invite,
      running: document.querySelector('.invite').getAnimations({subtree: true})
        .filter(a => a.playState === 'running').length,
      total: document.getAnimations().length,
    })""")
    rep.note("D: entering stops the invitation and leaves nothing running",
             {"before": before, **after},
             after["invite"] == "off" and after["running"] == 0)
    page.close()


def check_sound_offer(ctx, rep, out):
    """The opening must be silent by default, and say how to hear it.

    Not a test that sound WORKS - that needs the output measured, which
    tools/check_audio.py does. This is the part that can be settled from the
    page alone: that nothing tries to make a noise without a gesture, and that
    the way to ask for one is present and labelled.
    """
    page = ctx.new_page()
    page.add_init_script("""
      window.__audioContexts = 0;
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) {
        const Wrapped = function (...a) { window.__audioContexts += 1; return new AC(...a); };
        Wrapped.prototype = AC.prototype;
        window.AudioContext = Wrapped;
        window.webkitAudioContext = Wrapped;
      }
    """)
    page.goto(BASE + "/", wait_until="networkidle")
    page.wait_for_timeout(2600)
    made = page.evaluate("() => window.__audioContexts")
    rep.note("the opening plays SILENTLY until asked - no audio context is built",
             f"{made} contexts created without a gesture", made == 0)

    label = page.eval_on_selector("[data-sound]", "el => el.textContent.trim()")
    pressed = page.eval_on_selector("[data-sound]", "el => el.getAttribute('aria-pressed')")
    rep.note("and the control that offers it says what it will do",
             {"label": label, "aria-pressed": pressed},
             label == "Play intro with sound" and pressed == "false")

    wait_state(page, "room-ready", timeout=25000)
    page.click("[data-sound]")
    page.wait_for_timeout(400)
    after = page.evaluate("""() => ({
      contexts: window.__audioContexts,
      state: document.querySelector('[data-room]').dataset.state,
      label: document.querySelector('[data-sound]').textContent.trim(),
    })""")
    rep.note("a real click unlocks audio and replays the opening from its hold",
             after, after["contexts"] == 1 and after["state"] in ("boot", "typing")
             and after["label"] == "Mute")
    page.close()


def check_touch(browser, rep, out):
    """A phone gets Tap, a big enough target, and no sideways scroll."""
    ctx = browser.new_context(viewport=PHONE, has_touch=True, is_mobile=True,
                              device_scale_factor=1)
    page = open_page(ctx, rep)
    wait_state(page, "room-ready", timeout=25000)
    page.wait_for_timeout(250)
    page.screenshot(path=str(out / "10-phone-room.png"))

    say = page.eval_on_selector("[data-go-label]", "el => el.textContent")
    rep.note("D: a touch layout is invited to TAP", say, say == "TAP!")

    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
    rep.note("no horizontal overflow on a phone", overflow, overflow == 0)

    hand = page.evaluate("""() => {
      const r = document.querySelector('.invite__hand').getBoundingClientRect();
      return {top: Math.round(r.top), left: Math.round(r.left), w: Math.round(r.width)};
    }""")
    rep.note("D: the hand has a deliberate place on a phone, not cropped off",
             hand, hand["top"] > 0 and hand["left"] > 0)

    box = page.eval_on_selector(GO, "el => { const r = el.getBoundingClientRect();"
                                " return {w: r.width, h: r.height}; }")
    rep.note("the button is a comfortable tap target on a phone",
             f"{round(box['w'])}x{round(box['h'])}", box["w"] >= 88 and box["h"] >= 44)

    page.tap(GO)
    wait_state(page, "desktop")
    rep.note("a single tap enters", state(page), state(page) == "desktop")
    page.close()
    ctx.close()


# ------------------------------------------------------------------ skipping


def check_skip(ctx, rep, out):
    """Skip has to resolve to the finished room from any phase, at once."""
    for phase, arrive in (
        ("boot", lambda p: p.wait_for_timeout(350)),
        ("typing", lambda p: wait_state(p, "typing")),
        ("revealing-room", lambda p: wait_state(p, "revealing-room", timeout=25000)),
    ):
        page = open_page(ctx, rep)
        arrive(page)
        was = state(page)
        page.click("[data-skip]")
        page.wait_for_timeout(120)
        got = finished(page)
        got["from"] = was
        # Skip has nothing left to skip, so it goes. The sound control stays:
        # the opening is short, and it is the only way to hear it.
        got["skip hidden"] = page.eval_on_selector("[data-skip]", "el => el.hidden")
        got["sound offered"] = page.eval_on_selector(
            "[data-sound]", "el => !el.hidden && el.textContent.trim()")
        rep.note(f"Skip during {phase} lands on the finished button state", got,
                 is_finished(got) and got["skip hidden"] and got["invite"] == "on"
                 and got["sound offered"] == "Play intro with sound")
        page.close()

    # Escape is the keyboard's Skip, and focus must not be stranded.
    page = open_page(ctx, rep)
    wait_state(page, "typing")
    page.keyboard.press("Escape")
    page.wait_for_timeout(150)
    focus = page.evaluate(
        "() => { const a = document.activeElement; return a && a.dataset.go !== undefined"
        " ? 'button' : (a ? a.tagName : 'none'); }")
    rep.note("Escape skips too, and focus lands on the button",
             {"state": state(page), "focus": focus},
             state(page) == "room-ready" and focus == "button")
    page.screenshot(path=str(out / "11-skipped.png"))
    page.close()


def check_second_visit(ctx, rep):
    """Moving between pages and back must not replay the boot sequence.

    sessionStorage belongs to the TAB, so this has to be one page navigating,
    not a second page: a new tab is a new session and is meant to see it again.
    """
    # Not open_page(): its init script clears the flag on EVERY navigation,
    # which would wipe the very thing this check is about. A brand-new tab
    # already starts with an empty session.
    page = ctx.new_page()
    page.on("pageerror", lambda e: rep.console.append("pageerror: {}".format(e)))
    page.goto(BASE + "/", wait_until="networkidle")
    wait_state(page, "room-ready", timeout=25000)

    page.goto(BASE + "/about/", wait_until="networkidle")
    page.goto(BASE + "/", wait_until="networkidle")
    page.wait_for_timeout(300)
    got = finished(page)
    rep.note("a refresh inside the session lands straight on the finished room", got,
             is_finished(got))
    page.close()


# ------------------------------------------------------------------- E and back


def check_enter_and_return(ctx, rep, out):
    page = open_page(ctx, rep)
    wait_state(page, "room-ready", timeout=25000)

    before = screen_box(page)
    page.click(GO)
    page.wait_for_timeout(400)
    mid = page.eval_on_selector(
        "[data-world]", "el => getComputedStyle(el).transform")
    rep.note("E: clicking flies into the screen", mid[:28] + "...", mid.startswith("matrix"))
    page.screenshot(path=str(out / "12-entering.png"))

    for _ in range(3):
        page.click(GO, force=True)  # repeated activation must be ignored
    wait_state(page, "desktop")
    page.wait_for_timeout(250)
    page.screenshot(path=str(out / "13-desktop.png"))
    rep.note("E: repeated clicks during the flight are ignored", state(page),
             state(page) == "desktop")
    rep.note("E: the desktop is visible and interactive",
             page.eval_on_selector("[data-desktop]",
                                   "el => ({hidden: el.hidden, inert: el.inert})"),
             page.eval_on_selector("[data-desktop]", "el => !el.hidden && !el.inert"))

    page.click("[data-start]")
    page.click("[data-leave]")
    wait_state(page, "room-ready")
    page.wait_for_timeout(250)
    page.screenshot(path=str(out / "14-returned.png"))
    got = finished(page)
    rep.note("E: returning restores the button and the demonstration", got,
             is_finished(got) and got["invite"] == "on")

    page.click(GO)
    wait_state(page, "desktop")
    rep.note("E: and it can be entered again", state(page), state(page) == "desktop")
    page.keyboard.press("Escape")
    wait_state(page, "room-ready")
    rep.note("E: Escape returns from the desktop", state(page), state(page) == "room-ready")
    page.close()


def check_keyboard(ctx, rep, out):
    page = open_page(ctx, rep)
    wait_state(page, "room-ready", timeout=25000)
    page.keyboard.press("Tab")
    name = page.evaluate("() => document.activeElement.textContent.trim()")
    rep.note("the button is reachable by keyboard", name, name == "CLICK!")
    ring = page.evaluate("""() => { const s = getComputedStyle(document.activeElement);
        return s.outlineWidth + ' ' + s.outlineColor; }""")
    rep.note("focus is visible", ring, ring.split()[0] != "0px")
    page.screenshot(path=str(out / "15-focus.png"))
    page.keyboard.press("Enter")
    wait_state(page, "desktop")
    rep.note("Enter activates it", state(page), state(page) == "desktop")
    page.close()


# ------------------------------------------------------------ robustness


def check_theme_midway(ctx, rep, out):
    """A theme change during the introduction must not lose progress."""
    page = open_page(ctx, rep)
    wait_state(page, "typing")
    page.wait_for_timeout(400)
    before = glass_lines(page)
    page.click(".theme-toggle--room")
    page.wait_for_timeout(250)
    after = glass_lines(page)
    theme = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
    grew = len(after[0]) + len(after[1]) >= len(before[0]) + len(before[1])
    rep.note("the theme can be changed mid-introduction without losing it",
             {"theme": theme, "before": before[0][:18], "after": after[0][:18], "state": state(page)},
             grew and state(page) in ("typing", "revealing-room", "room-ready"))
    page.screenshot(path=str(out / "16-theme-midway.png"))
    wait_state(page, "room-ready", timeout=25000)
    rep.note("and it still finishes", finished(page), is_finished(finished(page)))
    page.close()


def check_resize_midway(ctx, rep):
    """A resize during the zoom out must land, not hang between states."""
    page = open_page(ctx, rep)
    wait_state(page, "revealing-room", timeout=25000)
    page.set_viewport_size({"width": 1100, "height": 760})
    page.wait_for_timeout(400)
    rep.note("a resize during the zoom out resolves instead of sticking",
             finished(page), is_finished(finished(page)))
    page.close()


def check_reduced_motion(browser, rep, out):
    ctx = browser.new_context(viewport=DESKTOP, reduced_motion="reduce",
                              device_scale_factor=1)
    page = open_page(ctx, rep)
    page.wait_for_timeout(900)
    got = finished(page)
    rep.note("reduced motion: straight to the finished room, no character animation",
             got, is_finished(got))
    page.screenshot(path=str(out / "17-reduced.png"))

    still = page.evaluate("""() => ({
      moving: document.querySelector('.invite').getAnimations({subtree: true})
        .filter(a => a.playState === 'running').length,
      button: !document.querySelector('[data-go]').hidden,
      label: document.querySelector('[data-go-label]').textContent,
      burst: getComputedStyle(document.querySelector('.crt__fx')).display,
    })""")
    rep.note("reduced motion: a stationary hand, a usable button, no burst", still,
             still["moving"] == 0 and still["button"] and still["label"] == "CLICK!"
             and still["burst"] == "none")

    page.click(GO)
    wait_state(page, "desktop")
    rep.note("reduced motion: entering arrives without the flight", state(page),
             state(page) == "desktop")
    page.close()
    ctx.close()


def check_no_script(browser, rep, out):
    """With no JavaScript there is no introduction, and the room is not covered."""
    ctx = browser.new_context(viewport=DESKTOP, java_script_enabled=False,
                              device_scale_factor=1)
    page = ctx.new_page()
    page.goto(BASE + "/", wait_until="networkidle")
    hidden = page.eval_on_selector("[data-intro-controls]",
                                   "el => getComputedStyle(el).display")
    settled = page.eval_on_selector("[data-world]", "el => getComputedStyle(el).transform")
    rep.note("without JavaScript the room is already at rest and has no intro controls",
             {"controls": hidden, "camera": settled},
             hidden == "none" and settled in ("none", "matrix(1, 0, 0, 1, 0, 0)"))
    page.screenshot(path=str(out / "18-no-script.png"))
    page.close()
    ctx.close()


def check_no_rain(ctx, rep):
    """The binary rain, glyph streams and hacker-terminal decoration are gone."""
    page = open_page(ctx, rep)
    page.wait_for_timeout(500)
    found = page.evaluate("""() => {
      const bad = ['.boot', '.boot__rain', '.boot__col', '.boot__screen', '[data-boot]'];
      const hits = bad.filter(s => document.querySelector(s));
      // Any element whose text is only 0s, 1s and spaces would be a glyph stream.
      const streams = [...document.querySelectorAll('.room *')].filter(e => {
        const t = (e.textContent || '').trim();
        return t.length > 3 && /^[01 ]+$/.test(t);
      }).length;
      return {leftoverNodes: hits, glyphStreams: streams};
    }""")
    rep.note("the Matrix treatment is gone: no rain, no glyph streams, no terminal panel",
             found, not found["leftoverNodes"] and found["glyphStreams"] == 0)
    page.close()


def check_other_pages(ctx, rep):
    for path in ("/projects/", "/about/", "/contact/"):
        page = open_page(ctx, rep, path)
        nav = page.eval_on_selector_all(".nav__link", "els => els.length")
        rep.note(f"{path} still renders with site chrome", f"{nav} nav links", nav == 4)
        page.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="artifacts/room")
    ap.add_argument("--only", default=None)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rep = Report()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport=DESKTOP, device_scale_factor=1)
        groups = {
            "opening": lambda: check_opening(ctx, rep, out),
            "geometry": lambda: check_reveal_geometry(browser, rep, out),
            "invitation": lambda: check_invitation(ctx, rep, out),
            "sound": lambda: check_sound_offer(ctx, rep, out),
            "touch": lambda: check_touch(browser, rep, out),
            "skip": lambda: check_skip(ctx, rep, out),
            "second": lambda: check_second_visit(ctx, rep),
            "enter": lambda: check_enter_and_return(ctx, rep, out),
            "keyboard": lambda: check_keyboard(ctx, rep, out),
            "theme": lambda: check_theme_midway(ctx, rep, out),
            "resize": lambda: check_resize_midway(ctx, rep),
            "reduced": lambda: check_reduced_motion(browser, rep, out),
            "noscript": lambda: check_no_script(browser, rep, out),
            "norain": lambda: check_no_rain(ctx, rep),
            "pages": lambda: check_other_pages(ctx, rep),
        }
        for name, fn in groups.items():
            if args.only and args.only != name:
                continue
            fn()
        ctx.close()
        browser.close()

    rep.dump()
    (out / "report.json").write_text(
        json.dumps({"checks": rep.rows, "console": rep.console}, indent=1), encoding="utf-8"
    )
    sys.exit(1 if rep.failures or rep.console else 0)


if __name__ == "__main__":
    main()
