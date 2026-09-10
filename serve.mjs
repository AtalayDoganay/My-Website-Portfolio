// Minimal static preview server for dist/. Local development only.
// No dependencies, no directory listing, no writes, no request logging of bodies.
import { createServer } from 'node:http';
import { createReadStream, promises as fs } from 'node:fs';
import { extname, join, normalize, resolve, sep } from 'node:path';

const ROOT = resolve('dist');
const PORT = Number(process.env.PORT) || 4321;
const HOST = '127.0.0.1';

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.webp': 'image/webp',
  '.woff2': 'font/woff2',
  '.ico': 'image/x-icon',
  '.txt': 'text/plain; charset=utf-8',
  '.webmanifest': 'application/manifest+json',
};

/** Resolve a URL path to a file inside ROOT, or null if it escapes or is missing. */
async function resolveFile(urlPath) {
  let decoded;
  try {
    decoded = decodeURIComponent(urlPath.split('?')[0].split('#')[0]);
  } catch {
    return null;
  }
  const candidate = resolve(join(ROOT, normalize(decoded)));
  if (candidate !== ROOT && !candidate.startsWith(ROOT + sep)) return null; // traversal guard
  try {
    const stat = await fs.stat(candidate);
    if (stat.isDirectory()) {
      const index = join(candidate, 'index.html');
      await fs.access(index);
      return index;
    }
    return candidate;
  } catch {
    return null;
  }
}

const server = createServer(async (req, res) => {
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    res.writeHead(405, { allow: 'GET, HEAD' }).end('Method not allowed');
    return;
  }
  let file = await resolveFile(req.url || '/');
  let status = 200;
  if (!file) {
    file = join(ROOT, '404.html');
    status = 404;
    try {
      await fs.access(file);
    } catch {
      res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' }).end('Not found');
      return;
    }
  }
  const type = TYPES[extname(file).toLowerCase()] || 'application/octet-stream';
  res.writeHead(status, {
    'content-type': type,
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff',
  });
  if (req.method === 'HEAD') return res.end();
  createReadStream(file).pipe(res);
});

server.listen(PORT, HOST, () => {
  console.log(`\n  Preview running at  http://${HOST}:${PORT}/`);
  console.log('  Serving ./dist       Press Ctrl+C to stop.\n');
});
