# One elevated viewpoint, rebuilt equipment — 2026-09-11, third pass

[Open the visual review](index.html) · [Preview](http://127.0.0.1:4321/) ·
[Second pass](../equipment/REVIEW.md) · [First pass](../refinement/REVIEW.md)

## Starting point and preservation

Taken over from the second pass with the working tree still dirty. Nothing was reset,
checked out, committed, installed or deployed. The introduction, its sounds, the
glove, the particles, the themes, desktop entry and return, and refresh skipping were
not edited: `src/scripts/room.js` changed only in the wide canvas constant (576×330),
`src/components/room.js` only in the `<img>` width/height attributes and a comment,
`src/styles/room.css` only in comments and the wall glow's horizontal position.

The instruction to point the mouse left is superseded: the mouse now faces the
monitor. No screenshot file accompanied this request; the "latest screenshot" was
taken to be the second pass's after-captures, which the `before/` set here reproduces
from the working site before any asset changed.

## What was built

**One projection.** `tools/pixel_art_scene.py` now lays the scene out in desk
coordinates (x right, y up from the tabletop, z away from the viewer) and draws every
object through a single `View`: `(x - z/6, y0 - y - z/2)`. The viewer stands in front
of the desk and slightly above it - depth foreshortened to half (about 30°), receding
up the picture, with a modest turn of one pixel left per six units of depth (about
10° of yaw). Front faces stay true rectangles; tops are visible parallelograms; left
sides are thin slivers. Physical positions and sizes were set first (a 455mm keyboard
at 198px sets 0.435 px/mm; a 14-inch CRT 132×118×138; tower 66×140×138; mouse
27×50×16; desk 522×250 with a 12-unit top) and the drawing follows from them.

**Mouse.** A height field over a pebble footprint, rasterised far to near and closed
by its rear wall. The rounded palm dome is nearest; the two button surfaces, their
narrow division and a small wheel are at the far end; the cable leaves the nose and
lies on the desk to the tower. The first draft's front sloped as steeply as a real
mouse and, from this elevation, collapsed to two rows; the profile now stays high
toward the nose so the buttons read. Its long axis runs bottom-to-top on screen.

**Monitor and support.** The previous strip of background under the casing came from
a housing that stood too far back and a dark joint band drawn on rows the chin then
hid. The support is now built in assembly order: the casing's underside in shadow (the
mounting area), a truncated-cone housing seated into it, and a broad low plate with
rounded corners on the desk. The housing sits behind the bezel block, under its depth,
so the chin hides its top rows; the joint is the dark band that emerges beneath the
bezel outline, and the socket shows as a shadow crescent in front of the foot. The
stand is one outlined layer, so no silhouette is separated from another by air. The
casing itself is a bezel block over a narrower, lower tube housing with vents.

**Keyboard.** A full-size ANSI layout in key units (`ANSI_ROWS`), placed on the deck
with one x unit and one z unit and projected: function row set half a unit back,
staggered rows with Backspace 2u, Tab 1.5u, Caps 1.75u, Enter 2.25u, Shifts 2.25u and
2.75u, 1.25u bottom modifiers and a 6.25u spacebar; the navigation cluster and the
inverted-T arrows from 15.5u; the keypad from 19u with tall + and Enter. Each cap is a
lit top three rows deep over a one-row front, in a dark well with a one-unit gap. The
deck's tilt adds one row per key row to the depth's four, so the pitch is five rows.

**Desk.** The finite table is kept, drawn from the same projection: top, front
thickness, the thin left end face, and four square legs at the corners hanging from
the underside (drawn first, so the top hides their tops). Every footprint and shadow
is on the top plane.

**Canvas.** The wide grid grew from 510×270 to 576×330: the visible tops and the deep
tabletop need rows, and a desk with both ends in frame needs columns. At 2× it is
1152×660 and still fits 1280×720; at 3× it fits 1920×1080; short landscape phones
stay at 1×. The compact grid is unchanged at 180×252 and uses the same projection at
a smaller equipment scale. The glass stayed a true rectangle, so the live screen
mapping needed no new transform: the build regenerated the rectangle (185,107 wide;
18,66 compact) and the text, button, glove and particle origin followed it.

## Visual findings

Inspected at 1×, 2× and 4-8× nearest-neighbour while drawing, then on the page in
both themes at 1440×900, 390×844 and 844×390.

- The mouse can be read as used facing the monitor: palm nearest, buttons and wheel at
  the far end, cable to the tower. Its button area is 7-8 rows deep at this elevation,
  which is enough at 2× and the physical limit of the angle.
- There is no background at the monitor's mounting joint: the housing's dark band
  meets the bezel outline directly, and the plate's front edge meets the desk.
- The keyboard matches the real arrangement: separate function row, staggered rows,
  correct relative Backspace/Enter/Shift, long spacebar, navigation cluster, inverted-T
  arrows, keypad with tall keys. No lettering; shapes and grouping carry it.
- All objects share the desk's projection; front faces are rectangles, tops recede at
  the same slope, and the legs, plate, housing and casing meet their supports.
- Outlines stay white on dark and black on light, one unit thick.
- Still open, by eye: the tower's top is large from this elevation, which is correct
  for a 30° view of a 320mm-deep case but heavier than the flatter references; at the
  landscape-phone 1× scale the mouse reads as a shape, as before.

## Verification

| Check | Result |
|---|---|
| `node build.mjs` | Builds; wide framing 576×330 with an empty desk band, narrow keeps its band |
| `tools/check_escaping.mjs`, `tools/check_links.mjs` | Pass |
| `tools/check_scene.py` | 14 checks, 0 failures: identical theme geometry, overlay on the glass in both framings, no stray click targets |
| `tools/check_room.py` | 62 checks, 0 failures, 0 console messages (intro timing, deletion, pullback, invitation, burst, entry, return, skip, touch, keyboard, reduced motion, refresh) |
| `tools/check_theme.py` | 74 checks, 0 failures, 0 console messages (7 viewports, both themes, whole-number scale, glass and key usable) |
| `tools/check_audio.py` | 22 checks, 0 failures (dot beeps, backspaces, typing, click and whoosh measured at the master; silence after mute, entry, hiding and teardown) |
| `tools/check_pages.py` | 0 problems: no console messages, failed requests, overflow, contrast or axe errors on the five pages at two widths. The same eight pre-existing small link targets on the unrelated inner pages (wordmark and GitHub links) are listed and were not changed |

Browser checks were run one at a time, because the room and audio checks measure
real-time sequences.

**Limits.** No perceptual listening pass and no physical device. Visual judgements are
mine from screenshots and enlarged crops. The layout uses the standard ANSI 104-key
dimensions rather than a photograph of one specific keyboard.

Regenerate:

```powershell
.venv/Scripts/python.exe tools/pixel_art.py --out src/assets/pixel
node build.mjs
.venv/Scripts/python.exe tools/capture_refinement.py --stage after --out docs/evidence/viewpoint
.venv/Scripts/python.exe tools/check_scene.py --out artifacts/viewpoint/scene
.venv/Scripts/python.exe tools/check_room.py --out artifacts/viewpoint/room
.venv/Scripts/python.exe tools/check_theme.py --out artifacts/viewpoint/theme
.venv/Scripts/python.exe tools/check_audio.py --out artifacts/viewpoint/audio
.venv/Scripts/python.exe tools/check_pages.py --out artifacts/viewpoint/pages
```

Preview remains at http://127.0.0.1:4321/. Work is uncommitted and not deployed.
