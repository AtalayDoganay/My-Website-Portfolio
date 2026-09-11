# atalaydoganay.com

Personal portfolio website for Atalay Doganay.

## Status

**A first working local version.** Five pages build and run on a local preview server.
The home page is an interactive scene - an old computer you enter; the rest of the site
is a quiet light-themed portfolio.

Not hosted. Not deployed. The domain `atalaydoganay.com` is a target, not a connected
domain, and no hosting account exists. Nothing on the site has been published, and the
project write-ups still need Atalay's sign-off before they go anywhere public — see
`docs/CONTENT-SOURCES.md`.

## Run it

```bash
npm run preview     # build, then serve at http://127.0.0.1:4321/
npm run dev         # the same, plus rebuild on change
npm run build       # build to dist/ only
npm test            # escaping and URL-scheme checks
```

There is nothing to install. `package.json` has **no dependencies** — not in production,
not in development.

## Checks

```bash
npm test                        # escaping, URL schemes, script policy
node tools/check_links.mjs      # every internal link and fragment resolves
```

`tools/check_room.py` drives the home page's opening sequence: it records every frame of
the typed introduction with timestamps and checks both the exact text and the measured
timing, then exercises hover, pointer leave, keyboard entry, touch entry, repeated clicks
mid-transition, arrival, return and replay, mobile layout and reduced motion.

`tools/check_pages.py` drives real Chromium over all five pages at desktop and phone
widths: console errors, failed requests, horizontal overflow, colour contrast (including
sampling the artwork's actual pixels behind the navigation), a full axe-core scan, touch
target sizes, keyboard focus order, and whether reduced motion really stops the animation.
It writes screenshots so the pages can be looked at rather than assumed.

It needs two things that are deliberately not committed - a Python virtual environment and
axe-core. Both report themselves as unavailable rather than silently passing if missing.

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install playwright
.venv/Scripts/python.exe -m playwright install chromium
mkdir -p tools/vendor
curl -o tools/vendor/axe.min.js https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js

.venv/Scripts/python.exe .claude/skills/webapp-testing/scripts/with_server.py --server "npm run preview" --port 4321 -- .venv/Scripts/python.exe tools/check_pages.py --out ./shots
```

What each check covers, and what is still unavailable, is in `docs/RELEASE-CHECKS.md`.

## Layout

| Path | What it is |
|---|---|
| `src/data/site.js` | **All the content.** Edit this to change what the site says |
| `src/pages/` | One module per page |
| `src/components/` | Page shell, the scenes, and the reusable pieces |
| `src/scripts/room.js` | The opening scene's behaviour. Timing is in `TUNING` at the top |
| `src/assets/pixel/` | The pixel art and the metadata that positions the screen |
| `tools/pixel_art.py` | Draws all of it. See `docs/ASSETS.md` |
| `src/scripts/theme.js` | Theme state, loaded render-blocking so nothing flashes |
| `src/styles/` | Design tokens and stylesheets, concatenated at build time |
| `src/assets/fonts/` | Self-hosted Fraunces and Karla, with their licences |
| `build.mjs` / `serve.mjs` | The build and the preview server |
| `tools/check_pages.py` | Browser checks: contrast, axe, focus, overflow, reduced motion |
| `tools/check_room.py` | Drives the whole opening sequence in a browser and measures it |
| `tools/check_theme.py` | Both themes across seven viewports: outlines, scaling, persistence |
| `tools/check_escaping.mjs` | Proves data cannot become markup, and self-tests that it can detect injection |
| `tools/check_links.mjs` | Internal link and fragment resolution |
| `dist/` | Build output. Not committed |

To change a project write-up, add a screenshot, or add a contact channel, edit
`src/data/site.js`. The rules that govern what may be written there are at the top of
that file and in `CLAUDE.md`.

## Documentation

| Path | What it is |
|---|---|
| `docs/PROJECT-BRIEF.md` | Goals, audiences, confirmed facts, and the stack and design decisions |
| `docs/DESIGN-NOTES.md` | Palette, type, the scene, motion, and measured contrast |
| `docs/ASSETS.md` | Where every asset came from, and how to regenerate the render |
| `docs/CONTENT-SOURCES.md` | The source of every claim on the site, and what is still missing |
| `docs/HOSTING-DECISIONS.md` | Open hosting, domain, DNS and deployment decisions |
| `docs/RELEASE-CHECKS.md` | Which checks are active and which to activate when |
| `CLAUDE.md` | Working instructions, including the content and security rules |

## Installed skills

Two sets, tracked separately so their installers do not compete.

From [`claude-web-toolkit`](https://github.com/AtalayDoganay/claude-web-toolkit), recorded
in `.claude/skills-manifest.json`. Update them by editing the toolkit and re-running its
installer with `-Update`. Do not hand-edit the copies here.

| Skill | Use it when |
|---|---|
| `web-build` | Implementing or changing pages, components, or features |
| `web-design-review` | Reviewing typography, spacing, hierarchy, mobile, accessibility |
| `web-security-review` | Reviewing the real attack surface |
| `web-release-check` | Running the project's real build and checks |

From [`anthropics/skills`](https://github.com/anthropics/skills) at revision
`41bbe19`, Apache 2.0, each with its `LICENSE.txt` preserved. Provenance and a SHA-256 per
file are in `.claude/skills-external.json`.

| Skill | Use it when |
|---|---|
| `frontend-design` | Making visual and typographic decisions |
| `webapp-testing` | Driving a browser to verify what actually rendered |

## Next step

Atalay reviews the local preview. Open items are listed under "Missing material" in
`docs/CONTENT-SOURCES.md`.
