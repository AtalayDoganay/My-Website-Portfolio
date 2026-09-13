# A quick click, a slow fade, and a wider arch on a dark wall — 2026-09-12, sixth pass

[Open the visual review](index.html) · [Preview](http://127.0.0.1:4321/) ·
[Fifth pass](../hold/REVIEW.md)

## Starting point and preservation

Taken over from the uncommitted fifth pass and its same-day corrections, on a dirty
tree. Nothing was reset, checked out or deployed. The `before/` set was captured from
that build with `tools/capture_refinement.py --stage before` before any change. The
screenshot that prompted this pass (`Screenshot 2026-09-12 141315.png`, a 1840×869
capture of a window about 1472×695 CSS px wide, where the artwork renders at 1x) showed
the cyan halo flooding the wall behind the monitor, the five links ringed tightly around
a small machine, and the whole upper wall empty.

Untouched: the equipment artwork and its generator, the opening (dots, deletion, typing,
sounds, replay, refresh skipping), the camera moves, the themes, the desktop and its
links. Changed: one span removed from the room component; the Social heading given two
lines in the data; the timing constant, the focus cutoff, the real-click acceptance
window and the manual menu in `src/scripts/room.js`; the timeline, the lamps' size,
positions and light in `src/styles/room.css`; the lamp and room checks.

## 1. The halo is gone

`.room__glow` is removed from the markup and from both framings in the stylesheet. The
wall behind the machine is the navy ground with its grain; only the glass is lit
(`data-hot` still switches the screen's own lit background). The five patches of light
are small ellipses inside each group's own box (inset 4% and 8%, 26% of the accent on
dark, 72% warm white on light), and each group - icon, heading and patch - fades as a
whole because its opacity follows `--lit`, so five of them never merge into a wash and
nothing is left at the end of a fade, not even dim lettering.

## 2. One timeline, named beats

| Beat | Time in the 3600ms cycle | Keyframe |
|---|---|---|
| approach, straight down | 0–540ms | 0–15% (anticipation to 7.5%) |
| contact: key down, click, burst, lamps light in 50ms | 540ms | 15% |
| press, fingertip on the depressed key | 540–640ms (100ms) | 15–17.78% |
| lift; the key is back up by 660ms | 640–790ms (150ms) | 17.78–21.94% |
| fade to nothing, starting as the finger lifts | 640–2540ms (1900ms) | 17.78–70.56% |
| pointer refused from half brightness | 1590ms | 44.18% |
| hidden | 2540ms | 70.6% |
| dark, then the next approach | 2540–3600ms + 540ms | 70.6–100% |
| burst in flight | 540–1598ms | 15–44.4% |

The hand, the key, the burst and the lamps run keyframes of one duration that start on
one state change. The script reads contact from the hand keyframes, the first visible
flight from the burst keyframes and the pointer cutoff from the lamp keyframes
(`lampCutoff`), so the click, the whoosh and the focus hand-off follow the rendered
animation and nothing is timed separately. The checks read the same keyframes. No trace
of the two-second hold remains in the stylesheet, the script or the checks.

A real click, tap, Enter or Space still enters the desktop as before. When it arrives
while the demonstrated burst is still in flight (contact to 1598ms) it accepts that
press and lets the one burst finish; otherwise it fires its own single press and burst.

## 3. Larger, and spread across the wall

Icons are 48px and the lettering 24px on desktop-class windows, from 32px and 16px.
That is 50% rather than the suggested 25–35%: Silkscreen is an 8px face and the icons
are 16-cell marks, both crisp only at whole multiples, and the step above 2× is 3× -
2.5× would blur every edge. The padding (18px by 24px) is the hit area, with nothing
drawn in it; there are no cards. Phones keep the 2× sizes with more padding, and every
group measures 44px or more in both dimensions.

The arch is laid out on the wall rather than only on the artwork. The crown and the two
upper links take their height from the free wall above the artwork and their spread from
the window's width (17%, 50% and 83%, with rem floors and ceilings that keep the whole
icon and heading inside any window and off the theme switch); GitHub and Degrees sit
lower, beside the desk, measured from the artwork so they never land on the machine. In
the laptop-shaped window from the screenshot the five now span the empty wall instead of
ringing the small machine; at 1440×900 they sit further out and higher than before, and
the two right-hand links are well apart. "Other Social Medias" wraps to two lines.
Phones fold the five into three rows using the whole wall above the machine; Social
takes two lines and Degrees three. One layout bug surfaced and was fixed on the way: an
absolutely positioned group with only a left edge shrinks to the room left of the window
edge and wrapped early, so every group now has `width: max-content`.

## 4. Darkness and interaction

Between clicks the groups are `visibility: hidden` with opacity 0, so nothing can hover,
click, tap, focus or read them; their positions stay reserved. A link can be activated
while it is at half brightness or more; from the cutoff it refuses the pointer while
still faintly visible, so there is never an invisible clickable area. A link that has
keyboard focus at the cutoff hands it to the "Show links" control. That control shows all
five steadily until closed and, while it is open, the demonstration rests: the glove
raised, the key up, no burst, no cues (the stylesheet removes the animations and the
script drops its observer, re-binding when the menu closes). Escape closes it and returns
focus to it. Under reduced motion the control is the only reveal. The desktop window
still lists the same five destinations.

## Visual findings

Judged in the captures at 1440×900, 1472×695 and 390×844 in both themes.

- Dark rest: a flat dark wall, the lit glass, nothing else. Contact: the key down, the
  five coming up. Contact + 400ms: the finger up, the five bright, the burst crossing the
  room around the monitor and tower only. Mid-fade: half brightness, the burst gone.
  Hidden: nothing.
- The 48px marks read cleanly: the Invertocat, the bust, the folder, the bubbles, the
  diploma. The patches are a soft halo hugging each group.
- In the light theme the patches are quiet by design; the lit lettering carries the
  reveal.
- On the phone the crown sits 6px from the top edge, which is tight but inside, and on
  very short phones the rows still crowd the monitor - unchanged from the previous pass,
  since the machine may not shrink.

## Verification

| Check | Result |
|---|---|
| `node build.mjs`, `tools/check_escaping.mjs`, `tools/check_links.mjs` | Builds; escaping holds; all internal links and fragments resolve |
| `tools/check_lamps.py` (rewritten for the click) | 32 checks, 0 failures. Beats read from the keyframes: contact 540, press 100, cutoff 1590, visible span 2001ms. Three consecutive live cycles at a 3600ms cadence: press→light offset 0ms in each; the key down 100/100/100ms; full light 133/134/134ms; fade 1700ms ×3 (lit 0.95 to 0.05); visible 1983/1984/1984ms; hidden afterwards in all three; 1616ms of darkness before each next press; the pointer taken only at 0.50 light or more (250 frames) and refused on 164 faint visible frames; no animation or interval accumulates. Dark: hover reveals nothing, a click goes nowhere, Tab never lands. Tail of the fade: faintly visible, no pointer. Lit: visible at full light under the pointer, Tab reaches GitHub with a ring, clicking About navigates. Focus on a lamp hands to the reveal control at the cutoff. The control: five steady, the hand, key and burst animations gone, the glove raised, the key up, the burst dark; Escape closes, returns focus, hides the lamps and restarts the cycle. Activation in the dark phase lights them within 120ms; the desktop leaves them inert and lists five links. Reduced motion as before. No halo element and no radial gradient on the wall. Desktop, laptop and phone, both themes: 48/24px (32/16 on the phone), inside the window, 44px+, 24px+ apart (10px+ on the phone), clear of the machine's boxes, the glass and the controls, every patch inside its group's box |
| `tools/check_room.py` (parks at contact + 60ms for the fingertip) | 62 checks, 0 failures, 0 console messages |
| `tools/check_theme.py` | 74 checks, 0 failures, 0 console messages |
| `tools/check_audio.py` (reads the keyframes; unchanged) | 22 checks, 0 failures: one click and one whoosh per demonstrated cycle, a real activation in the dark pause, a click during the burst's flight reusing the one burst |
| `tools/check_pages.py` | 0 problems |
| `tools/check_scene.py` | 0 failures |

**Expectations that intentionally changed.** The lamp check now measures a ~100ms press,
a ~1.7s measured fade, a ~2s visible span, a second or more of darkness, the pointer
cutoff at half light, the resting demonstration under the manual menu, the halo's
absence, the larger sizes, the spacing, the machine clearance, and a laptop-shaped
viewport, over three live cycles. The room check parks the fingertip test 60ms after
contact instead of 240ms, because the press is 100ms long. The real-click acceptance
window in the script runs to the end of the burst's flight instead of the end of the
hold.

**Limits.** Frames here were 17–50ms, which bounds "the same frame". No perceptual
listening pass and no physical phone. The machine's boxes used for clearance are
measured fractions of the artwork, recorded in the check. Visual judgements are mine
from the captures.

Preview remains at http://127.0.0.1:4321/. Work is uncommitted and not deployed.
