// Static site build. Renders src/pages/*.js to dist/, concatenates styles, copies assets.
// No dependencies by design: see docs/PROJECT-BRIEF.md for the reasoning.
import { promises as fs } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { pathToFileURL } from 'node:url';

const SRC = 'src';
const OUT = 'dist';

/** Style sheets are concatenated in this order into one styles.css. */
const STYLE_ORDER = [
  'tokens.css',
  'base.css',
  'typography.css',
  'layout.css',
  'scene.css',
  'components.css',
  'room.css',
  'desktop.css',
];

const PAGES = [
  { module: 'index.js', out: 'index.html' },
  { module: 'projects.js', out: 'projects/index.html' },
  { module: 'about.js', out: 'about/index.html' },
  { module: 'contact.js', out: 'contact/index.html' },
  { module: 'not-found.js', out: '404.html' },
];

async function write(relPath, contents) {
  const target = join(OUT, relPath);
  await fs.mkdir(dirname(target), { recursive: true });
  await fs.writeFile(target, contents);
  return target;
}

// Build inputs that live beside the assets but must never be served: the lossless
// render master is 2.6 MB and the browser only ever wants the WebP exports.
const NOT_SHIPPED = new Set(['crt.png']);

async function copyDir(from, to) {
  await fs.mkdir(to, { recursive: true });
  for (const entry of await fs.readdir(from, { withFileTypes: true })) {
    if (NOT_SHIPPED.has(entry.name)) continue;
    const src = join(from, entry.name);
    const dest = join(to, entry.name);
    if (entry.isDirectory()) await copyDir(src, dest);
    else await fs.copyFile(src, dest);
  }
}

/**
 * The screen overlay is positioned from numbers the renderer measured, not from
 * numbers a human copied. tools/model_crt.py writes the rectangle the tube occupies
 * in the rendered image; this turns it into custom properties the stylesheet uses.
 *
 * It also enforces the one assumption the overlay rests on: that the renderer's
 * camera was level, so the screen projects as an axis-aligned rectangle. If a future
 * camera change tilts it, the rectangle would no longer match the glass and the text
 * would sit crooked on it - so the build stops instead.
 */
async function sceneVariables() {
  const meta = JSON.parse(await fs.readFile(join(SRC, 'assets', 'scene', 'crt.json'), 'utf8'));
  const { glass, clip } = meta.screen;

  const skew = Math.max(glass.skew_x, glass.skew_y);
  if (skew > 0.05) {
    throw new Error(
      `The rendered screen is not axis-aligned (skew ${skew.toFixed(3)}%). The camera ` +
        `must stay level, or the overlay needs a perspective transform instead of a rect.`,
    );
  }

  const pct = (n) => `${n.toFixed(4)}%`;
  // Unitless fractions as well as percentages: percentages place the overlay inside
  // the asset, fractions let a narrow layout solve "put the screen's centre here"
  // arithmetically instead of by eye.
  const cx = (glass.left + glass.width / 2) / 100;
  const cy = (glass.top + glass.height / 2) / 100;
  const aspect = meta.assetPixels[0] / meta.assetPixels[1];
  return `/* ---------- generated from src/assets/scene/crt.json ---------- */
/* ${meta.renderer}, ${meta.samples} samples, asset ${meta.assetPixels.join(' x ')} px */
.crt {
  --screen-left: ${pct(glass.left)};
  --screen-top: ${pct(glass.top)};
  --screen-width: ${pct(glass.width)};
  --screen-height: ${pct(glass.height)};
  /* how much of the tube the front moulding hides, as a clip on the overlay */
  --screen-clip-top: ${pct(clip.top)};
  --screen-clip-right: ${pct(clip.right)};
  --screen-clip-bottom: ${pct(clip.bottom)};
  --screen-clip-left: ${pct(clip.left)};

  /* the centre of the glass within the asset, and the asset's own aspect */
  --screen-cx: ${cx.toFixed(6)};
  --screen-cy: ${cy.toFixed(6)};
  --crt-aspect: ${aspect.toFixed(6)};
}
`;
}

async function buildStyles() {
  const parts = [];
  for (const name of STYLE_ORDER) {
    const path = join(SRC, 'styles', name);
    parts.push(`/* ---------- ${name} ---------- */\n${await fs.readFile(path, 'utf8')}`);
  }
  const all = await fs.readdir(join(SRC, 'styles'));
  const missed = all.filter((f) => f.endsWith('.css') && !STYLE_ORDER.includes(f));
  if (missed.length) throw new Error(`Stylesheet not listed in STYLE_ORDER: ${missed.join(', ')}`);
  parts.push(await sceneVariables());
  return parts.join('\n\n');
}

async function build() {
  const started = Date.now();
  await fs.rm(OUT, { recursive: true, force: true });

  const written = [];
  for (const page of PAGES) {
    const url = pathToFileURL(join(process.cwd(), SRC, 'pages', page.module)).href;
    // Cache-bust so --watch picks up edits.
    const mod = await import(`${url}?v=${Date.now()}`);
    if (typeof mod.render !== 'function') throw new Error(`${page.module} must export render()`);
    written.push(await write(page.out, mod.render()));
  }

  written.push(await write('styles.css', await buildStyles()));
  await copyDir(join(SRC, 'assets'), join(OUT, 'assets'));

  // Client scripts are copied verbatim: no bundler, no transform, nothing minified
  // into something that cannot be read in the browser's sources panel.
  const scriptDir = join(SRC, 'scripts');
  if (await fs.stat(scriptDir).then(() => true, () => false)) {
    for (const name of await fs.readdir(scriptDir)) {
      if (name.endsWith('.js')) written.push(await write(name, await fs.readFile(join(scriptDir, name))));
    }
  }
  for (const extra of ['robots.txt']) {
    const path = join(SRC, extra);
    if (await fs.stat(path).then(() => true, () => false)) written.push(await write(extra, await fs.readFile(path)));
  }

  console.log(`built ${written.length} files in ${Date.now() - started}ms`);
  for (const f of written) console.log(`  ${relative('.', f)}`);
}

await build();

if (process.argv.includes('--serve')) {
  await import('./serve.mjs');
}

if (process.argv.includes('--watch')) {
  const { watch } = await import('node:fs');
  let queued = null;
  watch(SRC, { recursive: true }, () => {
    clearTimeout(queued);
    queued = setTimeout(() => build().catch((err) => console.error('build failed:', err.message)), 120);
  });
  console.log(`\nwatching ${SRC}/ for changes`);
}
