# Where every claim on the site comes from

Written 2026-09-09, when the first working local version was built.

The site makes public claims about a real person. This file records the source of each
one so a later session — or Atalay — can check them without re-deriving anything. If a
sentence on the site is not traceable to a row here, it should not be there.

**Nothing on this site has been published.** It runs locally only. Everything below is
still subject to Atalay's sign-off before it goes anywhere public.

## Sources referenced

| Key | What it is |
|---|---|
| `BRIEF` | `docs/PROJECT-BRIEF.md`, "Confirmed content" |
| `BF-README` | `README.md` in Atalay's `Game-For-Insta` repository, read read-only |
| `NC-README` | `README.md` in Atalay's `Class-schedule-app` repository, read read-only |
| `NC-APP` | `app.json` in the same repository (the app's own name) |

The two repositories were read without being modified. They belong to other work and
were not touched.

## Home

| Claim | Source |
|---|---|
| Name: Atalay Doganay | `BRIEF` |
| Computer science student at Cal Poly Pomona | `BRIEF` |
| Interested in software engineering and indie game development | `BRIEF` |
| "I make browser games and small apps" | `BF-README` (a browser game) and `NC-README` (a phone app) |
| "No account to make, no server to keep alive, no build step if I can avoid one" | `BF-README` ("no build, no libraries, no server") and `NC-README` ("No account, no server, no sync") |

## About

| Claim | Source |
|---|---|
| Computer science student at Cal Poly Pomona | `BRIEF` |
| Associate in Science in Computer Science, Orange Coast College | `BRIEF` |
| Time zones, per-platform limits, behaviour after a reboot | `NC-README` — all three are described there as real problems the app handles |
| Interest in how something feels to watch | `BF-README` — the game is explicitly built to be watched |

No dates, no employers, no job titles. None are confirmed and none appear.

## Projects — BALL FIGHTERS

| Claim | Source |
|---|---|
| "A browser auto-battler" | `BF-README` |
| Pick two fighters, choose an arena, the match plays itself | `BF-README` |
| Built to be watched, tall portrait window, short-form-video shaped | `BF-README` |
| Classic script files sharing one global, no build step, no libraries | `BF-README` |
| Runs by opening `index.html` off the disk | `BF-README` and `BRIEF` |
| No modules, no fetching local files | `BF-README` |
| Pixel art drawn on canvas or embedded as base64 | `BF-README` |
| Most audio synthesised with Web Audio | `BF-README` |
| Five arenas presenting the same fight | `BF-README` |
| Vanilla JavaScript, HTML canvas, Web Audio | `BF-README` |
| Portrait, 480 x 854 | `BF-README` and `BRIEF` |

## Projects — Next Class

| Claim | Source |
|---|---|
| The name "Next Class" | `NC-APP` and the `NC-README` title |
| "A class reminder app for students" | `NC-README` |
| The glance-at-your-phone summary sentence | `NC-README`, near-verbatim from its opening |
| No account, no server, no sync; schedule lives on the device | `NC-README` |
| Reminders are weekly repeating triggers delivered by the OS | `NC-README` |
| Survives the app being closed, swiped away, or the phone restarting | `NC-README` |
| Weekday plus wall-clock time rather than a timestamp | `NC-README` |
| iOS caps an app at 64 pending notifications; the planner drops a whole tier | `NC-README` |
| React Native and TypeScript on Expo | `NC-README` |

## Deliberately absent

These are *not* on the site, because they are not confirmed. Adding any of them needs
Atalay's explicit go-ahead.

- **No contact email.** Forbidden by `CLAUDE.md` until Atalay supplies a public one.
- **No project links or repository URLs**, for either project.
- **No release status.** Neither project is described as released, playable, shipped,
  in progress, or available.
- **No screenshots.** See below.
- **No download counts, user numbers, or any other metric.**
- **No solo/team attribution** for Next Class — `BRIEF` lists this as unverified and
  the site makes no claim either way.
- **No resume**, in any form. Publishing one is not authorised.

## Missing material Atalay needs to provide

1. **Screenshots for both projects.** Each project renders an empty doorway captioned
   "No screenshot yet" until real captures are cleared. Dev and QA captures do exist on
   the desktop (`BALL-FIGHTERS-EVIDENCE`, `BALL-FIGHTERS-REVIEW`), but they are wall
   damage comparisons and test frames, not presentation material, and none is cleared
   for publication. To add one: put the file in `src/assets/` and fill in the
   `screenshot` field in `src/data/site.js`.
2. **A public contact email**, if he wants one on the site. Currently only GitHub is listed.
3. **Any other public accounts** — LinkedIn, itch.io, YouTube — with the exact handles.
4. **Release status for each project**, and whether either has a link a visitor can follow.
5. **Repository visibility.** `Game-For-Insta` is MIT-licensed; `Class-schedule-app` is
   "All Rights Reserved, source-available for viewing". Whether either should be linked
   publicly is his call.
6. **Confirmation of the project descriptions above.** They are drawn from his own
   READMEs, but a README is written for developers and a portfolio page is written for
   strangers. He should read them as published sentences.
7. **Sign-off on the Cal Poly Pomona / Orange Coast College wording**, including whether
   he wants dates or an expected graduation shown. Neither appears now.
