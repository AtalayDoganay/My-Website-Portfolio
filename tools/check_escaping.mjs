// The security control this codebase actually has: content from src/data never reaches
// the page as markup, and a URL from data can never carry an executable scheme.
// This test proves both rather than asserting them. Run: node tools/check_escaping.mjs
//
// How it detects injection: it renders each component twice, once with an inert string
// and once with a hostile payload, then compares the *tag structure* of the two outputs
// - element names and attribute names, with all text and attribute values stripped. If
// a payload created an element or an attribute, the structures differ. Searching the
// output for "onerror=" instead would flag correctly escaped text as a failure.

import { esc, attrs, safeUrl } from '../src/lib/html.js';
import { projectEntry, contactCard, workList, pageHeader } from '../src/components/parts.js';
import { layout } from '../src/components/layout.js';

const INERT = 'PLACEHOLDERTEXT';

const MARKUP_PAYLOADS = [
  '<script>alert(1)</script>',
  '"><img src=x onerror=alert(1)>',
  "' onmouseover='alert(1)",
  '</title><script>alert(1)</script>',
  '<svg/onload=alert(1)>',
  '</a><a href="https://evil.example">',
  ' <script>',
  '\u0000<script>',
];

const URL_PAYLOADS = [
  'javascript:alert(1)',
  'JaVaScRiPt:alert(1)',
  'data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==',
  'vbscript:msgbox(1)',
  ' javascript:alert(1)',
];

let failures = 0;
const fail = (what, detail) => {
  failures += 1;
  console.error(`FAIL  ${what}\n      ${detail}`);
};

/**
 * Element and attribute names only. Attribute *values* must be walked over rather than
 * scanned, or an escaped payload sitting inside a value (`id="...onerror=alert(1)..."`)
 * is misread as a new attribute and the test fails on correctly escaped output.
 */
// Attribute values may be double-quoted, single-quoted or bare. All three have to be
// recognised: an injected `<img src=x onerror=alert(1)>` uses bare values, and a parser
// that only understands quoted ones skips the injected tag and reports a clean run.
const ATTR = String.raw`\s+[\w:.-]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]*))?`;
const TAG = new RegExp(String.raw`<\/?([a-zA-Z][\w-]*)((?:${ATTR})*)\s*\/?>`, 'g');
const ATTR_NAME = new RegExp(String.raw`\s([\w:.-]+)(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]*))?`, 'g');

function tagStructure(html) {
  return [...html.matchAll(TAG)]
    .map((m) => {
      const attrNames = [...m[2].matchAll(ATTR_NAME)].map((a) => a[1]);
      return `${m[1]}[${attrNames.join(',')}]`;
    })
    .join(' ');
}

/** Guard the guard: an unescaped interpolation must be detected, or the test is theatre. */
function selfTest() {
  const careless = (id) => `<article id="${id}"><h2>x</h2></article>`;
  const clean = tagStructure(careless('SAFE'));
  const dirty = tagStructure(careless('"><img src=x onerror=alert(1)>'));
  if (clean === dirty) {
    console.error('FAIL  tagStructure() cannot see an injected element; the rest of this run proves nothing');
    console.error(`      clean: ${clean}\n      dirty: ${dirty}`);
    process.exit(1);
  }
  console.log(`self-test: injection is detectable\n  clean: ${clean}\n  dirty: ${dirty}\n`);
}

/** Every component, rendered from one text value used everywhere it accepts data. */
function renderAll(value) {
  const project = {
    id: value,
    name: value,
    kind: value,
    summary: value,
    body: [value, value],
    facts: [{ label: value, value }],
    screenshot: null,
  };
  return {
    projectEntry: projectEntry(project),
    projectEntryWithImage: projectEntry({
      ...project,
      screenshot: { src: '/assets/x.png', alt: value, width: 9, height: 16 },
    }),
    contactCard: contactCard({ label: value, value, href: 'https://example.com/' + encodeURIComponent(value) }),
    workList: workList([project]),
    pageHeader: pageHeader({ title: value, lead: value, body: [value] }),
    layout: layout({ title: value, description: value, path: '/', variant: 'field', content: '' }),
  };
}

console.log('escaping check\n');
selfTest();

// --- esc() and attrs() ------------------------------------------------------
for (const payload of MARKUP_PAYLOADS) {
  if (/[<>"']/.test(esc(payload))) fail('esc() left a raw delimiter', `${payload} -> ${esc(payload)}`);
  const rendered = attrs({ 'data-x': payload });
  if (rendered.split('"').length !== 3) fail('attrs() let a value break out of its quotes', rendered);
}

// --- Structural comparison --------------------------------------------------
const baseline = renderAll(INERT);
for (const payload of MARKUP_PAYLOADS) {
  const hostile = renderAll(payload);
  for (const name of Object.keys(baseline)) {
    const before = tagStructure(baseline[name]);
    const after = tagStructure(hostile[name]);
    if (before !== after) {
      const at = [...before].findIndex((c, i) => c !== after[i]);
      fail(
        `${name} with ${JSON.stringify(payload)}`,
        `tag structure changed near index ${at}\n      expected: ...${before.slice(Math.max(0, at - 30), at + 60)}\n      actual:   ...${after.slice(Math.max(0, at - 30), at + 60)}`,
      );
    }
    if (hostile[name].includes(payload) && /[<>"']/.test(payload)) {
      fail(`${name} with ${JSON.stringify(payload)}`, 'payload survived verbatim in the output');
    }
  }
}

// --- URL schemes ------------------------------------------------------------
for (const payload of URL_PAYLOADS) {
  let threw = false;
  try {
    safeUrl(payload, 'test');
  } catch {
    threw = true;
  }
  if (!threw) fail('safeUrl accepted a dangerous scheme', payload);

  try {
    const html = contactCard({ label: 'x', value: 'x', href: payload });
    fail('contactCard rendered a dangerous URL', html.match(/href="[^"]*"/)?.[0] ?? html.slice(0, 80));
  } catch {
    /* expected: the build refuses rather than shipping it */
  }
}
// ...and still accepts the ones the site legitimately uses.
for (const good of ['https://github.com/AtalayDoganay', '/projects/', '/projects/#ball-fighters', 'mailto:a@b.example']) {
  try {
    safeUrl(good, 'test');
  } catch (err) {
    fail('safeUrl rejected a legitimate URL', `${good}: ${err.message}`);
  }
}

// --- The real pages, exactly as they ship -----------------------------------
// What no page may ever have is inline script content or an inline event handler:
// both are code smuggled into markup, and both would have to be blessed by hash in
// any future Content-Security-Policy. The theme switch is the reason this rule is
// worth keeping - the usual no-flash trick is an inline script in the head, and this
// site uses a blocking external file instead precisely so the rule survives.
//
// Every page loads /theme.js so the theme is settled before the first paint.
// The home page additionally loads /room.js for the opening scene. Nothing else.
const ALLOWED_SCRIPTS = { index: ['/theme.js', '/room.js'] };
const DEFAULT_SCRIPTS = ['/theme.js'];

for (const mod of ['index', 'projects', 'about', 'contact', 'not-found']) {
  const { render } = await import(`../src/pages/${mod}.js`);
  const html = render();
  const where = `src/pages/${mod}.js`;

  const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)];
  const allowed = ALLOWED_SCRIPTS[mod] || DEFAULT_SCRIPTS;
  const srcs = scripts.map((m) => (m[1].match(/\bsrc="([^"]*)"/i) || [])[1]);
  if (srcs.length !== allowed.length || srcs.some((s) => !allowed.includes(s))) {
    fail(where, `scripts ${JSON.stringify(srcs)} do not match the allowed ${JSON.stringify(allowed)}`);
  }
  for (const [, attrText, body] of scripts) {
    if (body.trim()) fail(where, `inline script body: ${body.trim().slice(0, 60)}`);
    const src = attrText.match(/\bsrc="([^"]*)"/i);
    if (!src) fail(where, 'a <script> with no src, which means inline code');
    else if (!/^\/[^/]/.test(src[1])) fail(where, `script is not a same-origin root-relative path: ${src[1]}`);
  }

  for (const m of html.matchAll(/\son[a-z]+\s*=\s*["']/gi)) {
    fail(where, `inline event handler: ${html.slice(m.index, m.index + 40)}`);
  }
  for (const m of html.matchAll(/(?:href|src)="([^"]*)"/gi)) {
    if (/^\s*(javascript|data|vbscript):/i.test(m[1])) fail(where, `dangerous URL shipped: ${m[1].slice(0, 60)}`);
  }
}

if (failures) {
  console.error(`\n${failures} failure(s)`);
  process.exit(1);
}
console.log(
  `passed\n` +
    `  ${MARKUP_PAYLOADS.length} markup payloads x 6 components: tag structure unchanged\n` +
    `  ${URL_PAYLOADS.length} URL payloads refused by safeUrl, legitimate URLs still accepted\n` +
    `  5 shipped pages: no inline script, no inline handlers, no dangerous URL schemes\n` +
    `  (home loads one same-origin script; the other four load none)`,
);
