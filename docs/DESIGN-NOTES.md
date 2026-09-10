# Design notes

Written 2026-09-09, with the first working local version.

The direction Atalay chose: **dreamcore** — a quiet, nostalgic, slightly surreal place.
An almost-familiar landscape remembered from a dream. The structural reference was the
contact page at `phillipche.com`: a narrow centred column, compact horizontal navigation,
left-aligned headings, thin-bordered cards, generous negative space. That *structure* was
adapted. None of its branding, colour, type, imagery or copy was reused — the reference
is dark, sans-serif and video-led; this is none of those things.

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
- That is all. Nothing animates on scroll, nothing fades in per section, there is no
  loading sequence, no cursor effect, no audio.

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
