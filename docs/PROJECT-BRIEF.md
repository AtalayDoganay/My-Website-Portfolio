# atalaydoganay.com — project brief

**Status: a first working local version exists.** Four pages build and run on a local
preview server. Nothing is hosted or deployed, the domain is not registered or connected,
and no content here has been published.

Written 2026-09-09. Updated the same day, when the first version was built.

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

## Design direction — chosen 2026-09-09

Atalay chose **dreamcore**: a quiet, nostalgic, slightly surreal place, built around a
single atmospheric scene — a lit doorway standing alone in a meadow under drifting cloud.
Faded sky blue, misty lavender, muted meadow green, soft ivory. See `docs/DESIGN-NOTES.md`
for the palette, type, motion and the reasoning behind each.

**Updated 2026-09-10:** the home page was redesigned around an interactive early-2000s
computer - dreamcore, cyberpunk lighting and Windows nostalgia - which you click into to
reach a desktop. The desktop's portfolio surface is the next piece of work. The inner
pages keep the light meadow design described here. See `docs/DESIGN-NOTES.md`.

The structural reference was the contact page at `phillipche.com`: narrow centred column,
compact horizontal navigation, thin-bordered cards, generous negative space. Structure only
— no branding, colour, type, imagery or copy was taken from it.

What was already agreed, and still holds:

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

### Stack — chosen 2026-09-09

**A static site with a small zero-dependency build step.** `package.json` has no
dependencies of any kind, production or development.

- Pages are small ES modules under `src/pages/` that return HTML strings; `src/data/site.js`
  holds all the content in one place; `build.mjs` (about 90 lines) renders them to `dist/`,
  concatenates the stylesheets and copies assets. `serve.mjs` is a preview server.
- Why not a framework: the site is four static pages with no interactivity. A generator
  would add a few hundred transitive packages to produce the same output, and every one of
  those is supply-chain surface on a repository whose stated policy is to add a dependency
  only when the work needs it.
- Why not four hand-written HTML files: navigation, layout, and project presentation are
  shared, and duplicating them across four files is how they drift apart.
- **The site ships no JavaScript.** Nothing on it needs any.

Provisional in the sense that Atalay has not reviewed it yet; it is easy to move off, since
the output is plain HTML and CSS.

## Unresolved: hosting, domain, DNS, deployment

**None of this exists.** Creating this repository did not register the domain, connect it, or
deploy anything. See `docs/HOSTING-DECISIONS.md` for the open decisions. No account was
created, nothing was purchased, and nothing was deployed during setup.

## Next action

Atalay reviews the local preview. The open items are listed under "Missing material" in
`docs/CONTENT-SOURCES.md` — screenshots for both projects, whether a contact email or any
other account should appear, release status, and sign-off on the project write-ups.

Hosting remains unresolved; see `docs/HOSTING-DECISIONS.md`. Nothing should be deployed
until Atalay asks for it.
