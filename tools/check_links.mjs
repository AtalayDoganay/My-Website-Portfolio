// Every internal link and asset reference in dist/ must resolve to a file that exists,
// and every in-page fragment must match an id on the page that links to it.
// External links are listed, not fetched. Run: node tools/check_links.mjs

import { promises as fs } from 'node:fs';
import { join, relative, resolve } from 'node:path';

const OUT = 'dist';

async function htmlFiles(dir) {
  const found = [];
  for (const entry of await fs.readdir(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) found.push(...(await htmlFiles(path)));
    else if (entry.name.endsWith('.html')) found.push(path);
  }
  return found;
}

/** A root-relative URL maps to dist/<path>, with directories resolving to index.html. */
async function resolveTarget(urlPath) {
  const candidate = resolve(join(OUT, urlPath));
  for (const attempt of [candidate, join(candidate, 'index.html')]) {
    try {
      const stat = await fs.stat(attempt);
      if (stat.isFile()) return relative('.', attempt);
    } catch {
      /* try the next shape */
    }
  }
  return null;
}

const problems = [];
const external = new Set();
let checked = 0;

const pages = await htmlFiles(OUT);
if (pages.length === 0) problems.push('no HTML in dist/ - run npm run build first');

for (const page of pages) {
  const html = await fs.readFile(page, 'utf8');
  const ids = new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]));

  for (const m of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
    const raw = m[1];
    if (raw.startsWith('data:')) continue;
    checked += 1;

    if (/^https?:\/\//.test(raw)) {
      external.add(raw);
      continue;
    }
    if (raw.startsWith('mailto:')) continue;

    const [path, fragment] = raw.split('#');

    if (path === '') {
      // Same-page fragment.
      if (fragment && !ids.has(fragment)) problems.push(`${page}: #${fragment} has no matching id on this page`);
      continue;
    }
    if (!path.startsWith('/')) {
      problems.push(`${page}: ${raw} is not root-relative; the site is served from /`);
      continue;
    }

    const target = await resolveTarget(path);
    if (!target) {
      problems.push(`${page}: ${raw} -> no file at dist${path}`);
      continue;
    }
    if (fragment) {
      const targetHtml = target.endsWith('.html') ? await fs.readFile(target, 'utf8') : '';
      const targetIds = new Set([...targetHtml.matchAll(/\sid="([^"]+)"/g)].map((x) => x[1]));
      if (!targetIds.has(fragment)) problems.push(`${page}: ${raw} -> ${target} has no id="${fragment}"`);
    }
  }
}

console.log(`link check: ${checked} references across ${pages.length} pages`);
if (external.size) {
  console.log(`\nexternal links (listed, not fetched - no checker is configured):`);
  for (const url of [...external].sort()) console.log(`  ${url}`);
}

if (problems.length) {
  console.error(`\n${problems.length} problem(s):`);
  for (const p of problems) console.error(`  ${p}`);
  process.exit(1);
}
console.log('\nall internal links and fragments resolve');
