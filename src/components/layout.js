// The page shell.
//
// Two kinds of page share one <head>:
//   'site'      - the masthead, sky band, column and footer the inner pages use.
//                 These ship no JavaScript.
//   'immersive' - a single full-viewport composition with no site chrome at all.
//                 The home page uses this; it is the only page that loads a script.

import { esc, attrs, safeUrl } from '../lib/html.js';
import { nav, site } from '../data/site.js';
import { scene } from './scene.js';

const SCENE_LABEL =
  'An open doorway standing by itself in a wide meadow, lit from within, under slowly drifting clouds.';

const navList = (current) =>
  nav
    .map(({ label, href }) => {
      const active = href === current;
      return `<li><a${attrs({
        class: active ? 'nav__link nav__link--current' : 'nav__link',
        href: safeUrl(href, `nav item "${label}"`),
        'aria-current': active ? 'page' : null,
      })}>${esc(label)}</a></li>`;
    })
    .join('\n          ');

const head = ({ documentTitle, description, chrome, preloadCrt }) => `  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${esc(documentTitle)}</title>
  <meta name="description" content="${esc(description)}">
  <meta name="color-scheme" content="${chrome === 'immersive' ? 'dark' : 'light'}">
  <meta name="theme-color" content="${chrome === 'immersive' ? '#05060F' : '#C3D9E8'}">
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
${preloadCrt ? '  <link rel="preload" href="/assets/fonts/vt323-latin.woff2" as="font" type="font/woff2" crossorigin>\n' : ''}  <link rel="preload" href="/assets/fonts/karla-latin.woff2" as="font" type="font/woff2" crossorigin>
${preloadCrt ? '' : '  <link rel="preload" href="/assets/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossorigin>\n'}  <link rel="stylesheet" href="/styles.css">`;

/**
 * @param {{title: string, description: string, path: string,
 *          variant?: 'field'|'horizon', chrome?: 'site'|'immersive',
 *          script?: string, content: string}} page
 */
export function layout({
  title,
  description,
  path,
  variant = 'horizon',
  chrome = 'site',
  script = null,
  content,
}) {
  const isHome = path === '/';
  const documentTitle = isHome ? site.name : `${title} — ${site.name}`;

  if (chrome === 'immersive') {
    return `<!doctype html>
<html lang="en" class="immersive">
<head>
${head({ documentTitle, description, chrome, preloadCrt: true })}
${script ? `  <script src="${esc(safeUrl(script, 'page script'))}" defer></script>` : ''}
</head>
<body class="immersive__body">
  <main id="main">
${content}
  </main>
  <div class="grain grain--dark" aria-hidden="true"></div>
</body>
</html>
`;
  }

  return `<!doctype html>
<html lang="en">
<head>
${head({ documentTitle, description, chrome, preloadCrt: false })}
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>

  <div class="band band--${esc(variant)}">
    ${scene({ variant, label: SCENE_LABEL })}
    <header class="masthead">
      <div class="column masthead__inner">
        <a class="wordmark" href="/">${esc(site.name)}</a>
        <nav class="nav" aria-label="Primary">
          <ul class="nav__list">
          ${navList(path)}
          </ul>
        </nav>
      </div>
    </header>
  </div>

  <main class="column" id="main">
${content}
  </main>

  <footer class="site-foot">
    <div class="column site-foot__inner">
      <p class="site-foot__mark">&copy; ${site.year} ${esc(site.name)}</p>
      <p class="site-foot__aside"><a href="https://github.com/AtalayDoganay">GitHub</a></p>
    </div>
  </footer>

  <div class="grain" aria-hidden="true"></div>
</body>
</html>
`;
}
