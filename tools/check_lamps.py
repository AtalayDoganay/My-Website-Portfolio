"""Verify the five wall lamps on the demonstrated CLICK: lit at contact, fading
to nothing over the two seconds after the finger lifts, gone in between, on the
click's own clock. Also writes the review's captures.

    .venv/Scripts/python.exe tools/check_lamps.py --out artifacts/lamps \
        --evidence docs/evidence/click/after

What it measures, rather than assumes:

  - the lamp animations share the hand animation's start time and duration;
  - in REAL TIME, over three consecutive cycles, the frame the key goes down
    is the frame the lamps begin to light; the key is back up within a
    quarter of a second; the lamps are at full light for only the press,
    fade for about 1.8s, and are then HIDDEN (visibility) for at least a
    second before the next click - while a lamp takes the pointer it is at
    half brightness or more, and it refuses the pointer before it is faint;
  - there is no halo on the wall behind the machine, and each lamp's own
    patch of light stays inside the lamp's box;
  - in the dark phase a lamp cannot be hovered, clicked, tapped or tabbed
    into, and hovering its reserved position reveals nothing;
  - while lit a lamp can be hovered, clicked (it navigates) and tabbed into
    with a visible focus ring;
  - a lamp that has focus at the cutoff hands it to the reveal control;
  - the manual reveal control shows a steady lit menu with the glove at rest
    and the cycle stopped, Escape closes it, returns focus and restarts the
    cycle; under reduced motion that control is the only reveal;
  - a real activation lights them once and the desktop leaves them inert;
  - cycles do not accumulate animations or interval timers;
  - on a desktop, a laptop-shaped window and a phone, in both themes: the
    icons and headings are the larger sizes, the five groups are inside the
    window, 44px+, well apart from each other, and clear of the machine, the
    glass and the controls.

Run `node serve.mjs` first.
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
RESUME = """() => document.querySelectorAll(
      '.invite, .invite *, .crt__fx, .crt__fx *, .crt__go, .crt__go-face, .lamp')
    .forEach(el => el.getAnimations({subtree: true}).forEach(a => a.play()))"""
LAMP = """sel => { const el = document.querySelector(sel); const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return {lit: parseFloat(cs.getPropertyValue('--lit')) || 0, visibility: cs.visibility,
            opacity: parseFloat(cs.opacity), pointer: cs.pointerEvents,
            x: r.x + r.width / 2, y: r.y + r.height / 2, w: r.width, h: r.height}; }"""
COUNTERS = """(() => { window.__timers = {timeouts: 0, intervals: 0};
    const st = window.setTimeout, si = window.setInterval;
    window.setTimeout = function () { window.__timers.timeouts++; return st.apply(window, arguments); };
    window.setInterval = function () { window.__timers.intervals++; return si.apply(window, arguments); }; })()"""
# Per frame: [t, key travel, --lit, visible, takes pointer]
SAMPLE = """ms => new Promise(done => {
  const face = document.querySelector('.crt__go-face');
  const lamp = document.querySelector('.lamp--projects');
  const out = [];
  const t0 = performance.now();
  function tick(now) {
    const tr = getComputedStyle(face).translate.split(' ');
    const cs = getComputedStyle(lamp);
    out.push([Math.round(now - t0), parseFloat(tr[1] || tr[0]) || 0,
              parseFloat(cs.getPropertyValue('--lit')) || 0, cs.visibility === 'visible' ? 1 : 0,
              cs.pointerEvents === 'auto' ? 1 : 0]);
    if (now - t0 < ms) requestAnimationFrame(tick); else done(out);
  }
  requestAnimationFrame(tick);
})"""
BEAT = """() => {
  const a = document.querySelector('.invite__hand').getAnimations()
    .find(x => x.animationName === 'invite-hand');
  const d = a.effect.getTiming().duration, k = a.effect.getKeyframes();
  const l = document.querySelector('.lamp').getAnimations().find(x => x.animationName === 'lamp-cycle');
  const lk = l ? l.effect.getKeyframes() : [];
  let live = false, cutoff = null, hidden = null, shown = null;
  for (const f of lk) {
    if (f.pointerEvents === 'auto') live = true;
    else if (live && cutoff === null && f.pointerEvents === 'none') cutoff = f.computedOffset * d;
    if (f.visibility === 'visible' && shown === null) shown = f.computedOffset * d;
    if (shown !== null && hidden === null && f.visibility === 'hidden' && f.computedOffset > 0) hidden = f.computedOffset * d;
  }
  return {duration: d, contact: k[2].computedOffset * d, lift: k[4].computedOffset * d,
          cutoff, shown, hidden};
}"""


class Report:
    def __init__(self):
        self.notes = []
        self.fails = 0

    def note(self, name, detail, ok):
        self.notes.append({"check": name, "ok": bool(ok), "detail": detail})
        print(("  ok   " if ok else "  FAIL ") + name + " -- " + json.dumps(detail, default=str)[:230])
        if not ok:
            self.fails += 1


def open_room(ctx, counters=False):
    page = ctx.new_page()
    page.add_init_script("sessionStorage.setItem('atalay.intro','1')")
    if counters:
        page.add_init_script(COUNTERS)
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_function("document.querySelector('[data-room]').dataset.state === 'room-ready'")
    page.wait_for_function("document.querySelector('[data-room]').dataset.invite === 'on'")
    page.wait_for_timeout(120)
    return page


def beat(page):
    return page.evaluate(BEAT)


def edges(samples, index, threshold):
    out, below = [], samples[0][index] <= threshold
    for row in samples:
        v = row[index]
        if below and v > threshold:
            out.append(row[0])
            below = False
        elif v <= threshold:
            below = True
    return out


def run(samples, start, index, threshold):
    t0 = t1 = None
    for row in samples:
        if row[0] < start:
            continue
        if row[index] > threshold:
            if t0 is None:
                t0 = row[0]
            t1 = row[0]
        elif t0 is not None:
            break
    return (t0, t1) if t0 is not None else None


def check_sync(ctx, rep, out):
    page = open_room(ctx, counters=True)
    b = beat(page)
    clock = page.evaluate("""() => {
      const a = document.querySelector('.invite__hand').getAnimations()[0];
      const ls = [...document.querySelectorAll('.lamp')].map(l => l.getAnimations()[0]);
      return {hand: [a.startTime, a.effect.getTiming().duration],
              lamps: ls.map(l => l ? [l.startTime, l.effect.getTiming().duration] : null)};
    }""")
    rep.note("the five lamps run on the hand's own animation clock",
             {"cycle": b, **clock},
             len(clock["lamps"]) == 5 and all(l and abs(l[0] - clock["hand"][0]) <= 20 and l[1] == clock["hand"][1]
                                              for l in clock["lamps"]))
    rep.note("the named beats read from the keyframes: contact, a ~100ms press, a cutoff at half light, a ~2s visible span",
             b, b["cutoff"] is not None and b["hidden"] is not None
             and 80 <= b["lift"] - b["contact"] <= 130
             and 900 <= b["cutoff"] - b["contact"] <= 1200
             and 1900 <= b["hidden"] - b["shown"] <= 2100
             and b["duration"] - b["hidden"] + b["contact"] >= 1000)
    # Static facts about the five: each heading reads as its label (wrapped
    # lines must not run together where a layout puts them inline), each light
    # patch has a colour, and the wall behind the machine has no halo.
    facts = page.evaluate("""() => [...document.querySelectorAll('.lamp')].map(l => ({
      id: l.dataset.lamp, text: l.querySelector('.lamp__text').textContent.trim().replace(/\\s+/g, ' '),
      patch: getComputedStyle(l.querySelector('.lamp__glow')).backgroundImage}))""")
    labels = {"github": "GitHub", "about": "About Me", "projects": "Projects I Have Done So Far",
              "social": "Other Social Medias", "degrees": "Degrees, Certificates & Skills"}
    rep.note("each lamp's heading reads as its label, wrapped lines included",
             [[f["id"], f["text"]] for f in facts],
             len(facts) == 5 and all(f["text"] == labels.get(f["id"]) for f in facts))
    rep.note("each lamp's light patch has a colour of its own",
             [[f["id"], f["patch"][:48]] for f in facts],
             len(facts) == 5 and all(f["patch"] not in ("none", "") for f in facts))
    halo = page.evaluate("""() => ({glowElement: !!document.querySelector('.room__glow'),
      wallGradients: [...document.querySelectorAll('.room__env *')].map(e => getComputedStyle(e).backgroundImage)
        .filter(v => v.includes('radial-gradient')).length})""")
    rep.note("no halo on the wall behind the machine", halo, not halo["glowElement"] and halo["wallGradients"] == 0)

    before = page.evaluate("() => ({anims: document.getAnimations().length, timers: window.__timers})")
    # Long enough to hold three complete clicks wherever the sampling starts.
    samples = page.evaluate(SAMPLE, int(b["duration"] * 3.9) + 400)
    after = page.evaluate("() => ({anims: document.getAnimations().length, timers: window.__timers})")
    frame = max(17, max(y[0] - x[0] for x, y in zip(samples, samples[1:])))
    presses, lights = edges(samples, 1, 0.3), edges(samples, 2, 0.05)
    pairs = [[tp, min(lights, key=lambda tl: abs(tl - tp)) if lights else None] for tp in presses]
    pairs = [[tp, tl, None if tl is None else tl - tp] for tp, tl in pairs]
    rep.note("in real time the lamps begin to light on the frame the key goes down, three consecutive cycles",
             {"press->light ms": pairs, "frame ms": frame},
             len(pairs) >= 3 and all(p[2] is not None and abs(p[2]) <= frame + 1 for p in pairs))
    gaps = [q - p for p, q in zip(presses, presses[1:])]
    rep.note("and the cycles keep the demonstration's cadence", {"gaps": gaps, "cycle": b["duration"]},
             len(gaps) >= 2 and all(abs(g - b["duration"]) <= 60 for g in gaps))
    key_down = [run(samples, tp, 1, 0.3) for tp in presses[:3]]
    key_down = [k[1] - k[0] for k in key_down if k]
    rep.note("the key is down for only the press and back up at once", {"key down ms": key_down},
             len(key_down) >= 3 and all(60 <= k <= 200 for k in key_down))
    full, fades, shown, dark, gap_after = [], [], [], [], []
    for i, tl in enumerate(lights[:3]):
        lit = run(samples, tl, 2, 0.95)
        vis = run(samples, tl - 100, 3, 0.5)
        if lit:
            full.append(lit[1] - lit[0])
            fade = run(samples, lit[1] + 1, 2, 0.05)
            if fade:
                fades.append(fade[1] - lit[1])
        if vis:
            shown.append(vis[1] - vis[0])
            hidden = [r for r in samples if vis[1] + frame < r[0] < vis[1] + 900]
            dark.append(all(r[3] == 0 and r[2] == 0 for r in hidden) and bool(hidden))
            nxt = [tp for tp in presses if tp > vis[1]]
            if nxt:
                gap_after.append(nxt[0] - vis[1])
    rep.note("full light for only the press, a ~1.8s fade to nothing, HIDDEN for a second or more before the next click",
             {"full ms": full, "fade ms": fades, "visible ms": shown, "hidden after": dark, "dark before next press ms": gap_after},
             len(full) >= 3 and all(60 <= f <= 260 for f in full)
             and len(fades) >= 3 and all(1500 <= f <= 1950 for f in fades)
             and len(shown) >= 3 and all(1850 <= s <= 2150 for s in shown) and all(dark)
             and len(gap_after) >= 2 and all(g >= 1000 for g in gap_after))
    live = [r for r in samples if r[4] == 1]
    faint_live = [r for r in live if r[2] < 0.4]
    unlive_visible = [r for r in samples if r[3] == 1 and r[4] == 0 and 0.05 < r[2] < 0.4]
    rep.note("a lamp takes the pointer only at half light or more, and refuses it while still faintly visible",
             {"pointer frames": len(live), "dimmest live": min((r[2] for r in live), default=None),
              "faint frames that still took the pointer": len(faint_live), "faint frames refusing it": len(unlive_visible)},
             live and not faint_live and len(unlive_visible) >= 3)
    rep.note("repeat cycles accumulate no animations and no interval timers",
             {"before": before, "after": after},
             after["anims"] == before["anims"] and after["timers"]["intervals"] == 0)
    (out / "samples.json").write_text(json.dumps(samples), encoding="utf-8")

    # --- the dark phase: nothing there for pointer, tap or keyboard --------
    page.evaluate(PARK, 100)
    page.wait_for_timeout(60)
    box = page.evaluate(LAMP, ".lamp--github")
    page.mouse.move(box["x"], box["y"])
    page.wait_for_timeout(80)
    under = page.evaluate("p => { const e = document.elementFromPoint(p.x, p.y); return e ? (e.closest('.lamp') ? 'lamp' : (e.className.baseVal || e.className || e.tagName)) : 'none'; }",
                          {"x": box["x"], "y": box["y"]})
    dark_state = page.evaluate(LAMP, ".lamp--github")
    rep.note("dark: hovering a lamp's reserved position reveals nothing and hits nothing",
             {"under pointer": under, **dark_state},
             under != "lamp" and dark_state["visibility"] == "hidden" and dark_state["lit"] == 0
             and dark_state["opacity"] == 0 and dark_state["w"] > 0)
    url_before = page.url
    page.mouse.click(box["x"], box["y"])
    page.wait_for_timeout(400)
    rep.note("dark: a click on that position goes nowhere", {"url": page.url, "state": page.evaluate("() => document.querySelector('[data-room]').dataset.state")},
             page.url == url_before)
    page.evaluate("() => document.querySelector('[data-go]').focus()")
    landed = []
    for _ in range(6):
        page.keyboard.press("Tab")
        landed.append(page.evaluate("() => { const a = document.activeElement; return a.closest('.lamp') ? 'LAMP' : (a.dataset.reveal !== undefined ? 'reveal' : a.className || a.tagName); }"))
    rep.note("dark: Tab never reaches a lamp", landed, "LAMP" not in landed)

    # --- the faint tail of the fade: visible, but nothing to click ----------
    page.evaluate(PARK, b["cutoff"] + (b["hidden"] - b["cutoff"]) * 0.6)
    page.wait_for_timeout(60)
    tail = page.evaluate(LAMP, ".lamp--about")
    under = page.evaluate("p => { const e = document.elementFromPoint(p.x, p.y); return e && e.closest('.lamp') ? 'lamp' : 'none'; }",
                          {"x": tail["x"], "y": tail["y"]})
    rep.note("late in the fade a lamp is still faintly visible but takes no pointer", {**tail, "under pointer": under},
             tail["visibility"] == "visible" and 0 < tail["lit"] < 0.4 and tail["pointer"] == "none" and under != "lamp")

    # --- the lit phase: usable, with visible focus --------------------------
    page.evaluate(PARK, b["contact"] + 80)
    page.wait_for_timeout(60)
    lit_state = page.evaluate(LAMP, ".lamp--about")
    page.mouse.move(lit_state["x"], lit_state["y"])
    page.wait_for_timeout(60)
    under = page.evaluate("p => { const e = document.elementFromPoint(p.x, p.y); return e && e.closest('.lamp') ? e.closest('.lamp').dataset.lamp : 'none'; }",
                          {"x": lit_state["x"], "y": lit_state["y"]})
    rep.note("lit: the lamp is visible, at full light and under the pointer", {**lit_state, "under pointer": under},
             lit_state["visibility"] == "visible" and lit_state["lit"] >= 0.99 and lit_state["opacity"] >= 0.99 and under == "about")
    page.evaluate("() => document.querySelector('[data-go]').focus()")
    page.keyboard.press("Tab")
    focused = page.evaluate("""() => { const a = document.activeElement; const s = getComputedStyle(a);
        return {who: a.dataset.lamp || a.className, ring: s.outlineWidth + ' ' + s.outlineColor}; }""")
    rep.note("lit: Tab from the key reaches the first lamp with a visible ring", focused,
             focused["who"] == "github" and focused["ring"].split()[0] != "0px")
    page.mouse.click(lit_state["x"], lit_state["y"])
    page.wait_for_url("**/about/**", timeout=5000)
    rep.note("lit: clicking About Me navigates to the About page", page.url, "/about/" in page.url)
    page.close()

    # --- focus hands back to the reveal control at the cutoff ---------------
    page = open_room(ctx)
    b = beat(page)
    page.wait_for_function("""(b) => { const a = document.querySelector('.invite__hand').getAnimations()[0];
        const t = a.currentTime % b.duration; return t > b.contact + 100 && t < b.contact + 500; }""", arg=b)
    page.evaluate("() => document.querySelector('.lamp--projects').focus()")
    had = page.evaluate("() => document.activeElement.dataset.lamp || null")
    page.wait_for_function("""(b) => { const a = document.querySelector('.invite__hand').getAnimations()[0];
        const t = a.currentTime % b.duration; return t > b.cutoff + 250; }""", arg=b)
    now = page.evaluate("() => ({who: document.activeElement.dataset.reveal !== undefined ? 'reveal' : (document.activeElement.dataset.lamp || document.activeElement.tagName), lamp: getComputedStyle(document.querySelector('.lamp--projects')).pointerEvents})")
    rep.note("a lamp focused while lit hands focus to the reveal control at the cutoff",
             {"focused while lit": had, "after the cutoff": now}, had == "projects" and now["who"] == "reveal" and now["lamp"] == "none")

    # --- the manual reveal control ------------------------------------------
    page.evaluate(PARK, 100)
    page.click("[data-reveal]")
    page.wait_for_timeout(120)
    opened = page.evaluate("""() => ({links: document.querySelector('[data-room]').dataset.links,
        expanded: document.querySelector('[data-reveal]').getAttribute('aria-expanded'),
        label: document.querySelector('[data-reveal]').textContent.trim(),
        lamps: [...document.querySelectorAll('.lamp')].map(l => [l.dataset.lamp, getComputedStyle(l).visibility, parseFloat(getComputedStyle(l).opacity)]),
        demo: document.querySelector('.invite__hand').getAnimations().length
            + document.querySelector('.crt__go-face').getAnimations().length
            + document.querySelector('.burst__bit').getAnimations().length,
        glove: getComputedStyle(document.querySelector('.invite__hand')).transform,
        key: getComputedStyle(document.querySelector('.crt__go-face')).translate,
        burst: getComputedStyle(document.querySelector('.burst__bit')).opacity})""")
    raised = opened["glove"] not in ("none", "") and float(opened["glove"].split(",")[-1].strip(" )")) < 0
    rep.note("the reveal control shows all five lamps steadily, with the cycle stopped and the glove raised at rest", opened,
             opened["links"] == "open" and opened["expanded"] == "true" and opened["label"] == "Hide links"
             and len(opened["lamps"]) == 5 and all(l[1] == "visible" and l[2] >= 0.99 for l in opened["lamps"])
             and opened["demo"] == 0 and raised and opened["key"] in ("none", "0px", "0px 0px") and float(opened["burst"]) == 0)
    page.keyboard.press("Escape")
    page.wait_for_timeout(120)
    closed = page.evaluate("""() => ({links: document.querySelector('[data-room]').dataset.links,
        focus: document.activeElement.dataset.reveal !== undefined,
        label: document.querySelector('[data-reveal]').textContent.trim(),
        lamp: getComputedStyle(document.querySelector('.lamp--github')).visibility,
        demo: document.querySelector('.invite__hand').getAnimations().length})""")
    rep.note("Escape closes it, returns focus to the control, hides the lamps and restarts the cycle", closed,
             closed["links"] == "closed" and closed["focus"] and closed["label"] == "Show links" and closed["lamp"] == "hidden"
             and closed["demo"] == 1)
    page.close()


def check_activation(ctx, rep, out):
    page = open_room(ctx)
    b = beat(page)
    page.wait_for_function("""(b) => { const a = document.querySelector('.invite__hand').getAnimations()[0];
        const t = a.currentTime % b.duration; return t > b.hidden + 150 && t < b.hidden + 400; }""", arg=b)
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
    rep.note("a real activation in the dark phase lights the lamps at once", peak, peak["best"] >= 0.95 and peak["at"] <= 120)
    page.wait_for_function("document.querySelector('[data-room]').dataset.state === 'desktop'", timeout=15000)
    page.wait_for_timeout(200)
    state = page.evaluate("""() => ({inert: document.querySelector('[data-lamps]').inert,
      hidden: getComputedStyle(document.querySelector('[data-room]')).visibility,
      desktopLinks: [...document.querySelectorAll('.win__link')].map(a => a.getAttribute('href'))})""")
    stray = []
    for _ in range(10):
        page.keyboard.press("Tab")
        hit = page.evaluate("() => document.activeElement.closest && document.activeElement.closest('.lamp') ? document.activeElement.className : null")
        if hit:
            stray.append(hit)
    rep.note("on the desktop the lamps are inert and never take focus; the desktop lists the same destinations",
             {**state, "focused lamps over 10 tabs": stray},
             state["inert"] is True and state["hidden"] == "hidden" and not stray and len(state["desktopLinks"]) == 5)
    page.keyboard.press("Escape")
    page.wait_for_function("document.querySelector('[data-room]').dataset.state === 'room-ready'")
    rep.note("back in the room the lamps are usable again", {"inert": page.evaluate("() => document.querySelector('[data-lamps]').inert")},
             page.evaluate("() => document.querySelector('[data-lamps]').inert") is False)
    page.close()


def check_reduced(browser, rep, evidence):
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce",
                              color_scheme="dark", device_scale_factor=1)
    page = ctx.new_page()
    page.add_init_script("sessionStorage.setItem('atalay.intro','1')")
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_function("document.querySelector('[data-room]').dataset.state === 'room-ready'")
    page.wait_for_timeout(300)
    d = page.evaluate("""() => ({
      running: [...document.querySelectorAll('.lamp')].flatMap(l => l.getAnimations()).length,
      hidden: [...document.querySelectorAll('.lamp')].every(l => getComputedStyle(l).visibility === 'hidden'),
      control: document.querySelector('[data-reveal]') ? getComputedStyle(document.querySelector('[data-reveal]')).visibility : null})""")
    rep.note("reduced motion: no loop, lamps hidden, the labelled reveal control is there", d,
             d["running"] == 0 and d["hidden"] and d["control"] == "visible")
    page.click("[data-reveal]")
    page.wait_for_timeout(120)
    o = page.evaluate("() => [...document.querySelectorAll('.lamp')].map(l => getComputedStyle(l).visibility)")
    rep.note("reduced motion: the control opens a steady menu", o, len(o) == 5 and all(v == "visible" for v in o))
    page.screenshot(path=str(evidence / "reduced-motion-menu-open-dark.png"))
    page.keyboard.press("Escape")
    page.wait_for_timeout(120)
    page.screenshot(path=str(evidence / "reduced-motion-menu-closed-dark.png"))
    ctx.close()


# The equipment's boxes as fractions of the artwork's displayed box, measured
# on the drawn pixels: on the wide canvas the monitor and tower stand between
# 28% and 73% of its width from 14% down, and the keyboard and mouse run on to
# 87% along the bottom band; the compact canvas is all machine from 10% down.
# The desk is furniture and may sit under a lamp.
EQUIPMENT = {"wide": [(0.28, 0.14, 0.73, 0.88), (0.28, 0.72, 0.87, 0.88)],
             "compact": [(0.0, 0.10, 1.0, 1.0)]}
VIEWPORTS = (("desktop", (1440, 900)), ("laptop", (1472, 695)), ("phone", (390, 844)))


def capture(browser, rep, out, evidence):
    layouts = []
    for device, (w, h) in VIEWPORTS:
        for theme in ("dark", "light"):
            ctx = browser.new_context(viewport={"width": w, "height": h}, color_scheme=theme, device_scale_factor=1,
                                      has_touch=device == "phone", is_mobile=device == "phone")
            page = open_room(ctx)
            b = beat(page)
            frames = (("dark", 100), ("contact", b["contact"] + 40), ("lifted", b["contact"] + 400),
                      ("midfade", b["contact"] + 1100), ("hidden", b["hidden"] + 200))
            for name, ms in frames:
                page.evaluate(PARK, ms)
                page.wait_for_timeout(80)
                page.screenshot(path=str(evidence / f"{device}-{theme}-{name}.png"))
            page.evaluate(PARK, b["contact"] + 80)
            page.wait_for_timeout(60)
            boxes = page.evaluate("""() => [...document.querySelectorAll('.lamp')].map(l => { const r = l.getBoundingClientRect();
                const g = l.querySelector('.lamp__glow').getBoundingClientRect();
                return {id: l.dataset.lamp, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
                        icon: Math.round(l.querySelector('.lamp__icon').getBoundingClientRect().width),
                        font: parseFloat(getComputedStyle(l).fontSize),
                        patchInside: g.x >= r.x - 1 && g.y >= r.y - 1 && g.right <= r.right + 1 && g.bottom <= r.bottom + 1}; })""")
            keep = page.evaluate("""() => { const q = s => { const r = document.querySelector(s).getBoundingClientRect();
                return {x: r.x, y: r.y, w: r.width, h: r.height}; };
                const art = [...document.querySelectorAll('.room__stage img')].map(i => i.getBoundingClientRect())
                  .filter(r => r.width > 0).sort((p, q) => q.width - p.width)[0];
                return {screen: q('[data-screen]'), toggle: q('[data-theme-toggle]'), sound: q('[data-sound]'), reveal: q('[data-reveal]'),
                        art: {x: art.x, y: art.y, w: art.width, h: art.height}}; }""")
            art = keep.pop("art")
            for j, (fx0, fy0, fx1, fy1) in enumerate(EQUIPMENT["wide" if art["w"] > art["h"] else "compact"]):
                keep[f"machine{j}"] = {"x": art["x"] + art["w"] * fx0, "y": art["y"] + art["h"] * fy0,
                                       "w": art["w"] * (fx1 - fx0), "h": art["h"] * (fy1 - fy0)}
            machine = {k: {kk: round(vv) for kk, vv in v.items()} for k, v in keep.items() if k.startswith("machine")}

            def hits(a, k, margin=0):
                return (a["x"] - margin < k["x"] + k["w"] and k["x"] < a["x"] + a["w"] + margin
                        and a["y"] - margin < k["y"] + k["h"] and k["y"] < a["y"] + a["h"] + margin)

            def gap(a, c):
                dx = max(a["x"] - (c["x"] + c["w"]), c["x"] - (a["x"] + a["w"]))
                dy = max(a["y"] - (c["y"] + c["h"]), c["y"] - (a["y"] + a["h"]))
                return max(dx, dy)

            room_gap = 24 if device != "phone" else 10
            close = [(a["id"], c["id"], round(gap(a, c))) for i, a in enumerate(boxes) for c in boxes[i + 1:] if gap(a, c) < room_gap]
            clear = [(a["id"], name) for a in boxes for name, k in keep.items() if hits(a, k)]
            inside = all(0 <= a["x"] and a["x"] + a["w"] <= w and 0 <= a["y"] and a["y"] + a["h"] <= h for a in boxes)
            big = all(a["w"] >= 44 and a["h"] >= 44 for a in boxes)
            icon, font = (48, 24) if device != "phone" else (32, 16)
            sized = all(a["icon"] >= icon and a["font"] >= font for a in boxes)
            patches = all(a["patchInside"] for a in boxes)
            rep.note(f"{device} {theme}: five lamps at the larger sizes, inside the window, 44px+, {room_gap}px+ apart, clear of the machine, the glass and the controls, patches inside their boxes",
                     {"boxes": boxes, "too close": close, "collisions": clear, "machine": machine},
                     len(boxes) == 5 and inside and big and sized and patches and not close and not clear)
            layouts.append({"device": device, "theme": theme, "boxes": boxes, "machine": machine})
            if device == "desktop" and theme == "dark":
                page.evaluate(RESUME)
                for k in range(3):
                    page.wait_for_function("() => parseFloat(getComputedStyle(document.querySelector('.lamp--projects')).getPropertyValue('--lit')) > 0.9")
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(evidence / f"live-click-{k + 1}.png"))
                    page.wait_for_function("() => getComputedStyle(document.querySelector('.lamp--projects')).visibility === 'hidden'")
                page.evaluate(PARK, b["contact"] + 80)
                page.wait_for_timeout(80)
                for lamp in ("github", "about", "projects", "social", "degrees"):
                    page.locator(f".lamp--{lamp}").screenshot(path=str(evidence / f"lamp-{lamp}.png"))
                page.evaluate(PARK, b["contact"] + 60)
                page.wait_for_timeout(80)
                page.locator("[data-screen]").screenshot(path=str(evidence / "glove-on-the-key.png"))
                page.evaluate(PARK, b["contact"] + 400)
                page.wait_for_timeout(80)
                page.locator("[data-screen]").screenshot(path=str(evidence / "glove-lifted.png"))
            ctx.close()
    (out / "layouts.json").write_text(json.dumps(layouts, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="artifacts/lamps")
    ap.add_argument("--evidence", default="docs/evidence/click/after")
    args = ap.parse_args()
    out, evidence = Path(args.out), Path(args.evidence)
    out.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    rep = Report()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme="dark", device_scale_factor=1)
        print("synchronization, dark phase, the fade's tail, lit phase, focus, reveal control")
        check_sync(ctx, rep, out)
        print("activation, desktop, return")
        check_activation(ctx, rep, out)
        ctx.close()
        print("reduced motion")
        check_reduced(browser, rep, evidence)
        print("captures")
        capture(browser, rep, out, evidence)
        browser.close()
    (out / "report.json").write_text(json.dumps(rep.notes, indent=2), encoding="utf-8")
    print(f"\n{len(rep.notes)} checks, {rep.fails} failures")
    sys.exit(1 if rep.fails else 0)


if __name__ == "__main__":
    main()
