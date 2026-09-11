# Fonts

Self-hosted so the site makes no third-party requests at runtime. Both families are
licensed under the SIL Open Font License 1.1, which permits redistribution provided the
licence travels with the files — the `OFL-*.txt` files here are that licence.

Downloaded 2026-09-09 from the Google Fonts CDN (`fonts.gstatic.com`) via the
`fonts.googleapis.com/css2` API, which is how Google serves the subsetted `woff2` builds.

| File | Family | Axes | Subset | Source |
|---|---|---|---|---|
| `fraunces-latin.woff2` | Fraunces | `opsz` 9–144, `wght` 300–600 | latin | Google Fonts, Fraunces v38 |
| `fraunces-latin-ext.woff2` | Fraunces | same | latin-ext | Google Fonts, Fraunces v38 |
| `karla-latin.woff2` | Karla | `wght` 300–700 | latin | Google Fonts, Karla v33 |
| `karla-latin-ext.woff2` | Karla | same | latin-ext | Google Fonts, Karla v33 |
| `vt323-latin.woff2` | VT323 | single weight | latin | Google Fonts, VT323 v18 |
| `silkscreen-latin.woff2` | Silkscreen | single weight | latin | Google Fonts, Silkscreen v6 |

| Licence file | Covers | Copyright |
|---|---|---|
| `OFL-Fraunces.txt` | Fraunces | Copyright 2018 The Fraunces Project Authors — https://github.com/undercasetype/Fraunces |
| `OFL-Karla.txt` | Karla | Copyright 2019 The Karla Project Authors — https://github.com/googlefonts/karla |
| `OFL-VT323.txt` | VT323 | Copyright 2011 The VT323 Project Authors — peter.hull@oikoi.com |
| `OFL-Silkscreen.txt` | Silkscreen | Copyright 2001 The Silkscreen Project Authors — https://github.com/googlefonts/silkscreen |

The `unicode-range` values in `src/styles/typography.css` were taken from the same CSS
response, so each subset only loads for the characters it covers.

To update a font, fetch the new `woff2` from the same API, replace the file, refresh the
`unicode-range` values if they changed, and update the version in this table.
