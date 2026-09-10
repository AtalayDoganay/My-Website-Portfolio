// Escaping helpers. All content from src/data is plain text and passes through esc()
// before it reaches the page: no template in this project ever interpolates raw HTML.

const ENTITIES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

/** Escape text for use in element content or a double-quoted attribute value. */
export const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ENTITIES[c]);

/** Build an attribute list, skipping null/undefined/false values. */
export const attrs = (map) =>
  Object.entries(map)
    .filter(([, v]) => v !== null && v !== undefined && v !== false)
    .map(([k, v]) => (v === true ? ` ${k}` : ` ${k}="${esc(v)}"`))
    .join('');

/** Join template fragments, dropping empty ones, with a newline between. */
export const lines = (...parts) => parts.filter(Boolean).join('\n');

// Escaping does not neutralise a URL scheme: `javascript:...` survives esc() intact
// because it contains no HTML delimiters. Every URL that comes from data goes through
// here, so a bad scheme cannot become a live link even by mistake.
const SAFE_SCHEMES = ['https:', 'http:', 'mailto:'];

/**
 * Allow absolute http(s)/mailto URLs and same-site relative paths. Anything else is
 * refused loudly at build time rather than shipped.
 * @param {string} url
 * @param {string} where - shown in the error, so the offending entry is findable
 */
export function safeUrl(url, where = 'unknown') {
  const value = String(url ?? '').trim();
  if (value.startsWith('/') && !value.startsWith('//')) return value; // root-relative
  if (/^[#?]/.test(value)) return value; // fragment or query on the current page
  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    throw new Error(`Unparseable URL in ${where}: ${JSON.stringify(value)}`);
  }
  if (!SAFE_SCHEMES.includes(parsed.protocol)) {
    throw new Error(
      `Refusing to render a "${parsed.protocol}" URL in ${where}. ` +
        `Allowed: ${SAFE_SCHEMES.join(' ')} or a root-relative path.`,
    );
  }
  return parsed.href;
}
