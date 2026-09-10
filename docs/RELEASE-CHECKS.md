# Release checks for this project

Updated 2026-09-09, when the first working local version was built. Before that, this
repository had no application and almost every check was Unavailable. Several are now
real. The rest still are not, and are marked as such rather than faked.

A green check nobody can trust is worse than an absent one. Nothing below is reported as
passing unless it ran.

## Active now

| Check | Command | What it does |
|---|---|---|
| Build | `npm run build` | Renders the five pages to `dist/`. Non-zero exit on any failure |
| Escaping and URL schemes | `npm test` | Runs `tools/check_escaping.mjs` |
| Internal links | `node tools/check_links.mjs` | Every internal href, src and fragment in `dist/` must resolve |
| Browser checks | `tools/check_pages.py` | See below |
| Secret scan | manual review of tree and history | Do before every push |

### `npm test` — escaping and URL schemes

Renders every component twice, once with inert text and once with a hostile payload, and
compares the **tag structure** of the outputs — element and attribute names with all text
and attribute values stripped. If a payload created an element or an attribute, the
structures differ and the test fails.

It begins with a self-test that feeds an unescaped interpolation through the same
detector and fails the whole run if the injection is *not* spotted. A test that cannot
fail is not a check, and this one proves it can before it proves anything else.

It also asserts that `safeUrl()` refuses `javascript:`, `data:` and `vbscript:` URLs while
still accepting the ones the site uses, and that no shipped page contains a `<script>`
tag, an inline event handler, or a dangerous URL scheme.

### `tools/check_pages.py` — browser checks

Drives real Chromium over all five pages at 1280x900 and 390x844:

- console errors and warnings (the deliberate 404 request is attributed and excluded)
- failed requests and any HTTP status of 400 or more
- horizontal overflow (`scrollWidth` against `clientWidth`)
- colour contrast on every text node, against its **computed** background
- colour contrast for text sitting on the scene, against the **artwork's actual pixels** —
  the masthead is screenshotted with its text hidden and the darkest pixel sampled. The
  computed-background check cannot see this and reported a pass where the real ratio was
  3.86:1. Do not remove it.
- axe-core 4.10.2: wcag2a, wcag2aa, wcag21a, wcag21aa, best-practice
- touch target sizes at phone width
- keyboard focus order and whether the focus ring is actually set
- whether `prefers-reduced-motion` genuinely stops the animation
- screenshots of every page at both widths, for looking at rather than assuming

It needs Python Playwright in `.venv/` and `tools/vendor/axe.min.js`; neither is
committed. Both are Unavailable rather than skipped if missing — axe reports its own
absence in the output. Setup is in `README.md`.

## Not applicable

| Check | Why |
|---|---|
| Dependency audit | `package.json` has zero dependencies and there is no lockfile. `npm audit` exits `ENOLOCK`. Activate the moment a first dependency is added |
| Server-side input validation, CSRF, sessions, rate limiting | No server, no forms, no handlers, no state |
| Client-side script review | The site ships no JavaScript. `npm test` fails if that changes |

## Still Unavailable

| Check | What would be needed |
|---|---|
| HTML validation | A validator. The W3C Nu service would mean sending page content to a third party, which is Atalay's call, not a default. A local `html-validate` or `vnu.jar` would be the alternative |
| External link reachability | A checker. `node tools/check_links.mjs` currently lists external links rather than fetching them. There is one: `https://github.com/AtalayDoganay` |
| Lighthouse performance budget | Not configured |
| CI | No workflow exists. Adding one requires the repository to exist on GitHub |

## Activate when hosting is chosen

See `docs/HOSTING-DECISIONS.md`. None of these can be done yet, and none should be faked.

- Response header verification against the **live response**, not a config file.
- CSP verification — present, and the page still works. The real origins are easy here:
  the site loads nothing cross-origin at all. Fonts are self-hosted, there are no
  scripts, no analytics, no embeds. `default-src 'self'` plus `img-src 'self' data:` for
  the grain texture is close to the whole policy, but it must still be tested against the
  deployed response.
- HSTS — only after HTTPS and subdomain coverage are confirmed.

## Rules for any workflow added later

- Least-privilege `permissions:` at workflow level, raised per job only where needed.
- Third-party actions pinned to a verified full commit SHA, never a tag.
- No secrets exposed to workflows triggered by untrusted pull requests.
- **No `continue-on-error` on a security or test gate.** A check that cannot fail is not a check.

## Release blockers

Blocking, regardless of what else passes:

- A secret exposed in the repository, its history, or build output.
- A reproducible, exploitable vulnerability.
- A failing required test or a failing build.
- **A public claim that has not been confirmed.** This project's specific risk is not a
  crash, it is publishing something untrue about a real person. `docs/CONTENT-SOURCES.md`
  is the record; anything on the site that is not traceable to a row there is a blocker.

For each, record whether it was **resolved** or **explicitly accepted by Atalay**, and the
reasoning. An unresolved blocker means not ready.

## Repository protections

Branch protection on `main` has **not** been configured. It requires the repository to
exist on GitHub first, and on a free plan protection rules for private repositories may be
unavailable — in which case the limitation should be reported rather than worked around.
A required status check cannot be configured until a workflow has actually run once.
