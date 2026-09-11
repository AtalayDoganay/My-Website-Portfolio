# Design notes

## Pixel art, in two themes (2026-09-10, current direction)

The site is pixel art throughout: the computer, the keyboard, the room, the desktop
wallpaper, the icons, the windows, the taskbar and the inner pages all share one grid
and one pair of palettes. This replaced the photorealistic Blender render; that work is
described further down and its asset is no longer part of the site.

**Outlines are the rule.** Pure #FFFFFF on dark, pure #000000 on light, one grid unit
thick, on every outlined object. Both palettes live in `src/styles/tokens.css` and
mirror the generator's palettes exactly, so a window border and the monitor's outline
are literally the same value.

**Whole-number scaling only.** Raster art is never shown at a fractional multiple; the
scale is picked from the viewport by `src/scripts/room.js` and rechecked on resize.
Narrow and short screens get a *different composition* rather than a smaller copy - the
monitor alone on a smaller canvas - because shrinking the wide framing left the tube
unreadable.

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

The home page is the exception, and deliberately so. It opens inside the display, prints
two lines, and then ONE camera - a single transform on the scene's common parent - pulls
back through the whole room until the desk, tower, keyboard, mouse and cables have all
arrived around the monitor. It then invites a click with a gloved pixel hand and a short
colourful burst on a two-second cycle with a quiet pause. Optional retro beeps are
off until someone turns them on. Under `prefers-reduced-motion: reduce` the introduction
is presented complete with no character animation, the room is revealed with a brief
fade, and the hand stands still beside a plain Click/Tap label with no burst and no
brightness pulse.

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
