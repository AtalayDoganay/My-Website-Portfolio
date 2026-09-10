# Hosting, domain, and deployment — open decisions

**Nothing here is resolved.** No hosting account exists, the domain is not registered or
confirmed as owned, no DNS is configured, and nothing is deployed. Creating this repository
did none of those things.

Recorded 2026-09-09 so the next session does not have to rediscover the open questions.

## Open decisions

| Decision | Status | Notes |
|---|---|---|
| Does Atalay own `atalaydoganay.com`? | **Unknown** | Must be confirmed before any DNS or hosting work. Registration costs money and is Atalay's call. |
| Registrar | Not chosen | Only relevant if the domain is not already owned. |
| Hosting platform | Not chosen | See options below. |
| Repository visibility at launch | Private for now | A portfolio site is usually made public eventually; that is a separate decision. |
| Deploy trigger | Not chosen | Manual first. Automatic deploy on push is a decision, not a default. |
| Analytics | Not chosen | Default to none. Any third-party script is new attack surface and a privacy question. |

## Hosting options to weigh

Decide with Atalay; do not create an account unilaterally. All three have free tiers
adequate for a static portfolio.

- **GitHub Pages** — closest to the repository, simplest mental model, custom domain plus
  automatic HTTPS supported. Response headers are largely not configurable, which limits CSP
  and other header work to `<meta>`-level equivalents where they exist.
- **Cloudflare Pages** — full control over response headers via a `_headers` file, so a real
  CSP is achievable. Adds an account and a dashboard to manage.
- **Netlify** — similar header control via `_headers` or `netlify.toml`. Comparable tradeoff.

**Header control is the deciding technical factor.** If a real CSP and security headers
matter, GitHub Pages will not deliver them.

## Security items that depend on this decision

None of these can be completed until hosting is chosen, and none should be faked in the
meantime:

- **CSP** must be derived from the real asset origins the finished page loads, then tested
  against the deployed site to confirm it does not break the page. A CSP copied from a
  template is either broken or permissive enough to be pointless.
- **Other response headers** (`X-Content-Type-Options`, `Referrer-Policy`,
  `X-Frame-Options`/`frame-ancestors`, `Permissions-Policy`) are platform-specific.
- **HSTS** only after HTTPS is confirmed working and subdomain coverage is understood. Enabled
  early or with a long max-age, it is painful to undo.
- A committed `_headers` or config file **is not a live header**. Verify against the actual
  HTTP response before claiming any of this works.

## What must never be claimed

Until it is actually true and verified against the live site:

- that the site is deployed or live
- that the domain is connected
- that HTTPS, HSTS, or a CSP is in effect
- that the site is "secure"

Setup existing is not a site existing.
