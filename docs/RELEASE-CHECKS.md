# Release checks for this project

This repository currently has **no application** — no package manifest, no build, no pages.
So it has no build job, no test job, and no npm commands.

That is deliberate. A CI job that "passes" because it does nothing produces a green check
that means nothing, and a green check nobody can trust is worse than an absent one. The
checks below get switched on when the thing they test exists.

## Available now

| Check | How | Status |
|---|---|---|
| Secret scan of tree and history | manual review, or a scanner once added | Do before every push |
| Markdown review | read the diff | Manual |

## Activate when a package manifest exists

- Build — must fail the job on non-zero exit.
- Unit / component tests — no placeholder test that asserts `true`.
- Dependency audit — review advisories; do not auto-merge fixes.
- Outdated dependency report — advisory, non-blocking.

## Activate when pages exist

- Accessibility scan (axe / pa11y / Lighthouse) against real rendered pages.
- Internal link check.
- HTML validation.
- Contrast verification against computed colors, in every theme the site supports.

## Activate when hosting is chosen

See `docs/HOSTING-DECISIONS.md`.

- Response header verification against the **live response**, not a config file.
- CSP verification — present, and the page still works.
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

For each, record whether it was **resolved** or **explicitly accepted by Atalay**, and the
reasoning. An unresolved blocker means not ready.

## Repository protections

Branch protection on `main` for these repositories has **not** been configured. It requires
the repositories to exist on GitHub first, and on a free plan, protection rules for private
repositories may be unavailable — in which case the limitation should be reported rather than
worked around. Note that a required status check cannot be configured until a workflow has
actually run at least once.
