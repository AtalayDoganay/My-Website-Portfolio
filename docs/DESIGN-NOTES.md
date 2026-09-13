# Design notes

## Artwork and sound refinement — 2026-09-11

The current implementation and review evidence are documented in
[the refinement report](evidence/refinement/REVIEW.md). It includes same-scale
before/after crops, the isolated glove, deletion frames, and a recorded journey.
The existing uncommitted implementation was the starting point: its camera,
replay/unlock, session skipping, external effects layer and responsive controls
were retained.

The glove now has a short index on the thumb side of the palm, three folded
fingers beside it, and an explicit `(7.5, 24)` fingertip anchor on a `22×24` grid.
Its cream fabric, shaded folds and violet cuff distinguish it from bare skin.
Only vertical translation animates. The whole raised silhouette fits the glass
in both themes at all seven tested viewport sizes.

**A quick click and a slow fade, 2026-09-12 (sixth pass).** The wall halo behind the
machine (`.room__glow`) is gone: the wall is the navy ground and its grain, and only the
screen glows. The demonstration is a normal click on a 3600ms cycle: contact at 540ms, the
key down for 100ms, the finger up over 150ms, the five links lit in 50ms at contact and
fading to nothing over the 1900ms after the finger lifts, then about a second of darkness
plus the next approach. Each group fades as a whole (its opacity follows `--lit`), its patch
of light sits inside its own box, and it refuses the pointer from half brightness - the
script reads that cutoff from the lamp keyframes to hand focus back. Icons are 48px and the
lettering 24px on desktop-class windows (three times the 8px face; two and a half would
blur the pixels), with the padding as the hit area; phones keep the 2x sizes. The arch is
laid out on the wall: the crown and the two upper links take their height from the free
wall above the artwork and their spread from the window (17%, 50%, 83% with rem floors),
GitHub and Degrees sit lower beside the desk, measured from the artwork. A laptop-shaped
window (1472x695, artwork at 1x) is now a checked viewport. "Show links" rests the
demonstration while open. See `docs/evidence/click/REVIEW.md`.

**Press and hold, 2026-09-11 (fifth pass).** The demonstration is now a press AND
HOLD on a 4600ms cycle: the glove comes straight down, the key depresses and the click
sounds at contact (460ms), the burst and whoosh fire once, five lamps on the wall light
in 50ms and stay fully lit while the glove keeps the key down for two seconds, then
fade over 300ms as it lifts, followed by a clearly dark pause. Between presses the
lamps are gone entirely - `visibility: hidden`, so nothing can hover, click, tap, focus
or read them, and their positions stay reserved so the reveal moves nothing. Five
lamps now: GitHub (the Invertocat, see ASSETS.md) at the far lower left, About Me
upper left, Projects at the crown, Other Social Medias upper right, and Degrees,
Certificates & Skills lower on the right, linking to a credentials section of the
About page that lists only the confirmed degrees. A "Show links" control beside the
sound control shows the lamps steadily until closed (Escape closes it); focus on a lamp
returns to that control as the fade begins; under reduced motion the control is the
only reveal. The desktop window lists the same five destinations. See
`docs/evidence/hold/REVIEW.md`.

**Corrections, 2026-09-12.** The lit hold is exactly 2000ms: lit from 11.1% to 54.6% of
the 4600ms cycle, faded by 61.1%, the glove up from 61.6%, then a dark pause of about
2.2s. The Degrees lamp has a violet accent and so a patch of light of its own, and every
lamp carries a neutral fallback accent so none can lose its patch silently. A heading's
wrapped lines are joined with a space, which the phone layouts lay inline. The lamp check
reads both facts and holds the lit span to 2000ms ± 50.

**Lamps and a shorter monitor, 2026-09-11 (fourth pass).** The CRT's tube housing is
84 deep instead of 108 and tapers toward the back; the tower is 114 deep instead of
138. Four portfolio labels now sit on the wall on a broad arch around the machine -
GitHub lower left, About Me above it, Projects I Have Done So Far at the top, Other
Social Medias down the right - each an original 16×16 outlined pixel mark in one of
the accents with Silkscreen lettering, always present and readable, and lit for a
moment on every press of the demonstrated key: up in 40ms, held 200ms, back in 200ms,
a small ellipse of light behind each. They have no timer of their own; their keyframes
share the invitation's duration and start, so contact is the same frame for the glove,
the key, the burst and the lamps. Hover or focus keeps one lit; reduced motion shows
them steady; they are inert whenever the room is not at rest. On phones the arch folds
into the wall above the machine in the same reading order. See
`docs/evidence/lamps/REVIEW.md`.

**Viewpoint, revised 2026-09-11 (third pass).** The scene is now laid out in desk
coordinates and drawn through one projection: the viewer stands in front of the desk
and slightly above it, depth is foreshortened to half and recedes up the picture,
with a modest turn of one pixel left per six units of depth. The keyboard's layout,
the mouse's top and side, the monitor's top casing and the base under it are all
visible; nothing is sheared on the old 2:1 line. The mouse points at the monitor,
palm nearest, buttons and cable at the far end. The monitor is a bezel block over a
narrower tube housing, standing on a tilt/swivel housing that emerges from under the
chin as a dark joint and seats in a socket on a low rounded plate. The keyboard is a
full ANSI layout in key units projected onto its deck: function row, staggered rows,
Backspace, Enter and Shift widths, spacebar, navigation cluster, inverted-T arrows
and a keypad with tall keys. The wide canvas is 576×330 (2× fits 1280×720, 3× fits
1920×1080); the glass stays a true rectangle, so the live screen mapping needed no
new transform, only the regenerated rectangle. The second-pass note below describes
the previous state.

**Equipment, revised 2026-09-11 (second pass).** The CRT support is a compact
tilt/swivel assembly: a dark joint under the casing, a short curved housing that
bellies out and seats in a shaded socket, and a low rounded plate with a visible
top and front edge meeting the desk. The casing is four rows deeper below the chin
so the support stays short; the glass rectangle did not move. The mouse lies
sideways in a low three-quarter view - nose and cable to the left toward the tower,
rounded rear to the right, a continuous shell with two button surfaces split along
the crest, a wheel near the nose and one seam before the palm. Keycaps are flat
lit tops stepped one pixel on the 2:1 line over a one-row front, in dark wells
with clear gaps; the recession is carried by the rows, not by skewing each cap.
The wide desk is a finite freestanding table with both ends in frame, a visible
end thickness and four straight legs (the back pair overlapped by the top); the
narrow framing keeps a tabletop that runs past the phone's edges. Equipment and
room palettes are retained.

The dots appear at 650/1050/1450 ms, then disappear individually at
1850/1970/2090 ms. Each deletion has a 38 ms backspace sound. Typing follows at
2132 ms; the 1500 ms pullback is unchanged. The ideal complete opening is 6952 ms,
and the stale-intro cutoff is 10952 ms, allowing 4000 ms for scheduling delays.

CSS remains the invitation's visual clock. JavaScript reads its contact and first
visible particle keyframes: normally 620 and 740 ms into a 2000 ms cycle. A 24 ms
filtered click sounds at contact; a soft 210 ms filtered whoosh sounds at visible
flight. Both pass through the existing master and cancellation path. Accepting a
demonstrated press finishes its existing burst once. Mute, hidden-page events and
pagehide stop repeating effects; return restores the invitation without an intro.

The following sections retain the project's design history; descriptions of the
earlier Blender/meadow versions are historical, not the current asset pipeline.

## Pixel art, in two themes (2026-09-10, current direction)

The site is pixel art throughout: the computer, the keyboard, the room, the desktop
wallpaper, the icons, the windows, the taskbar and the inner pages all share one grid
and one pair of palettes. This replaced the photorealistic Blender render; that work is
described further down and its asset is no longer part of the site.

**Outlines are the rule.** Pure #FFFFFF on dark, pure #000000 on light, one grid unit
thick, on every outlined object. Both palettes live in `src/styles/tokens.css` and
mirror the generator's palettes exactly, so a window border and the monitor's outline
are literally the same value.

**Whole-number scaling at rest.** The camera can pass through fractional scales; the
scale is picked from the viewport by `src/scripts/room.js` and rechecked on resize.
Narrow and short screens get a *different composition* rather than a smaller copy:
the compact framing brings the monitor forward and regroups the tower, keyboard and
mouse around it, because shrinking the wide framing left the tube unreadable.

**The monitor faces right by drawing, not by transform.** Its oblique depth runs back
and to the left, so you see its left casing; the front face stays a true rectangle on
the grid. A keystoned screen would resample the live text off the grid, which is the one
thing this direction cannot afford.

**Theme switching costs nothing at runtime.** Both artwork variants are in the markup
and CSS picks one, and `theme.js` is a render-blocking external file in the head - not
an inline script - so the correct theme is on the root element before the first paint
while the site's no-inline-script rule survives. Switching touches only palettes and
which image is shown: the opening, the flight, the desktop and its windows are all
untouched, which the tests check explicitly - including a theme change made part-way
through the introduction, which keeps its progress.

Written 2026-09-09, with the first working local version.

The direction Atalay chose: **dreamcore** — a quiet, nostalgic, slightly surreal place.
An almost-familiar landscape remembered from a dream. The structural reference was the
contact page at `phillipche.com`: a narrow centred column, compact horizontal navigation,
left-aligned headings, thin-bordered cards, generous negative space. That *structure* was
adapted. None of its branding, colour, type, imagery or copy was reused — the reference
is dark, sans-serif and video-led; this is none of those things.

## The home page is a different place (added 2026-09-10)

The home page no longer shows the meadow or the editorial column. It is a full-viewport
scene: a large beige CRT computer standing on a desk in a dark, hazy room, with the
introduction typed on its screen. Clicking, tapping or pressing Enter on the glass flies
you into the screen and lands on an early-2000s-inspired desktop.

The inner pages are unchanged and still use the light meadow shell described below.

**Why beige.** The obvious palette for "dreamcore plus cyberpunk" is a near-black ground
with a neon accent, which is one of the commonest generated-design defaults. The machine
is putty-coloured instead, which is what these computers actually were, and a warm beige
object under cold violet light is the opposite of a synthwave picture. Cyan and pink
appear only as *light falling on surfaces* - the screen's spill on the bezel, a thin rim
along the far edge of the casing, a pool on the desk. Neither is used as a fill, a border
or a text colour anywhere in the scene.

**The machine is modelled and rendered, not drawn** (revised 2026-09-10). The first
version was inline SVG and read as flat vector work, which no amount of extra gradient
or glow was going to fix. It is now a Blender/Cycles render of a machine modelled at
real size - 400mm across, 420mm deep - with a tapering rear shell, a moulded seam, cut
ventilation slots, bevelled edges everywhere, physical controls, and a keyboard whose
keycaps are generated on a plane in perspective at true 19mm pitch. Full provenance,
including how to re-render it, is in `docs/ASSETS.md`.

No image-generation tool exists in this environment, and no third-party model or photo
was used. Blender is installed here, so the machine is built from a script instead:
`tools/model_crt.py` is the asset's source.

**The glass is a real element.** The render leaves the tube blank on purpose. A
`<button>` sits over it at the rectangle the renderer measured, so the typed line is
live DOM text, the hit area is the glass, and the flight animates from its actual rect.

**Why the camera never tilts.** It is level and framed by lens shift. A plane parallel
to the image plane projects to a similar rectangle wherever it sits in frame, so the
screen comes out as a true axis-aligned rectangle at exactly 4:3 and the overlay needs
no perspective transform - which keeps the text crisp. Depth still reads because the
machine sits well off the optical axis. `build.mjs` generates the overlay's coordinates
from the render metadata and refuses to build if a future camera change ever skews the
screen.

**The desktop** (revised 2026-09-10) is an early-2000s Windows-era shell: a saturated
blue gradient title bar, compact minimise/maximise/close controls, warm-grey surfaces,
bevelled and inset panels, a menu bar, a status bar with a grip, a green Start tab and a
tray clock. The era's *construction* is reconstructed; none of its artwork is. There is
no Microsoft logo, no Luna wallpaper and no borrowed icon set - the Start mark and the
window icon are this site's lit doorway, and the wallpaper is its night meadow.

**Type.** VT323 for the screen and the desktop's title: a face drawn from a DEC VT320
terminal, which is what the machine is pretending to be. Karla, already self-hosted,
carries the taskbar at small tight sizes. Both OFL, both self-hosted, still nothing
fetched from a third party.

**The flight.** Clicking scales the whole room around the screen's centre until the glass
covers the viewport, so the bezel and the room leave the frame rather than a panel
appearing over them. The screen's wallpaper fades up as it grows and the real desktop
crossfades in over the last 40%, which is why nothing sharp is ever scaled and no text
stretches. 1.4 s on a slow-in, slow-out curve. Under `prefers-reduced-motion` the whole
thing is a 160 ms fade and the introduction is shown complete, without the typewriter.

**One script.** The home page is the only page that loads JavaScript, and it is one
same-origin file with no inline code and no inline handlers. `npm test` enforces exactly
that, and still enforces zero script on the other four pages.

## The one bold thing

A doorway standing by itself in a wide meadow, lit from inside, under drifting cloud.

It is the only loud element on the site. Everything around it is deliberately quiet:
one column, two typefaces, hairline rules, no shadows, no gradients used as decoration.
The scene appears on every page — full, with the doorway, on Home; as a horizon strip
elsewhere — so moving between pages feels like staying in one place rather than being
cut somewhere new.

It is **original inline SVG** (`src/components/scene.js`). No stock imagery, no
third-party assets, nothing hotlinked, nothing fetched at runtime. It weighs about 7 KB
of markup, stays crisp at any size, and takes its colours from the design tokens.

The empty-doorway motif also does honest work: a project with no cleared screenshot
renders **a doorway with nothing through it**, captioned "No screenshot yet", instead of
a grey box or a fabricated image.

## Palette

Set in `src/styles/tokens.css`. Ratios were measured, not estimated.

| Token | Value | Role |
|---|---|---|
| `--sky-high` | `#9FC4E2` | top of the sky |
| `--sky` | `#C3D9E8` | faded sky blue |
| `--haze` | `#D9D3E6` | misty lavender where sky meets land |
| `--meadow` / `--meadow-deep` | `#9FB093` / `#93A985` | muted meadow green |
| `--paper` | `#F2F0E6` | soft ivory — the bottom of the sky, not a separate sheet |
| `--door-light` | `#F6E7C0` | the glow through the doorway |
| `--ink` | `#26303B` | body and headings — 11.7:1 on paper |
| `--ink-soft` | `#4C5A68` | secondary text — 6.2:1 on paper |
| `--ink-on-sky` | `#3C4855` | navigation — 5.1:1 on the darkest sky the artwork paints |
| `--dusk` | `#42527A` | links and the focus ring — 6.8:1 on paper |
| `--edge` | `#8E8A79` | card boundary — 3.0:1 on paper, meeting WCAG 1.4.11 |

`--ink-on-sky` exists because of a real defect found during review. Navigation sits on
painted artwork, not on the band's flat CSS background, and `--ink-soft` measured
**3.86:1** against the darkest pixel of the sky — under AA. `tools/check_pages.py` now
screenshots the masthead area with the text hidden and samples the actual pixels, so
this class of mistake fails the check instead of passing it.

**Light only.** The design is a daylight meadow; a dark variant would be a different
scene, not a recolour. `color-scheme: light` is declared so browsers do not invert it.
Worth revisiting with Atalay if he wants a night version — that is a design job, not a
token swap.

## Type

Two families, both self-hosted, both SIL Open Font License 1.1. Nothing is requested
from a third party at runtime: no Google Fonts, no CDN, no tracking, and no font-related
entry needed in a future CSP.

- **Fraunces** — headings and the wordmark. A variable face with an optical-size axis;
  set around `opsz 38` rather than its display extreme, which keeps the serifs sturdy
  and warm instead of thin and fashionable. This is where the nostalgia comes from.
- **Karla** — body and interface. A grotesque with enough character to avoid the
  neutral-default feeling, and it sits well under a soft serif.

Scale follows the traditional sizes rather than a generated ramp: 13 / 17 / 19 / 22 px,
with the page title fluid between 30 and 40 px. Body measure is capped at 64 characters.

## Motion

Motion here is **weather**, not interface decoration.

- Three cloud bands drift at 130 s / 200 s / 300 s. Higher in the frame reads as nearer,
  so those are larger and faster. Each band is drawn once and `<use>`d twice at a
  1600-unit offset, so a full translation returns to an identical frame and the loop is
  invisible.
- The doorway glow breathes over 16 s.
- That is all on the inner pages: nothing animates on scroll, nothing fades in per
  section, there is no cursor effect.

The home page is the exception, and deliberately so. It opens inside the display on a
lit but EMPTY tube, holds for 650ms, then puts up three dots 400ms apart - one beep
each - removes them at 1850/1970/2090ms and prints two lines. Then ONE camera - a single transform
on the scene's common parent - pulls back through the whole room until the desk, tower,
keyboard, mouse and cables have all arrived around the monitor.

It then invites a press on a two-second cycle with a quiet pause. Three decisions there
are worth writing down, because each replaced something that read wrongly:

- **The hand presses straight down, and nothing else.** Its shape says so - an upright
  palm, a level cuff, one vertical index finger - and so does its movement: the sprite
  has its fingertip anchored on the button's centre line in CSS, and only `translateY` is ever
  animated. There is no horizontal term in the cycle to drift, and no rotation.
  `tools/check_room.py` samples the whole cycle and asserts the drift is zero rather
  than checking the two ends, since a sideways excursion that returns to centre would
  pass a two-point check and still look like a swipe.
- **The burst leaves the screen.** It used to live inside `.crt__glass`, which sets
  `overflow: hidden`, so it could only ever pile up against the bezel. It is now a
  sibling of the screen - still inside the moving scene, so the camera carries it, but
  clipped by nothing - and its origin is written from the same measured variables that
  place the screen and the button. The marks cross the glass, pass in front of the
  moulding and travel out into the room before fading.
- **Scanlines are for the tube, not for objects on it.** They sit below the hand and the
  button now. A dark stripe every other row is wide enough at this scale to cut a small
  sprite and an eight-pixel label into unreadable bands, which is what it was doing.

**Sound is offered, never taken.** A browser will not let a page make a noise before
someone has interacted with it, and no delay gets around that - a context created without
a gesture is born suspended and stays there, so every beep the old code "played" during
the opening was scheduled onto a context that was not running. The opening therefore
always plays SILENTLY, and a clearly labelled *Play intro with sound* control replays it
from its initial hold so the three beeps can actually be heard. That is a deliberate
replay on request; a refresh still skips the completed intro. `tools/check_audio.py`
measures the signal reaching `ctx.destination` rather than counting scheduled notes, and
leaves a recording of what came out.

Under `prefers-reduced-motion: reduce` the introduction is presented complete with no
character animation, the room is revealed with a brief fade, and the hand stands still
ON the key beside a plain Click/Tap label, with no burst and no brightness pulse.

Under `prefers-reduced-motion: reduce` every animation stops and the static frame is the
composition — it was designed to be looked at still. Cross-document view transitions are
enabled where the browser supports them, and disabled under the same query.

## Deliberate non-choices

Checked against the patterns that make generated design recognisable, and avoided:
no tracked-out ALL-CAPS eyebrow labels, no `A · B · C` meta strings, no `→` appended to
link text, no 01/02/03 numbering, no uniform rounded-card kit with one shadow under
everything, no scroll-triggered entrances.

The warm-cream background is the closest call — it is a known tell. Atalay's brief names
"soft ivory" explicitly, so it stays, but it is cooled toward green-grey, it is presented
as the bottom of the sky rather than a flat sheet, and it is paired with sky and meadow
rather than the terracotta accent that usually accompanies it.

Structure carries meaning rather than decorating: projects get wide apertures (a view
into the work), contact gets thin-bordered cards (the reference's device), the home list
gets hairline-separated rows. Three different treatments because they are three
different kinds of thing.
