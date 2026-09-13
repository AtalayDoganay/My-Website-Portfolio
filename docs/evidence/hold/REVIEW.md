# A press and hold, and five lamps that are gone in between — 2026-09-11, fifth pass

[Open the visual review](index.html) · [Preview](http://127.0.0.1:4321/) ·
[Fourth pass](../lamps/REVIEW.md)

## Starting point and preservation

Taken over from the committed fourth pass (`7e9f338`) with a clean tree. Nothing was
reset, checked out or deployed. The equipment, the intro (dots, deletion, typing,
sounds, replay, refresh skipping), the shared camera and the desktop behaviour were
not edited. No screenshot file accompanied the request and none with red marks was
found on disk (the newest images in Downloads and Pictures are the four references
and unrelated captures), so the five positions follow the written placement.

## 1. The five lamps and their positions

GitHub at the far lower left (past the desk's end where the window allows, above the
desk where it does not), About Me high on the left, Projects I Have Done So Far at the
crown, Other Social Medias high on the right, and Degrees, Certificates & Skills lower
down the right side. Positions are fractions of the artwork's displayed box with floors
so nothing lands on the theme switch, the sound and reveal controls, the glass or the
burst's reach; the check measures that at 1440×900 and 390×844 in both themes. On
phones the arch folds into three rows above the machine in the same reading order;
long headings wrap; the machine keeps its size. A phone held sideways gets two columns
in the side margins.

Icons: the GitHub lamp is a 16×16 pixel treatment of GitHub's own Invertocat, traced
from the official logo package and drawn in ink only so it renders in the mark's own
black or white - source, guidance and the modification it implies are recorded in
`docs/ASSETS.md`. About Me (bust) and Projects (folder) are unchanged; Other Social
Medias keeps the joined message bubbles; Degrees is a rolled diploma with a ribbon.
The fifth destination is a new credentials section of the About page that carries only
the confirmed degrees, a note that no certificates are listed yet, and a pointer to the
projects for skills - nothing invented. The desktop window lists the same five links,
so the destinations are reachable without the demonstration.

## 2. Hidden between presses

Between presses the lamps are `visibility: hidden`: not drawn, not hoverable, not
clickable or tappable, not focusable, and not in the accessibility tree. Their
positions stay reserved (`position: absolute`, fixed centres), so the reveal moves
nothing. Both themes use the same rule; only the light patch differs (accent tint on
dark, warm white on light).

## 3. The press and hold

One 4600ms cycle, one clock. The hand, the key, the burst and the lamps run keyframes
of the same duration that start on the same state change; the audio and the focus
hand-off follow the hand animation's own playhead through one frame observer. In
order: the glove comes straight down; at 10% (460ms) it touches the key, the key
depresses, the click sounds once, the burst launches once and the lamps light over
50ms; the glove holds the key down and the lamps stay fully lit until 54.6% (2512ms);
as the glove lifts the lamps fade over 300ms (to 61.1%) and refuse the pointer from
the first frame of the fade; from 61.2% they are hidden through a dark pause of
about 2.2s. A real activation lights them once from the press and goes on into the
desktop as before; the main button's job is unchanged.

Links can be activated during the lit phase. A lamp that has keyboard focus when the
fade begins hands it to the "Show links" control beside the sound control. That control
shows all five steadily until closed (Escape closes it and returns focus to it), and
under reduced motion, where nothing is demonstrated, it is the only reveal.

## Visual findings

Judged on the page at 1440×900 and 390×844 in both themes, and in the crops.

- Dark rest: nothing on the walls. Hold: all five at the marked positions with the
  glove on the depressed key. Fade: all five dim together as the glove lifts. Hidden:
  nothing again. The burst leaves once at contact and is gone long before the release.
- The Invertocat reads at 32px: ring, ears, face, tail. The diploma reads as a scroll
  with a ribbon; its first draft read as a speech bubble and was redrawn.
- In the light theme the patches of light are quiet by design; the lit lettering
  carries the reveal there.
- Still open, by eye: the burst's last pieces can drift near About Me and GitHub as
  they fade; on very short phones the third row sits close above the monitor.

## Verification

| Check | Result |
|---|---|
| `node build.mjs`, `tools/check_escaping.mjs`, `tools/check_links.mjs` | Builds; escaping holds for the new links (every href through `safeUrl`); all internal links and the new `#degrees-certificates-skills` fragment resolve |
| `tools/check_lamps.py` (rewritten) | 25 checks, 0 failures. All five lamps share the hand's start time and 4600ms duration; each heading reads as its label with its wrapped lines spaced, and each light patch has a colour of its own; press→light offset 0ms in consecutive live cycles at a 17ms frame, cadence 4600ms; lit 2000/2000ms, visible 2334/2333ms, hidden afterwards; no animations or interval timers accumulate across cycles. Dark phase: the pointer over a lamp's reserved position finds the stage, a click there goes nowhere, six Tabs never land on a lamp. Lit phase: the lamp is visible and under the pointer, Tab from the key reaches GitHub with a 2px ring, clicking About Me navigates to `/about/`. A lamp focused during the hold hands focus to the reveal control at the release. The control opens all five steadily ("Hide links"), Escape closes it and returns focus. A real activation in the dark phase lights them within 70ms; on the desktop they are inert, hidden and never focused, and the desktop lists the same five destinations; usable again on return. Reduced motion: no loop, lamps hidden, the control opens a steady menu. Desktop and phone, both themes: five lamps inside the window, 44px+, apart from each other, the glass and the controls |
| `tools/check_room.py` (retimed from the page's keyframes) | 62 checks, 0 failures, 0 console messages: intro timing, deletion, pullback, the fingertip on the depressed key inside the hold, straight-down travel across the whole 4600ms cycle, the burst escaping the glass mid-flight and still showing as entry begins, entry, return, skip, touch, keyboard (the first Tab still reaches the key), reduced motion, refresh |
| `tools/check_theme.py` | 74 checks, 0 failures, 0 console messages (7 viewports including the sideways phone, both themes, whole-number scale, no overflow with five lamps and the reveal control present) |
| `tools/check_audio.py` (retimed from the page's keyframes) | 22 checks, 0 failures: dot beeps, backspaces, typing; two demonstration cycles sound once at contact and once at visible flight, quieter than the beeps; a real activation in the dark pause fires one click and one flight; desktop entry silences; the restored demonstration sounds again at its first contact after return; a click during the held press reuses the one existing burst; mute, hiding and teardown leave silence. One earlier run missed a single 40ms backspace window and passed on re-run; the recording is sampled per frame, so a dropped frame can empty a window that short |
| `tools/check_pages.py` | 0 problems: no console messages, failed requests, overflow, contrast or axe errors on the five pages at two widths, the new About section and desktop links included. The same eight pre-existing small link targets on the inner pages remain listed |
| `tools/check_scene.py` | 14 checks, 0 failures: identical theme geometry, overlay on the glass in both framings, no stray click targets |

**Expectations that intentionally changed.** The room and audio checks used to assume
the 2000ms cycle (parked frames at 700 and 1240ms, cycle windows of 2000, an activation
window at 1380-1530ms). They now read the cycle's duration, contact and release beats
from the hand animation's keyframes, so the retimed demonstration retimes them. The lamp
check was rewritten for the new semantics: hidden rather than subdued between presses,
a two-second lit hold, focus hand-off, the reveal control, and no accumulation.

**Limits.** The browser here renders at 17-34ms frames, which is the precision of "the
same frame". No perceptual listening pass and no physical phone. Visual judgements are
mine from screenshots and crops.

## Corrections after review, 2026-09-12

Checking the finished pass against the written requirements found three shortfalls,
each fixed and re-verified:

- **The hold was 1933ms, not 2000ms.** The lit span ran from 11.1% to 53% of the
  4600ms cycle. It now runs to 54.6% (510ms to 2512ms), the key and the glove hold to
  the same beat, the fade runs to 61.1%, and the glove is up from 61.6%. The lamp
  check's tolerance was tightened to 2000ms ± 50 first; it failed at 1933ms and passes
  at 2000/2000ms after the change. The dark pause is about 2.2s.
- **The Degrees lamp had no patch of light.** It had no `--lamp-accent`, so its glow's
  gradient was invalid and never drew; only its lettering lit. It is violet now, and
  every lamp carries a neutral fallback accent so a lamp can never lose its patch
  silently. A new check reads each patch's computed background and refuses `none`.
- **Wrapped headings ran together on phones.** The two lines of "Degrees,
  Certificates & Skills" and "Projects I Have Done So Far" were joined without a
  space, which the phone layouts, laying them inline, rendered as "Certificates&
  Skills". The lines are joined with a space; a new check reads each heading's text.

Results after the corrections: lamps 25 checks, 0 failures (lit 2000/2000ms, visible
2334/2333ms); room 62, theme 74, audio 22, scene 14, all 0 failures; pages 0 problems;
escaping and links pass. The captures in `after/` were regenerated by the lamp check.

Preview remains at http://127.0.0.1:4321/. Work is uncommitted and not deployed.
