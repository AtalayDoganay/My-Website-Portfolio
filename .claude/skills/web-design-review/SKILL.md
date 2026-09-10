---
name: web-design-review
description: Use when reviewing or improving the visual and accessibility quality of web pages - evaluates typography, spacing, hierarchy, mobile behavior, keyboard access, contrast, and reduced motion, and produces prioritized findings.
---

# web-design-review

Critique a real page, then fix what was requested.

## Look at the actual rendered page

Review the page as rendered, not as source. If browser tooling is available, capture screenshots at a narrow width (~390px) and a desktop width, and attach them to the findings. If it is not available, say that the review is source-only and that visual defects may be missed.

## What to evaluate

**Typography** - type scale is deliberate and consistent; line length is readable (roughly 60-80 characters for body text); line height suits the size; font weights carry hierarchy instead of decorating it.

**Spacing and layout** - spacing comes from a consistent scale; related items are grouped by proximity; alignment is intentional; the page has breathing room at both ends of the width range.

**Hierarchy** - the most important element on each screen is the most prominent. Heading levels are ordered and meaningful, not chosen for size.

**Mobile behavior** - no horizontal scroll; gutters hold at every width; touch targets are large enough (~44px); nothing is clipped, overlapped, or reflowed into nonsense when rows wrap.

**Keyboard and focus** - every interactive element is reachable by Tab in a sensible order; focus is clearly visible against its background; nothing traps focus.

**Labels and semantics** - form controls have real labels; images have appropriate alt text (empty for decorative); icon-only buttons have accessible names; landmarks exist.

**Contrast** - body text meets 4.5:1 and large text 3:1 against its actual background, in every theme the page supports. Check computed colors, not intended ones.

**Motion** - animation supports comprehension rather than decorating; `prefers-reduced-motion` is respected for anything non-essential.

## Report

Produce prioritized observations, worst first. For each: what it is, where (file and line, or a screenshot), why it matters, and the smallest fix. Separate real defects from matters of taste, and say which is which.

## Fix and verify

Fix only what was requested. After fixing, re-render and confirm the specific issue is resolved. State what you verified and how.
