# A shorter monitor, and lamps around the computer — 2026-09-11, fourth pass

[Open the visual review](index.html) · [Preview](http://127.0.0.1:4321/) ·
[Third pass](../viewpoint/REVIEW.md)

## Starting point and preservation

Taken over from the committed third pass (`7ede245`) with a clean tree. Nothing was
reset, checked out or deployed. The dot/deletion/typing sequence, sounds, replay,
shared-camera move, key, glove, particles, themes and desktop interaction were not
edited: `src/scripts/room.js` gained only the two lines that make the labels inert
whenever the room is not at rest. No screenshot file accompanied the request; the
`before/` set here was captured from the working site before any change.

Only the frontend-design skill exists in this repository; no game-animation or game-ui
skill is installed, so none was read.

## 1. The monitor

The tube housing behind the bezel block was a 108-deep box. It is now 84 deep (22%
less) and TAPERS toward the back - 12 units a side and 6 on top - so the top and side
are trapezoids behind the wider front casing. The bezel block, the glass (185,107
108×81), the support and the joint are untouched; the shortening is in the geometry,
not a resample. The tower, which showed the same problem from this elevation, is 114
deep instead of 138. The compact framing follows (48-deep housing, 70-deep tower).
The scene check confirms the overlay still lands on the glass and both themes share
identical geometry.

## 2. The lamps

Four labels on the wall, on a broad arch: GitHub at the lower left, About Me above it,
Projects I Have Done So Far (two lines) at the top, Other Social Medias down the right
above the sound control. They are links to the verified GitHub account, `/about/`,
`/projects/` and `/contact/` (no other account is confirmed, so the social item goes to
Contact). Each has an original 16×16 pixel mark - a repository card with code marks, a
bust, a folder, two joined message bubbles - drawn with the design's one-unit outline
(white on dark, black on light) around an accent interior in cyan, pink, warm yellow
and mint, and Silkscreen lettering at a whole multiple of its 8px design size. No
cards, no pills: an icon, a heading, and when lit, an ellipse of light behind them.

Positions are fractions of the artwork's displayed box (`--art-w`, `--art-h` from the
generated variables), so they follow the framing and the scale rather than a
screenshot, with floors so the top of the arch stays inside a short window. On phones
the arch folds into the wall above the machine in the same reading order: Projects at
the top, About Me and Other Social Medias either side, GitHub at the lower left just
above the monitor; the machine is not shrunk.

## 3. Synchronization

The lamps have no timer. Their keyframes run on the same 2000ms duration as the hand,
the key and the burst and start on the same style change (`data-invite`), so contact
at 31% is the same frame for all four effects: `--lit` (a registered custom property)
goes 0 → 1 between 31% and 33% (40ms), holds to 43% (200ms), and returns to 0 by 53%
(200ms). A real activation runs a one-shot version from the press. A click that lands
during the held press finishes the current cycle once, as the other effects do. Under
reduced motion there is no loop and the labels stand at their readable resting state.

Hovering or keyboard-focusing a lamp keeps it fully lit (an important declaration
outranks the running animation). The links keep stable hit areas throughout: only
colour, icon fill and the light patch change.

## Visual findings

Judged on the page at 1440×900 and 390×844 in both themes, and in the crops.

- The monitor no longer dominates its silhouette; the housing reads as tapering behind
  the bezel and the top vents follow the taper. The joint under the chin is unchanged
  and shows no gap.
- At rest the labels are quiet but readable; at the press the four patches of light
  come up together and fade back while the burst is still leaving the glass. Nothing
  moves, and nothing flashes the whole screen.
- The icons read at 32px: the card's `< >` marks are the smallest detail and read as
  code; the bust, folder and bubbles are unambiguous.
- Still open, by eye: on very short phones (under about 700px tall) GitHub sits within a
  few pixels of the monitor's top edge; and the burst pieces do cross the Projects label
  briefly, which the brief accepted as legible through the burst.

## Verification

| Check | Result |
|---|---|
| `node build.mjs`, `tools/check_escaping.mjs`, `tools/check_links.mjs` | Builds; escaping policy holds for the new links (every href goes through `safeUrl`); all internal links resolve |
| `tools/check_scene.py` | 14 checks, 0 failures: identical theme geometry, overlay on the glass in both framings, no stray click targets |
| `tools/check_lamps.py` (new) | 15 checks, 0 failures. Shared start time and 2000ms duration for all four lamps; press→light offset 0ms in three live cycles at a 34ms frame; cadence 2000/2000; hold 200/200/200ms; dark again 433ms after the press; hover and Tab-focus keep a lamp lit with a visible ring; resting text 9.6:1 on the wall; a real click lights them within 41ms; on the desktop they are inert, hidden and never focused over ten Tabs; usable again on return; reduced motion runs no lamp animation; on desktop and phone all four sit inside the window, at least 44px, without overlapping |
| `tools/check_room.py` | 62 checks, 0 failures, 0 console messages (intro timing, deletion, pullback, invitation, burst, entry, return, skip, touch, keyboard - the first Tab still reaches the key - reduced motion, refresh) |
| `tools/check_theme.py` | 74 checks, 0 failures, 0 console messages (7 viewports, both themes, whole-number scale, no overflow with the lamps present) |
| `tools/check_audio.py` | 22 checks, 0 failures (dot beeps, backspaces, typing, click and whoosh measured at the master; silence after mute, entry, hiding and teardown) |
| `tools/check_pages.py` | 0 problems: no console messages, failed requests, overflow, contrast or axe errors on the five pages at two widths; the lamps' resting text is included in the contrast pass and none of them is a small target. The same eight pre-existing small link targets on the inner pages remain listed. The checker's colour parser was extended to read the `color(srgb …)` form Chromium reports for `color-mix()` results - it crashed on it before - with the contrast arithmetic unchanged |

`tools/check_lamps.py` measures, in real time with a frame callback, the frame the key
face starts down and the frame the lamps' `--lit` starts up, over three live cycles;
the shared animation start time and duration; the 200ms hold and the return to dark;
a real activation; hover and focus; the resting contrast; that no lamp can take focus
on the desktop; and reduced motion. It also writes the rest/peak/faded captures and
three peaks taken from live cycles.

Browser checks were run one at a time, because the room and audio checks measure
real-time sequences.

**Limits.** The browser here renders at about 30 frames per second, so "the same
frame" means within 34ms; a 60Hz display halves that. No perceptual listening pass and
no physical phone. Visual judgements are mine from screenshots and crops.

Preview remains at http://127.0.0.1:4321/. Work is uncommitted and not deployed.
