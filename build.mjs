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

  written.push(await write('styles.css', await buildStyles()));
  await copyDir(join(SRC, 'assets'), join(OUT, 'assets'));
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
