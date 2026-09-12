# Equipment artwork refinement — 2026-09-11, second pass

[Open the visual review](index.html) · [Preview](http://127.0.0.1:4321/) ·
[Previous pass](../refinement/REVIEW.md)

## Starting point and preservation

Taken over from the previous pass with the working tree still dirty (17 modified
tracked files, untracked audio/Blender/capture tools and evidence). Nothing was reset,
checked out, committed, installed or deployed. The previous pass's functional work is
untouched: individual dot deletion with backspace sounds, synchronized click/whoosh,
the offset pointing glove with vertical-only travel, explicit sound replay, mute,
refresh skipping, reduced motion, desktop entry and return. `src/scripts/room.js`,
`src/components/room.js`, the audio code and the invitation CSS were not edited.

What changed: `tools/pixel_art_scene.py` (the drawing), the four machine PNGs and
`pixel.json` it generates, `build.mjs` (accepts a framing with no desk band),
`src/styles/room.css` (a comment), `tools/check_room.py` (see verification),
`tools/capture_refinement.py` (wider crop rectangles, phone crops), and the notes in
`docs/ASSETS.md` and `docs/DESIGN-NOTES.md`.

## References

Four of the five described attachments were available and were opened and inspected:
the beige CRT/tower/keyboard/mouse photograph (image 2), the dark pixel-art setup on a
blue mousepad (image 3), the beige pixel-art tower and monitor (image 4) and the pink
low-poly 3D CRT on a desk (image 5). **Image 1, the "current website" screenshot, was
not among the four files supplied.** The `before/` captures of the working site stand
in for it; they were taken before any asset changed.

Nothing was imported from the references: no logo, wallpaper, screen text, watermark,
plant or terminal styling, and no pixels were copied. The 3D reference set the
construction target for the support; the photograph set equipment proportions and key
groups; the two pixel pieces set silhouette clarity and warm plastic shading. The
existing Blender study (`tools/study_desk.py`) was inspected and not extended: it
models the support as stacked cylinders on a box, which is the construction this pass
moves away from, and the references gave the target directly.

## Artwork review (visual findings)

Before/after crops share viewports (1440×900 desktop, 390×844 phone, 844×390
landscape), a 2× display scale and identical crop rectangles in artwork pixels. The
review page shows close-ups at a further 2× nearest-neighbour. Judged by eye at 1×, 2×
and 4-8× during drawing, then on the page in both themes.

**Mouse.** Redrawn, not rotated: two profile curves (height and plan width along the
length) rasterised in three passes - far side, top strip, near side. Its length runs
left to right; the low nose and the cable are on the left toward the tower; the rounded
rear is on the right; the near side shows the shell's height and curve; the top shows
the button split along the crest, a wheel near the nose and one seam before the palm.
One continuous shell, no plate or patch, no large flat highlight. The nose was raised
after the first draft read as a wedge. Single-pixel holes left by the line sampling
were ringed white by the outline pass; a hole-filling step now precedes it. The compact
mouse keeps the wheel and the palm seam and drops the crest line, which was noise at
26px. Clearance to the keyboard's right diagonal is about 19px; the cable leaves the
nose, lies on the tabletop and enters the tower's front.

**Support.** The pinched neck and broad plate are gone. Under the casing: two dark rows
of joint, a housing whose half-width follows a quarter ellipse (it bellies out under
the joint and runs down to a rounded foot), a shaded socket, and a low plate that
recedes on the 2:1 step with a visible top, a catch-light and a three-row front edge
meeting the desk. Its top rows sit behind the casing's bottom edge, so it is partly
concealed. The casing gained four rows below the chin (wide and compact) so the support
stays short; the glass rectangle is unchanged (99,31 108×81 and 30,23 96×72) and
`build.mjs` regenerated the same overlay variables. A diagonal sheen line on the first
draft read as a crack and was removed; the plate was narrowed from 96 to 84px.

**Desk.** The wide framing now draws a finite freestanding desk: front edge x=140-500,
the 2:1 step back to y=150, a left end whose thickness shows as a parallelogram,
and four straight square legs (front face plus a darker left face). The back legs are
drawn first and the tabletop over them, so the back-left one hangs below the end face
and the back-right one emerges under the front edge. Legs run off the bottom of the
frame, where the page bottom-aligns the artwork; the room shows around and beneath the
top. The CSS band that used to continue the tabletop to the window edges is empty for
this framing (`--desk-band: none`). The narrow framing keeps its tabletop running past
the phone's edges and its band, as the brief allows; outer legs and ends leave the
viewport there, and the monitor is not shrunk. Every object still sits on the same
tabletop plane at the same contact rows (tower 162, monitor base 164, keyboard 169-201,
mouse 199), with contact shadows and cast shadows on that surface.

**Keyboard.** Layout retained: staggered rows, wide modifiers, the long spacebar, the
function row and the navigation/numeric groups (wide), four rows (compact). Each cap
is now a flat lit top - three rows wide, two compact - stepped one pixel on the 2:1
line over a one-row front, in the dark wells with a clear gap; the per-cap 6px skew
that produced the diagonal-scratch pattern is gone. Recession is carried by the rows.

**Both themes.** Same geometry, zero alpha mismatches (scene check). White outlines on
dark, black on light, one unit thick, on the desk, legs, support and mouse alike.

**Still open, by eye.** At the landscape-phone 1× scale the mouse is 48×16 device
pixels and reads as a shape rather than a mouse; the button and label are unchanged
there. The back-right leg appearing below the front edge is geometrically correct for
this projection but is the least self-explanatory part of the desk.

## Verification (automated results)

| Check | Result |
|---|---|
| `node build.mjs` | Builds; wide framing emits an empty desk band, narrow keeps its 68-row band |
| `tools/check_escaping.mjs`, `tools/check_links.mjs` | Pass; all internal links and fragments resolve |
| `tools/check_scene.py` | 14 checks, 0 failures: identical theme geometry, overlay on the glass in both framings, no stray click targets |
| `tools/check_theme.py` | 74 checks, 0 failures, 0 console messages (7 viewports, both themes, whole-number scale) |
| `tools/check_room.py` | See below |
| `tools/check_audio.py` | See below |
| `tools/check_pages.py` | See below |

**Room check.** The first run gave 62 checks, 1 failure: "E: the burst is still on
screen as entry begins" with `showing: 0`. Root cause, in the check rather than the
page: its park helper pauses the hand, button and burst animations at 700ms (an
invisible burst frame, held by the 31% step keyframe until 37%), but its resume step
restarted only the hand and button. A click during the held press rewinds the burst to
the current phase without unpausing it, so the result depended on the click landing
more than 40ms after the hand resumed. The previous pass's saved report shows the same
check passing with `showing: 10`, which is that race falling the other way. The resume
step now mirrors the park selector (`RESUME` in `tools/check_room.py`); no page code
changed. Results of the re-runs are recorded in the table below.

| Run | Result |
|---|---|
| Room, run 1 (original check) | 62 checks, 1 failure (the race above), 0 console messages |
| Room, run 2 (original check, repeat) | 62 checks, 0 failures, 0 console messages - the same check passed, so it is a race |
| Room, run 3 (resume step fixed) | 62 checks, 0 failures, 0 console messages |
| Audio output and lifecycle | 22 checks, 0 failures (dot beeps, backspaces, typing, click and whoosh measured at the master; silence after mute, entry, hiding and teardown) |
| Page checks and axe-core | 0 problems: no console messages, failed requests, overflow, contrast or axe errors on the five pages at two widths. The pre-existing small link targets on the unrelated inner pages (wordmark and GitHub links) are still listed and were not changed by this pass |

Browser checks were run one at a time, because the room and audio checks measure
real-time sequences.

**Limits.** No perceptual listening pass and no physical device; the audio check
measures digital output at the master, as before. Visual judgements are mine from
screenshots and enlarged crops, not a second reviewer's. The reference images are not
in the repository, so the provenance note in `docs/ASSETS.md` describes them rather
than linking them.

Regenerate:

```powershell
.venv/Scripts/python.exe tools/pixel_art.py --out src/assets/pixel
node build.mjs
.venv/Scripts/python.exe tools/capture_refinement.py --stage after --out docs/evidence/equipment
.venv/Scripts/python.exe tools/check_scene.py --out artifacts/equipment/scene
.venv/Scripts/python.exe tools/check_room.py --out artifacts/equipment/room
.venv/Scripts/python.exe tools/check_theme.py --out artifacts/equipment/theme
.venv/Scripts/python.exe tools/check_audio.py --out artifacts/equipment/audio
.venv/Scripts/python.exe tools/check_pages.py --out artifacts/equipment/pages
```

Preview remains at http://127.0.0.1:4321/. Work is uncommitted and not deployed.
