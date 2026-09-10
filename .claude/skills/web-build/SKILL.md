---
name: web-build
description: Use when implementing or changing pages, components, or features on a website - inspects the existing stack and design system first, then builds scoped semantic, responsive HTML/CSS/JS with minimal dependencies.
---

# web-build

Build scoped website work that fits the project already in front of you.

## Inspect before writing

Never assume the stack. Establish, from the repository itself:

- Build tooling and framework: package manifest, lockfile, config files, or plain static files.
- Where pages, components, styles, and assets actually live.
- The existing design system: type scale, spacing units, color tokens, breakpoints, motion conventions.
- Project instructions (`CLAUDE.md`, `README.md`, `docs/`) and any lasting requirements they set.

If the project has no application manifest yet, say so and build static files rather than inventing a toolchain.

## Implement

- Scope the change to what was asked. Do not redesign unrelated pages.
- Semantic HTML: real landmarks, headings in order, `button` for actions and `a` for navigation, labelled form controls.
- Responsive by default. Verify narrow widths (~360-400px) as well as desktop; no horizontal page scroll.
- Reuse the established design tokens. If the project has none and the work needs them, propose a small set and record it rather than scattering literals.
- Add a dependency only when the work genuinely needs it. Prefer platform features. Note what a new dependency costs in bundle size and maintenance.
- Keep content honest. Do not invent copy that states facts about the owner, their projects, or their metrics; use clearly marked placeholders and ask.

## Finish the states, not just the happy path

When a feature has meaningful interaction, implement and check:

- Empty state, loading state, and error state.
- Keyboard operation and visible focus for anything interactive.
- What happens when content is longer or shorter than the mockup assumed.

## Verify

Run the project's real build and checks if they exist, and report their actual output. Open or render the changed page and confirm the change appears. Do not describe a layout as verified when you only read the source.

Related: `web-design-review` for a critique pass, `web-release-check` before shipping.
