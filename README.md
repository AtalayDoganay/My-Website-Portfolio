# atalaydoganay.com

Personal portfolio website for Atalay Doganay.

## Status

**Setup only.** There is no website yet — no design, no pages, no build, no hosting, no
deployment. The domain `atalaydoganay.com` is a target, not a connected domain.

This repository currently contains the brief, the working instructions, and the Claude Code
skills the project will use.

## Contents

| Path | What it is |
|---|---|
| `docs/PROJECT-BRIEF.md` | Goals, audiences, confirmed facts, candidate projects, what needs verifying |
| `docs/HOSTING-DECISIONS.md` | Open hosting, domain, DNS, and deployment decisions |
| `docs/RELEASE-CHECKS.md` | Which checks are active now and which to activate when |
| `CLAUDE.md` | Working instructions, including the content and security rules |
| `.claude/skills/` | Web skills installed from `claude-web-toolkit` |
| `.claude/skills-manifest.json` | Provenance for the installed skills |

## Installed skills

Copied from [`claude-web-toolkit`](https://github.com/AtalayDoganay/claude-web-toolkit) by its
installer, which recorded the source revision and a SHA-256 per file in
`.claude/skills-manifest.json`. Claude Code discovers them here automatically; the toolkit
checkout is not required.

| Skill | Use it when |
|---|---|
| `web-build` | Implementing or changing pages, components, or features |
| `web-design-review` | Reviewing typography, spacing, hierarchy, mobile behavior, accessibility |
| `web-security-review` | Reviewing the real attack surface before release or after adding routes, data, or dependencies |
| `web-release-check` | Running the project's real build, tests, and checks before shipping |

To update them, edit the skill in the toolkit, commit it, then re-run the toolkit's installer
with `-Update`. Do not hand-edit files under `.claude/skills/` — the installer will refuse to
update a modified copy, by design.

## Next step

Discuss visual direction and the project list. See the end of `docs/PROJECT-BRIEF.md`.
