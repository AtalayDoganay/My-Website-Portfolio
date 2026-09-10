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

async function copyDir(from, to) {
  await fs.mkdir(to, { recursive: true });
  for (const entry of await fs.readdir(from, { withFileTypes: true })) {
    const src = join(from, entry.name);
    const dest = join(to, entry.name);
    if (entry.isDirectory()) await copyDir(src, dest);
    else await fs.copyFile(src, dest);
  }
}

/**
 * The interactive screen is an HTML element laid over an aperture drawn in SVG.
 * Two files therefore hold the same four numbers, and a silent drift between them
 * would slide the hit area off the glass without anything failing. Check it.
 */
async function checkScreenBox() {
  const { SCREEN_BOX } = await import(
    `${pathToFileURL(join(process.cwd(), SRC, 'components', 'room.js')).href}?v=${Date.now()}`
  );
  const css = await fs.readFile(join(SRC, 'styles', 'room.css'), 'utf8');
  const expected = {
    '--screen-left': SCREEN_BOX.left,
    '--screen-top': SCREEN_BOX.top,
    '--screen-width': SCREEN_BOX.width,
    '--screen-height': SCREEN_BOX.height,
  };
  for (const [prop, value] of Object.entries(expected)) {
    const found = css.match(new RegExp(`${prop}:\\s*([\\d.]+)%`));
    if (!found) throw new Error(`room.css is missing ${prop}`);
    if (Math.abs(Number(found[1]) - value) > 0.01) {
      throw new Error(
        `Screen aperture drift: room.css has ${prop}: ${found[1]}% but room.js computes ` +
          `${value.toFixed(4)}%. The interactive screen would not sit on the drawn glass.`,
      );
    }
  }
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

  await checkScreenBox();
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
