---
name: web-release-check
description: Use before releasing or deploying a website - runs the project's real build, tests, link, accessibility, dependency, and secret checks, and reports passed, failed, unavailable, and not-applicable results honestly. Does not deploy.
---

# web-release-check

Run the checks that exist and report exactly what happened.

## Discover, then run

Read the package manifest, CI workflows, and project instructions to find the real commands. Run what exists:

- Build - the project's actual build command; the build must succeed, not merely emit warnings you skipped reading.
- Tests - the project's real test suite.
- Links - internal links resolve; external links reachable if a checker is configured.
- Accessibility - the configured checker (axe, pa11y, Lighthouse) against real pages.
- Dependencies - audit for known advisories; review outdated and newly added packages.
- Secrets - scan the working tree and history.
- Hosting configuration - headers, redirects, and build settings match the intended platform.

## Report each check as one of four states

- **Passed** - it ran and succeeded. Quote the command and the result.
- **Failed** - it ran and failed. Quote the actual error.
- **Unavailable** - the tooling is not installed or configured. Say what would be needed.
- **Not applicable** - the project has no such surface. Say why.

Never report a check as passed because it was skipped, because a config file exists, or because it "should" pass. Never use `continue-on-error` or a swallowed exit code to manufacture a pass. If a project has no application manifest yet, most app checks are Unavailable - record which to activate when implementation begins rather than inventing dummy commands.

## Release blockers

Treat these as blocking, and say so plainly:

- A secret exposed in the repository, history, or build output.
- A reproducible, exploitable vulnerability.
- A failing required test or a failing build.

For each blocker, state whether it was resolved or explicitly accepted by the owner, and by what reasoning. An unresolved blocker means the release is not ready, regardless of how much else passed.

## Distinguish these carefully

- A committed workflow file vs. a workflow run that actually succeeded.
- A check that ran vs. a branch protection rule that requires it.
- Setup being complete vs. a site being deployed, live, or secure.

## Deployment

Do not deploy. Report readiness and wait for an explicit request to deploy.
