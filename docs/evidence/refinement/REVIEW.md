# Artwork and sound refinement — 2026-09-11

[Open the visual review and video](index.html) · [Preview](http://127.0.0.1:4321/)

## Starting point and preservation

The working tree was already dirty: 17 modified tracked files, untracked audio and
Blender-study tools, and an untracked evidence directory. No reset, checkout, commit,
skill installation or deployment was performed. One agent edited throughout.
The existing changes to skill records, site content and unrelated pages were preserved.
The user handoff, design/asset notes, saved evidence, current owners and their actual
dependencies were inspected. Fresh baseline checks passed: **61 room, 7 audio**.

The single camera, 650ms opening hold, dot beeps, asynchronous explicit sound replay,
master gain, cancellation, refresh skipping, vertical glove movement, external particle
layer, scanline stacking and landscape-phone button sizing were retained.

## Artwork review

The before crops were taken from the current working implementation, with the invitation
hidden, before the redraw. Both sets use the same 1440×900 viewport, 1× device scale,
2× artwork display scale and identical crop rectangles. No comparison image is stretched.

| Part | Before, dark / light | After, dark / light |
|---|---|---|
| Equipment together | [dark](before/equipment-dark.png) / [light](before/equipment-light.png) | [dark](after/equipment-dark.png) / [light](after/equipment-light.png) |
| CRT support | [dark](before/support-dark.png) / [light](before/support-light.png) | [dark](after/support-dark.png) / [light](after/support-light.png) |
| Keyboard | [dark](before/keyboard-dark.png) / [light](before/keyboard-light.png) | [dark](after/keyboard-dark.png) / [light](after/keyboard-light.png) |
| Mouse | [dark](before/mouse-dark.png) / [light](before/mouse-light.png) | [dark](after/mouse-dark.png) / [light](after/mouse-light.png) |

The former slab support is now a curved cradle with a short neck seated in a broad,
low pedestal. The top, rim, thickness and desk contact are visible. Keyboard rows now
contain individual oblique caps, staggered modifiers, a long spacebar and separate
navigation/numeric groups. The compact drawing retains four rows at readable density.
The mouse has a fuller palm, button seams, a wheel, a lower skirt and a contact shadow
under its rounded footprint. The equipment was inspected separately at native and 2×
sizes before integration, then reviewed in both themes on the page.

Reference photographs and the corrected Blender study informed forms; none was traced
or shipped. The study's unit-cube helper had halved boxes but not cylinders. Correcting
that scale made it usable with the already-installed Blender 5.1.1. Reference links and
provenance are in [ASSETS.md](../../ASSETS.md).

### Glove and layouts

[Isolated glove, light](after/hand-alone-light.png) / [dark](after/hand-alone-dark.png).
The short index sits next to three folded fingers, with the thumb on its other side.
The explicit contact anchor is `(7.5,24)` on a `22×24` grid; the palm is offset to the
right. The measured horizontal drift is **0.000px**, with no rotation. At the parked
pressed frame the tip meets the moving button face; its horizontal error is under 0.01px.

[Desktop dark](after/desktop-dark.png) / [light](after/desktop-light.png) ·
[Phone dark](after/phone-dark.png) / [light](after/phone-light.png) ·
[Landscape dark](after/landscape-dark.png) / [light](after/landscape-light.png).

[Raised phone glove, dark](after/hand-raised-phone-dark.png) /
[light](after/hand-raised-phone-light.png). The full raised glove fits all seven tested
viewports in both themes. Phone screenshots emulate touch; a touch activation is also
exercised by the room regression.

### Dimensions

Git's previous wide grid is **340×180**, not 340×270. The current **510×270** increases
both dimensions by 1.5×, giving 2.25× the pixels. This was a documentation error, not
a stretched asset. No canvas or screen rectangle changed during this refinement.

| Viewport | Native canvas | Displayed canvas | Button |
|---|---|---|---|
| 1440×900 | 510×270 | 1020×540 | 99×43 |
| 390×844 | 180×252 | 360×504 | 111×50 |
| 844×390 | 510×270 | 510×270 | 69×45 |

The old wide 3× display was also 1020×540. The old compact 120×168 at 3× was 360×504.
This equivalence applies at those scales, not every possible viewport threshold.
[Before measurements](before/dimensions.json) / [after measurements](after/dimensions.json).

## Sequence and playback

The existing dots arrive at 650/1050/1450ms. After the third dot's 400ms hold, they
become `..` at 1850ms, `.` at 1970ms and empty at 2090ms, with one backspace per removal.
Typing starts 42ms later. The pullback remains 1500ms. The ideal intro duration is
6952ms; its stale-intro cutoff includes 4000ms of scheduling allowance, totalling 10952ms.

Deletion frames, dark: [three](after/deletion-dark-3.png), [two](after/deletion-dark-2.png),
[one](after/deletion-dark-1.png), [empty](after/deletion-dark-0.png).
The same [light sequence](after/deletion-light-3.png) is included in the visual review.
These stills use a controlled browser clock; the room tests independently measure the
unmodified real-time sequence.

[Recorded journey with captured audio](audio/full-journey.mp4) ·
[Audio alone](audio/intro-invitation-audio.webm) · [Signal report](audio/report.json).

The recording covers explicit sound replay, intro and pullback, two complete invitation
cycles after settling, real activation, desktop entry, and return. Video comes from CDP
frames; audio comes from the master-output tap. Browser epoch timestamps align the two.
The encoded file is 1280×800, H.264 video at 30fps with AAC audio. Raw audio is WebM/Opus.
Visual review uses frames decoded from this recording across the journey, plus a denser
[contact/flight segment](contact-review.jpg). This is a recorded-frame review, not a claim of physical-device
or real-time perceptual playback testing.

CSS keyframes remain the invitation's clock: contact at 31% (620ms), first visible
flight at 37% (740ms). One animation-frame observer follows that playhead and drops
missed cues. The click is 24ms; flight noise is 210ms. Both use the original master and
voice cancellation. A real click during the demonstrated hold completes that existing
burst once. A new press outside the hold fires one new click and flight. Entry, mute,
visibility changes and teardown stop repeating effects. Return restores the invitation.

## Verification and limits

| Check | Result |
|---|---|
| Build, escaping/script policy, internal links | Pass; 68 internal references resolve |
| Room sequence and interaction | 62 checks, 0 failures, 0 console messages |
| Themes, dimensions, raised glove, controls | 74 checks, 0 failures, 0 console messages |
| Audio output and lifecycle | 22 checks, 0 failures |
| Page checks and axe-core 4.10.2 | No console, request, overflow, contrast or axe errors |

The page checker still lists eight small link targets on the unrelated inner pages
(wordmark and GitHub links). They were not changed as part of this focused refinement.

**Measured:** absolute digital sample peaks after the master, not just scheduled notes.
Dot beeps peak about 0.089, backspaces about 0.040, typing about 0.043; clicks and
whooshes are lower than the beeps, with the flight sound lower than the click. Exact
noise peaks vary by run and are saved in the signal report. Mute, desktop, hiding and
teardown checks measure zero output after settling. The third-backspace window ends
before the first typed character, so a missing deletion sound cannot pass on typing.
Live visual/audio timing measurements have approximately one browser-frame granularity.

**Listened to:** no perceptual listening pass was performed. This environment's digital
capture cannot establish how speakers/headphones sound, perceived loudness, timbre or
device latency. The included audio and video are ready for that listening check.
Visibility/page lifecycle events were simulated in Chromium; physical mobile devices,
Safari/iOS audio routing and OS backgrounding were not tested.

Installed design/review guidance informed the silhouette-first review, native-scale
comparisons and phone checks. Animation guidance informed the shared playhead and
cleanup; the existing CSS/Web Animations implementation was extended without adding GSAP.
Browser checks follow the installed webapp-testing workflow. Skill records were preserved.

Regenerate with the existing virtual environment:

```powershell
.venv/Scripts/python.exe tools/pixel_art.py --out src/assets/pixel
node build.mjs
.venv/Scripts/python.exe tools/capture_refinement.py --stage after
.venv/Scripts/python.exe tools/check_room.py --out artifacts/refinement-final/room
.venv/Scripts/python.exe tools/check_theme.py --out artifacts/refinement-final/theme
.venv/Scripts/python.exe tools/check_audio.py --out docs/evidence/refinement/audio
```

Preview remains at http://127.0.0.1:4321/. Work is uncommitted and not deployed.
