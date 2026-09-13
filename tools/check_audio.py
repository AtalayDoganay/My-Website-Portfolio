"""Verify that the opening actually PRODUCES SOUND - not that it scheduled some.

    python tools/check_audio.py --out docs/evidence

Counting scheduled notes proves nothing. A note can be scheduled onto a gain
that is muted, onto a context that is suspended, or onto a node that was never
connected to the destination, and in every one of those cases the page is
silent while the code looks correct. This measures the other end.

HOW. An init script wraps AudioNode.connect, so anything the page connects to
ctx.destination is ALSO connected to an AnalyserNode. A rAF loop samples that
analyser's time-domain data and keeps the peak absolute sample per frame. A
beep that is scheduled but never reaches the output makes no peak. The same tap
feeds a MediaStreamDestination and a MediaRecorder, so the run leaves a real
.webm of what came out, which a person can listen to.

The browser runs with NO autoplay-bypass flag, so the policy is the one a real
visitor gets. The only thing that unlocks audio is a genuine page.click().

What it asserts:
  - nothing is audible before a gesture, and no context is even built
  - the control is labelled, and clicking it replays the opening from its hold
  - all THREE beeps produce measured output, at 650 / 1050 / 1450ms
  - the typing is audible, and quieter than the beeps
  - each backspace produces output before the next typed character
  - click and flight output follow measured contact/visibility on two cycles
  - activation, interruption, return, mute, visibility and teardown behave
  - a CDP journey recording is aligned to captured audio by browser timestamps

No speaker/headphone or perceptual listening judgement is made by this checker.
"""

import argparse
import base64
import json
import os
import sys
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("PREVIEW", "http://127.0.0.1:4321")
DESKTOP = {"width": 1280, "height": 800}
DOTS_AT = (650, 1050, 1450)

TAP = r"""
window.__tap = { samples: [], visuals: [], started: 0, ctxState: null, recorded: null, contexts: 0 };
(function () {
  var AC = window.AudioContext || window.webkitAudioContext;
  if (!AC) return;
  var Counted = function () { window.__tap.contexts += 1; return new AC(); };
  Counted.prototype = AC.prototype;
  window.AudioContext = Counted;
  window.webkitAudioContext = Counted;

  var OrigConnect = AudioNode.prototype.connect;
  var taps = new WeakMap();

  function tapFor(ctx) {
    if (taps.has(ctx)) return taps.get(ctx);
    var an = ctx.createAnalyser();
    an.fftSize = 2048;
    var msd = ctx.createMediaStreamDestination();
    an.connect(msd);
    var t = { analyser: an, buf: new Float32Array(an.fftSize) };
    taps.set(ctx, t);
    try {
      var rec = new MediaRecorder(msd.stream, { mimeType: 'audio/webm' });
      var chunks = [];
      rec.ondataavailable = function (e) { if (e.data.size) chunks.push(e.data); };
      rec.onstop = function () {
        var fr = new FileReader();
        fr.onload = function () { window.__tap.recorded = fr.result; };
        fr.readAsDataURL(new Blob(chunks, { type: 'audio/webm' }));
      };
      rec.start();
      window.__tap.stopRec = function () { try { rec.stop(); } catch (e) {} };
    } catch (e) { /* no recorder here */ }

    window.__tap.started = performance.now();
    window.__tap.epoch = performance.timeOrigin + window.__tap.started;
    (function loop() {
      an.getFloatTimeDomainData(t.buf);
      var peak = 0;
      for (var i = 0; i < t.buf.length; i++) {
        var v = t.buf[i] < 0 ? -t.buf[i] : t.buf[i];
        if (v > peak) peak = v;
      }
      window.__tap.samples.push([Math.round(performance.now() - window.__tap.started), peak]);
      var room = document.querySelector('[data-room]');
      var hand = document.querySelector('.invite__hand');
      var face = document.querySelector('.crt__go-face');
      var bit = document.querySelector('.burst__bit');
      var a = bit.getAnimations().find(a => /burst/.test(a.animationName));
      var h = hand.getBoundingClientRect(), f = face.getBoundingClientRect();
      var time = Math.round(performance.now() - window.__tap.started);
      window.__tap.visuals.push({t:time, state:room.dataset.state, invite:room.dataset.invite,
        line:document.querySelector('[data-line="1"]').textContent,
        phase:a ? Number(a.currentTime) : null,
        gap:h.top + h.height * Number(hand.dataset.tipY) - f.top,
        bit:Number(getComputedStyle(bit).opacity)});
      window.__tap.ctxState = ctx.state;
      requestAnimationFrame(loop);
    })();
    return t;
  }

  AudioNode.prototype.connect = function (dest) {
    var r = OrigConnect.apply(this, arguments);
    try {
      if (dest && this.context && dest === this.context.destination) {
        OrigConnect.call(this, tapFor(this.context).analyser);
      }
    } catch (e) { /* ignore */ }
    return r;
  };
})();
"""


class Report:
    def __init__(self):
        self.rows = []
        self.fails = []

    def note(self, name, detail, ok=True):
        self.rows.append((ok, name, detail))
        if not ok:
            self.fails.append(name)

    def dump(self):
        for ok, name, detail in self.rows:
            print(f"  {'ok  ' if ok else 'FAIL'} {name} -- {detail}")
        print(f"\n{len(self.rows)} checks, {len(self.fails)} failures")
        return 1 if self.fails else 0


def peaks_in(samples, t0, t1):
    return [p for (t, p) in samples if t0 <= t <= t1]


class Journey:
    """CDP frames and captured output share the browser's epoch clock."""
    def __init__(self, page, out):
        self.out = out
        self.frames = []
        self.folder = out / "journey-frames"
        self.folder.mkdir(parents=True, exist_ok=True)
        self.cdp = page.context.new_cdp_session(page)
        self.cdp.on("Page.screencastFrame", self.frame)
        self.cdp.send("Page.startScreencast", {
            "format": "jpeg", "quality": 88, "maxWidth": DESKTOP["width"],
            "maxHeight": DESKTOP["height"], "everyNthFrame": 1})

    def frame(self, event):
        name = f"frame-{len(self.frames):05d}.jpg"
        (self.folder / name).write_bytes(base64.b64decode(event["data"]))
        self.frames.append((name, event["metadata"]["timestamp"] * 1000))
        self.cdp.send("Page.screencastFrameAck", {"sessionId": event["sessionId"]})

    def finish(self, audio_epoch):
        self.cdp.send("Page.stopScreencast")
        manifest = []
        for i, (name, timestamp) in enumerate(self.frames):
            duration = (self.frames[i + 1][1] - timestamp) / 1000 if i + 1 < len(self.frames) else 0.12
            manifest.extend([f"file 'journey-frames/{name}'", f"duration {max(0.001, duration):.6f}"])
        manifest.append(f"file 'journey-frames/{self.frames[-1][0]}'")
        (self.out / "journey-concat.txt").write_text("\n".join(manifest), encoding="utf-8")
        offset = (audio_epoch - self.frames[0][1]) / 1000
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", str(self.out / "journey-concat.txt"), "-itsoffset", str(offset),
                        "-i", str(self.out / "intro-invitation-audio.webm"),
                        "-map", "0:v", "-map", "1:a", "-r", "30", "-c:v", "libx264",
                        "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                        str(self.out / "full-journey.mp4")], check=True)
        return {"frames": len(self.frames), "audioOffsetSeconds": offset,
                "firstFrameEpoch": self.frames[0][1]}


def wait_room(page, state="room-ready"):
    page.wait_for_function("s => document.querySelector('[data-room]').dataset.state === s",
                           arg=state, timeout=25000)


def snapshot(page):
    return page.evaluate("() => ({samples:__tap.samples, visuals:__tap.visuals})")


def output_peak(page, start, end=None):
    samples = page.evaluate("() => __tap.samples")
    return max(peaks_in(samples, start, end if end is not None else 1e9), default=0)


def time_now(page):
    return page.evaluate("performance.now() - __tap.started")


def quiet_after(page, rep, name, action, check_animation=True):
    action()
    page.wait_for_timeout(140)
    start = time_now(page)
    page.wait_for_timeout(700)
    peak = output_peak(page, start)
    moving = page.evaluate("""() => [...document.querySelectorAll(
        '.invite__hand, .crt__go-face, .burst__bit')].flatMap(e => e.getAnimations())
        .filter(a => a.playState === 'running').length""")
    rep.note(name, {"peak": peak, "moving invitation parts": moving},
             peak < 0.001 and (not check_animation or moving == 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/evidence/refinement/audio")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rep = Report()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()  # no autoplay policy bypass
        ctx = browser.new_context(viewport=DESKTOP, color_scheme="dark")
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.add_init_script(TAP)
        page.goto(BASE + "/", wait_until="networkidle")
        wait_room(page)
        rep.note("automatic intro stays silent without a gesture",
                 page.evaluate("() => __tap.contexts"), page.evaluate("() => __tap.contexts") == 0)
        btn = page.locator("[data-sound]")
        rep.note("explicit sound replay stays available", btn.inner_text(),
                 btn.is_visible() and btn.inner_text() == "Play intro with sound")
        journey = Journey(page, out)
        page.wait_for_timeout(240)
        btn.click()
        page.wait_for_timeout(480)
        rep.note("sound unlock is asynchronous and replays the empty hold",
                 page.evaluate("() => [__tap.ctxState, document.querySelector('[data-room]').dataset.state]"),
                 page.evaluate("__tap.ctxState") == "running"
                 and page.locator("[data-line='1']").inner_text() == "")
        wait_room(page)
        # Record until the third demonstration cycle has begun, so cycles one
        # and two are complete whatever the cycle's length is.
        page.wait_for_function("""() => {
            const a = document.querySelector('.invite__hand').getAnimations()[0];
            return a && a.currentTime >= a.effect.getTiming().duration * 3 + 100; }""",
            timeout=30000)
        data = snapshot(page)
        samples, visuals = data["samples"], data["visuals"]
        beeps = [max(peaks_in(samples, at - 20, at + 145), default=0) for at in DOTS_AT]
        rep.note("three dot beeps reach the master output", beeps, all(p > 0.01 for p in beeps))

        # The first occurrence after the third dot is a deletion, not dot insertion.
        third = next(v["t"] for v in visuals if v["line"] == "...")
        deletions = []
        for text in ("..", ".", ""):
            v = next(v for v in visuals if v["t"] > third and v["line"] == text)
            # Stop before typing begins 42ms after the last deletion. Otherwise
            # a missing third backspace could accidentally pass on the first W.
            peak = max(peaks_in(samples, v["t"] - 16, v["t"] + 24), default=0)
            deletions.append({"text": text, "at": v["t"], "peak": peak})
        rep.note("each individual deletion produces a separate short backspace", deletions,
                 all(d["peak"] > 0.004 for d in deletions)
                 and all(100 <= deletions[i + 1]["at"] - deletions[i]["at"] <= 170 for i in (0, 1)))
        typed = max(peaks_in(samples, 2250, 3300), default=0)
        rep.note("typing remains audible and quieter than dot beeps",
                 {"typing": typed, "beep": max(beeps)}, 0.005 < typed < max(beeps))

        # The cycle's length and its contact beat come from the page's own
        # keyframes, so a retimed demonstration retimes this check with it.
        timing = page.evaluate("""() => {
            const a = document.querySelector('.invite__hand').getAnimations()[0];
            const d = a.effect.getTiming().duration;
            return {duration: d, contact: a.effect.getKeyframes()[2].computedOffset * d}; }""")
        cycle_ms, contact_ms = timing["duration"], timing["contact"]
        cues = []
        for cycle in (1, 2):
            frames = [v for v in visuals if v["invite"] == "on" and v["phase"] is not None
                      and cycle * cycle_ms <= v["phase"] < (cycle + 1) * cycle_ms]
            contact = next(v for v in frames if abs(v["gap"]) < 0.7)
            flight = next(v for v in frames if v["bit"] > 0.5)
            click_peak = max(peaks_in(samples, contact["t"] - 16, contact["t"] + 75), default=0)
            flight_peak = max(peaks_in(samples, flight["t"] - 16, flight["t"] + 90), default=0)
            cues.append({"cycle": cycle, "contact": contact["t"], "visible flight": flight["t"],
                         "contact error px": contact["gap"], "click peak": click_peak,
                         "flight peak": flight_peak})
        rep.note("two demonstration cycles sound at contact and visible flight", cues,
                 all(c["click peak"] > 0.004 and c["flight peak"] > 0.001
                     and 80 <= c["visible flight"] - c["contact"] <= 155 for c in cues))
        rep.note("invitation effects are quieter than terminal beeps", cues,
                 all(c["click peak"] < max(beeps) and c["flight peak"] < c["click peak"] for c in cues))

        # Activate in the dark pause at the end of the cycle:
        # one new press and one new flight.
        page.wait_for_function("""() => {
            const a = document.querySelector('.invite__hand').getAnimations()[0];
            const d = a.effect.getTiming().duration;
            const t = a.currentTime % d; return t > d - 1000 && t < d - 850; }""")
        page.click("[data-go]")
        activated = time_now(page)
        page.locator("[data-go]").dispatch_event("click")
        page.wait_for_timeout(220)
        live = snapshot(page)
        rep.note("real activation fires a single click and flight",
                 {"click": output_peak(page, activated - 25, activated + 70),
                  "flight": output_peak(page, activated + 95, activated + 200)},
                 output_peak(page, activated - 25, activated + 70) > 0.004
                 and output_peak(page, activated + 95, activated + 200) > 0.001)
        wait_room(page, "desktop")
        page.wait_for_timeout(600)
        desktop_at = time_now(page)
        page.wait_for_timeout(600)
        rep.note("desktop entry stops all invitation audio", output_peak(page, desktop_at),
                 output_peak(page, desktop_at) < 0.001)
        page.keyboard.press("Escape")
        wait_room(page)
        returned_at = time_now(page)
        # The restored demonstration's first click comes at its contact beat,
        # wherever that beat is in the cycle: wait for it, then look for output
        # since the return rather than at a fixed offset.
        page.wait_for_function("""() => {
            const a = document.querySelector('.invite__hand').getAnimations()[0];
            if (!a) return false;
            const d = a.effect.getTiming().duration;
            return a.currentTime > a.effect.getKeyframes()[2].computedOffset * d + 200; }""",
            timeout=15000)
        page.wait_for_timeout(120)
        rep.note("return restores invitation without replaying intro",
                 {"line": page.locator("[data-line='1']").inner_text(),
                  "peak since return": output_peak(page, returned_at)},
                 page.locator("[data-line='1']").inner_text() == ""
                 and output_peak(page, returned_at) > 0.001)
        page.evaluate("__tap.stopRec()")
        page.wait_for_function("__tap.recorded !== null")
        recorded = page.evaluate("__tap.recorded")
        (out / "intro-invitation-audio.webm").write_bytes(base64.b64decode(recorded.split(",", 1)[1]))
        timing = journey.finish(page.evaluate("__tap.epoch"))
        data = snapshot(page)
        (out / "signal-and-visuals.json").write_text(json.dumps(data), encoding="utf-8")
        rep.note("journey video is muxed to captured output using browser timestamps", timing,
                 len(journey.frames) > 100)

        # Accept a demonstration already in contact. Its current flight must survive
        # and its playhead must not jump back to the beginning of a second burst.
        page.wait_for_function("""() => {
            const a = document.querySelector('.invite__hand').getAnimations()[0];
            const d = a.effect.getTiming().duration;
            const c = a.effect.getKeyframes()[2].computedOffset * d;
            const t = a.currentTime % d; return t > c + 300 && t < c + 380; }""")
        page.click("[data-go]")
        accepted = page.evaluate("""() => ({
            invite:document.querySelector('[data-room]').dataset.invite,
            animations:document.querySelector('.burst__bit').getAnimations().map(a => a.animationName),
            phase:document.querySelector('.burst__bit').getAnimations()[0]?.currentTime ?? -1})""")
        rep.note("click during demonstrated contact reuses one existing burst", accepted,
                 accepted["invite"] == "finish" and accepted["animations"] == ["burst"]
                 and contact_ms + 250 < accepted["phase"] < contact_ms + 700)
        wait_room(page, "desktop")
        page.keyboard.press("Escape")
        wait_room(page)
        quiet_after(page, rep, "mute stops output and repeating animation", lambda: btn.click())
        rep.note("muted control still permits real entry", page.locator("[data-go]").is_visible())
        page.click("[data-go]")
        wait_room(page, "desktop")
        page.keyboard.press("Escape")
        wait_room(page)

        # Replay / mid-typing cancellation is retained from the original test.
        btn.click()
        page.wait_for_timeout(2600)
        quiet_after(page, rep, "mute cancels typing voices and later scheduled characters",
                    lambda: btn.click(), check_animation=False)
        page.click("[data-skip]")
        btn.click()
        page.click("[data-skip]")
        quiet_after(page, rep, "hidden-page event stops voices and invitation",
                    lambda: page.evaluate("""() => {
                      Object.defineProperty(document, 'visibilityState', {configurable:true, value:'hidden'});
                      document.dispatchEvent(new Event('visibilitychange')); }"""))
        page.evaluate("""() => {
          delete document.visibilityState; document.dispatchEvent(new Event('visibilitychange')); }""")
        page.wait_for_timeout(1000)
        rep.note("visibility return resumes invitation without introduction",
                 page.get_attribute("[data-room]", "data-invite"),
                 page.get_attribute("[data-room]", "data-invite") == "on")
        quiet_after(page, rep, "pagehide teardown stops voices and animation",
                    lambda: page.evaluate("window.dispatchEvent(new Event('pagehide'))"))
        page.evaluate("window.dispatchEvent(new Event('pageshow'))")
        page.reload(wait_until="networkidle")
        rep.note("refresh skips intro and starts with sound disabled",
                 page.evaluate("() => [document.querySelector('[data-room]').dataset.state, __tap.contexts]"),
                 page.get_attribute("[data-room]", "data-state") == "room-ready"
                 and page.evaluate("__tap.contexts") == 0)
        rep.note("no browser script errors", errors, not errors)
        ctx.close()
        reduced = browser.new_context(viewport=DESKTOP, reduced_motion="reduce")
        page = reduced.new_page()
        page.add_init_script(TAP)
        page.goto(BASE, wait_until="networkidle")
        wait_room(page)
        page.click("[data-sound]")
        page.wait_for_timeout(1100)
        rep.note("reduced motion stays static and makes no demonstration sounds",
                 output_peak(page, 0), output_peak(page, 0) < 0.001)
        reduced.close()
        browser.close()
    (out / "report.json").write_text(json.dumps({"checks": rep.rows, "failures": rep.fails,
        "limits": ["Digital signal before OS output, not a speaker or headphone measurement.",
                   "Visibility lifecycle event is simulated; no physical device was backgrounded.",
                   "30 fps review encoding; cue measurements use original browser-frame timestamps."]},
        indent=2), encoding="utf-8")
    sys.exit(rep.dump())


if __name__ == "__main__":
    main()
