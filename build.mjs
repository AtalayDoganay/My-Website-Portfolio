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
  'site.css',
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
 * The screen overlay is positioned from numbers the artwork measured, not from
 * numbers a human copied. tools/pixel_art.py writes the rectangle the tube occupies
 * on the pixel grid; this turns it into the custom properties the stylesheet uses.
 *
 * The old build refused to continue unless the screen was axis-aligned, which was
 * an assumption about one particular asset rather than a real invariant. What
 * actually matters is that the rectangle lies inside the artwork and has a sane
 * aspect, so that is what is checked now. A future asset drawn in perspective would
 * carry four corners instead, and the overlay would take a matrix - the geometry is
 * read from the asset either way.
 */
async function sceneVariables() {
  const meta = JSON.parse(await fs.readFile(join(SRC, 'assets', 'pixel', 'pixel.json'), 'utf8'));
  const { canvas, screen, screenFraction: f } = meta.machine;
  const compact = meta.machineCompact;

  const inside =
    screen.x >= 0 && screen.y >= 0 &&
    screen.x + screen.w <= canvas[0] && screen.y + screen.h <= canvas[1];
  if (!inside) {
    throw new Error(
      `The screen rectangle (${screen.x},${screen.y} ${screen.w}x${screen.h}) falls ` +
        `outside the ${canvas.join('x')} artwork, so the overlay would miss the glass.`,
    );
  }
  const aspect = screen.w / screen.h;
  if (aspect < 1.1 || aspect > 1.6) {
    throw new Error(`The screen is ${aspect.toFixed(2)}:1, which is not a tube shape.`);
  }

  // The tabletop is continued past the artwork by a CSS band, so the desk meets
  // both window edges instead of floating with wall showing past its ends. The
  // row structure is read from the asset; only the key-to-token map lives here,
  // and an unknown key is a build failure rather than a silently missing stripe.
  const DESK_TOKENS = {
    outline: '--outline',
    desk_top: '--desk-top',
    desk_front: '--desk-front',
    desk_edge: '--desk-edge',
  };
  const rowPx = (n) => (n === 0 ? '0' : `calc(${n} * var(--px-scale) * 1px)`);
  const deskBand = (desk, what) => {
    let at = 0;
    const stops = desk.rows.map(([n, key]) => {
      const token = DESK_TOKENS[key];
      if (!token) throw new Error(`The ${what} tabletop uses palette key "${key}", which has no CSS token.`);
      const from = at;
      at += n;
      return `var(${token}) ${rowPx(from)} ${rowPx(at)}`;
    });
    return { height: at, css: `linear-gradient(180deg, ${stops.join(', ')})` };
  };

  const pct = (n) => `${(n * 100).toFixed(4)}%`;
  const block = (c, r) => `  --screen-left: ${pct(r.left)};
  --screen-top: ${pct(r.top)};
  --screen-width: ${pct(r.width)};
  --screen-height: ${pct(r.height)};
  --art-width: ${c[0]};
  --art-height: ${c[1]};`;

  const wideBand = deskBand(meta.machine.desk, 'wide');
  const compactBand = deskBand(compact.desk, 'narrow');
  const deskBlock = (desk, band) => `  --desk-band-bottom: ${desk.fromBottom};
  --desk-band-height: ${band.height};
  --desk-band: ${band.css};`;

  return `/* ---------- generated from src/assets/pixel/pixel.json ---------- */
/* ${meta.generatedBy}
   wide framing    ${canvas.join(' x ')}, screen ${screen.w}x${screen.h} on the grid
   narrow framing  ${compact.canvas.join(' x ')}, screen ${compact.screen.w}x${compact.screen.h} */
.crt {
${block(canvas, f)}
}

.room {
${deskBlock(meta.machine.desk, wideBand)}
}

/* Narrow screens get their own framing, not a shrunken copy of the wide one. */
@media (max-width: 34rem), (max-height: 26rem) and (max-width: 44rem), (orientation: portrait) and (max-width: 48rem) {
  .crt {
${block(compact.canvas, compact.screenFraction)}
  }

  .room {
${deskBlock(compact.desk, compactBand)}
  }
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
