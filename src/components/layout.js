// The page shell every page shares: head, masthead, sky band, main, footer.
// Ships no JavaScript. Nothing on this site needs it.

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

/**
 * @param {{title: string, description: string, path: string,
 *          variant?: 'field'|'horizon', content: string}} page
 */
export function layout({ title, description, path, variant = 'horizon', content }) {
  const isHome = path === '/';
  const documentTitle = isHome ? site.name : `${title} — ${site.name}`;

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${esc(documentTitle)}</title>
  <meta name="description" content="${esc(description)}">
  <meta name="color-scheme" content="light">
  <meta name="theme-color" content="#C3D9E8">
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <link rel="preload" href="/assets/fonts/fraunces-latin.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/assets/fonts/karla-latin.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/styles.css">
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
