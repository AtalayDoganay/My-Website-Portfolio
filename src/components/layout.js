// The page shell.
//
// Two kinds of page share one <head>:
//   'site'      - the masthead, column and footer the inner pages use
//   'immersive' - a single full-viewport composition with no site chrome at all
//
// Every page loads /theme.js synchronously in the head. It is a blocking request
// for a very small file, and it is what stops the wrong theme being painted for a
// frame before JavaScript catches up. It also binds the theme toggles by
// delegation, so the inner pages get a working switch without a second script.

import { esc, attrs, safeUrl } from '../lib/html.js';
import { nav, site } from '../data/site.js';
import { themeToggle } from './pixel.js';

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
    .join('\n            ');

const head = ({ documentTitle, description, preload }) => `  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>${esc(documentTitle)}</title>
  <meta name="description" content="${esc(description)}">
  <meta name="color-scheme" content="dark light">
  <meta name="theme-color" content="#070A18">
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
${preload.map((f) => `  <link rel="preload" href="/assets/fonts/${f}" as="font" type="font/woff2" crossorigin>`).join('\n')}
  <script src="/theme.js"></script>
  <link rel="stylesheet" href="/styles.css">`;

/**
 * @param {{title: string, description: string, path: string,
 *          chrome?: 'site'|'immersive', script?: string, content: string}} page
 */
export function layout({ title, description, path, chrome = 'site', script = null, content }) {
  const isHome = path === '/';
  const documentTitle = isHome ? site.name : `${title} — ${site.name}`;

  if (chrome === 'immersive') {
    return `<!doctype html>
<html lang="en" class="immersive">
<head>
${head({ documentTitle, description, preload: ['vt323-latin.woff2', 'silkscreen-latin.woff2'] })}
${script ? `  <script src="${esc(safeUrl(script, 'page script'))}" defer></script>` : ''}
</head>
<body class="immersive__body">
  <main id="main">
${content}
  </main>
</body>
</html>
`;
  }

  return `<!doctype html>
<html lang="en">
<head>
${head({ documentTitle, description, preload: ['silkscreen-latin.woff2', 'karla-latin.woff2'] })}
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>

  <div class="band">
    <header class="masthead">
      <div class="column masthead__inner">
        <a class="wordmark" href="/">${esc(site.name)}</a>
        <div class="masthead__end">
          <nav class="nav" aria-label="Primary">
            <ul class="nav__list">
            ${navList(path)}
            </ul>
          </nav>
          ${themeToggle({ className: 'theme-toggle--bar' })}
        </div>
      </div>
    </header>
    <div class="band__scene" aria-hidden="true">
      <span class="band__sky"></span>
      <span class="band__ridge band__ridge--far"></span>
      <span class="band__ridge band__ridge--near"></span>
      <span class="band__door"></span>
    </div>
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
</body>
</html>
`;
}
