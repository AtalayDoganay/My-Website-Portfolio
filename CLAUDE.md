# atalaydoganay.com — working instructions

Personal portfolio site for Atalay Doganay. **Current state: setup only.** No design, no
implementation, no hosting, no deployment.

Read `docs/PROJECT-BRIEF.md` before doing any work here. It holds the goals, the confirmed
facts, and what still needs verifying.

## Content rules (these are the important ones)

Everything published here is a public claim about a real person's background. Getting it
wrong is worse than leaving it out.

**Never invent or imply:** employers, job titles, internships, employment dates, metrics,
testimonials, references, awards, certifications, project URLs, demo links, download counts,
skills, technologies, or a contact email.

**Never publish:** private personal information (home address, phone number, student ID, date
of birth), or any resume. Publishing a resume is not authorized; only a public version Atalay
explicitly provides may be linked.

**Confirmed and safe to write:** Atalay Doganay; Computer Science student at Cal Poly Pomona;
Associate in Science in Computer Science from Orange Coast College; interests in software
engineering and indie game development.

**Project details are not confirmed.** BALL FIGHTERS and the student class-reminder app are
candidates. Their features, links, screenshots, release status, and contribution details all
need verification before a public claim is written. If a detail is missing, ask or leave a
clearly marked placeholder — do not write plausible filler.

## Design

Do not lock in a visual theme before discussing preferences with Atalay. Agreed already:
intentional typography, polished mobile layout, restrained animation respecting
`prefers-reduced-motion`, and a distinctive rather than templated result. Color, mood, and
layout structure are open.

## Technical constraints

- **Static by default.** No login, no database, no server-side contact handler unless a
  requested feature genuinely needs one. Every added service adds attack surface.
- Add a dependency only when the work needs it. Prefer platform features.
- No secrets in this repository, ever — not in code, config, committed history, screenshots,
  or client-side bundles. Only `.env.example` style placeholders belong here.
  `.gitignore` does not protect a secret that has already been committed; such a secret is
  disclosed and must be rotated.
- Handle any untrusted content safely: no raw HTML injection, no `eval` or dynamic script
  construction from data.

## Hosting and deployment

Unresolved — see `docs/HOSTING-DECISIONS.md`. Do not create accounts, register the domain, or
deploy. CSP and other response headers must be derived from the chosen platform and the real
assets, then verified against the live response. A committed config file is not a live header.

**Do not deploy without an explicit request.**

## Honesty about status

Never state that the site is deployed, live, connected to the domain, or secure. Setup
existing is not a site existing. A committed workflow is not a passing run; a passing check is
not a branch rule requiring it; a scanner finding nothing is not proof of security.

## Skills

`.claude/skills/` holds copies installed from `claude-web-toolkit`, with provenance in
`.claude/skills-manifest.json`. They are guidance, not enforcement — do not rely on a model
remembering to invoke the security skill. Lasting requirements belong in this file, and
mechanical checks belong in CI once there is an application to check. See
`docs/RELEASE-CHECKS.md`.

Do not hand-edit files under `.claude/skills/`. The installer will refuse to update a
modified copy — change it in the toolkit and reinstall with `-Update`.
