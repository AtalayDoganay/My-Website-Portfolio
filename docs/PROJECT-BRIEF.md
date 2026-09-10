# atalaydoganay.com — project brief

**Status: setup only.** Nothing is designed, implemented, hosted, or deployed. This brief
exists so a later session can start work without re-deriving the goals.

Written 2026-09-09.

## Purpose

A personal portfolio site for Atalay Doganay, useful to two audiences:

1. **Employers and recruiters** — who this person is, what they can build, evidence, how to reach them.
2. **People interested in the projects themselves** — what each project is, why it is interesting, how to try it.

Both should be served by the same pages. A visitor should understand what Atalay builds
within a few seconds of landing, and be able to go deeper on any single project.

## Confirmed content

These facts are confirmed and may be written as-is:

- Name: **Atalay Doganay**
- **Computer Science student at Cal Poly Pomona**
- **Associate in Science in Computer Science, Orange Coast College**
- Interests: **software engineering** and **indie game development**
- Domain target: **atalaydoganay.com**
- GitHub account: **AtalayDoganay**

## Candidate projects — require verification before publishing

Two candidates. Neither is cleared for public claims yet.

### BALL FIGHTERS

A portrait browser auto-battler (repository: `Game-For-Insta`). Verified read-only during
setup: portrait 480x854, vanilla JavaScript, runs from `file://` by opening `index.html`.

Needs verification before anything is published:

- [ ] Public description Atalay is happy with
- [ ] Whether the repository is or should be public
- [ ] Whether it is playable via a link, or download-only
- [ ] Screenshots or a short capture cleared for publication
- [ ] Release status (in progress / playable / released)
- [ ] Asset licenses and any third-party content credits

### Student class-reminder app

A class-schedule/reminder app (a local `Class-schedule-app` folder exists).

Needs verification before anything is published:

- [ ] What it does, in Atalay's own words
- [ ] Platform and stack
- [ ] Whether it was solo or a team project, and if a team, what Atalay's contribution was
- [ ] Release status and whether it is usable by anyone else
- [ ] Screenshots cleared for publication
- [ ] Whether it should appear publicly at all

**Do not write around a gap.** If a detail is unverified, ask, or leave a clearly marked
placeholder. An invented feature list is worse than a short honest one.

## Planned sections

1. **Introduction** — name, what he builds, and a reason to keep reading. No filler tagline.
2. **Selected projects** — each with its own explanation, not a uniform card grid of one-liners. Say what it is, what was hard, and what it demonstrates.
3. **About / education** — Cal Poly Pomona, Orange Coast College, interests.
4. **Contact / resume** — only the public versions Atalay provides.

## Design direction

Deliberately open. **Do not commit to a visual theme before discussing preferences with
Atalay** — that conversation is the first step of the next phase.

What is already agreed:

- Intentional typography. A real type scale, chosen deliberately, not framework defaults.
- Polished mobile layout, treated as a first-class case rather than a fallback.
- Restrained animation that supports content and respects `prefers-reduced-motion`.
- Distinctive rather than templated. It should not read as a generic starter theme.

Undecided and to be discussed: color, mood, light/dark, layout structure, typeface pairing,
imagery, whether the tone leans engineering or game-development.

## Hard rules for content

Do not invent, imply, or placeholder-as-if-real any of:

- Employers, job titles, internships, or dates of employment
- Metrics ("10,000 users", "40% faster")
- Testimonials, references, awards, certifications
- Project URLs, demo links, download counts, store listings
- Skills or technologies not confirmed by Atalay
- A contact email address

Also excluded: private personal information (home address, phone number, student ID, date of
birth), and any resume — **publishing a resume is not authorized**; a public version must be
provided by Atalay explicitly.

## Technical direction

Prefer a **static site**: no login, no database, no server-side contact handler, unless a
requested feature genuinely needs one. This is a deliberate security decision as much as a
simplicity one — a static portfolio has almost no attack surface, and every added service
adds some.

For a contact route, prefer a `mailto:` link or a linked profile over a form that requires a
backend. If a form is later wanted, that decision reopens server-side validation, spam
handling, rate limiting, and data storage — treat it as a real feature with a real review.

Stack is not chosen. Decide it with Atalay at the start of the implementation phase, and
record the decision here.

## Unresolved: hosting, domain, DNS, deployment

**None of this exists.** Creating this repository did not register the domain, connect it, or
deploy anything. See `docs/HOSTING-DECISIONS.md` for the open decisions. No account was
created, nothing was purchased, and nothing was deployed during setup.

## Next action

Discuss visual direction and the project list with Atalay. Specifically: which two or three
projects appear, what each one is allowed to claim, and the design preferences that are
currently open. Then choose a stack and record it here.
