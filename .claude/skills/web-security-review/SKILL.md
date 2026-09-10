---
name: web-security-review
description: Use when reviewing the security of a website or web app before release or after adding routes, data handling, dependencies, or third-party code - inspects the real attack surface and reports severity, evidence, impact, and remediation.
---

# web-security-review

Review the security of what is actually built. A review is an inspection, not a guarantee.

## Map the real surface first

Do not review a checklist against an imagined app. Establish what exists:

- Routes and pages, and which accept input or render user-controlled content.
- Data: what is collected, where it is stored, what leaves the browser, what is logged.
- Dependencies and lockfiles; which run at build time and which ship to the client.
- Third-party code: scripts, embeds, fonts, analytics, iframes.
- Hosting and deployment: platform, headers, redirects, environment variables, CI permissions.
- Authentication, sessions, and any server-side handler - or the confirmed absence of them.

Name the trust boundaries you found. Review the controls that apply to those boundaries and explicitly mark the rest not-applicable. A static site with no input and no server has a different surface than an app with a login, and pretending otherwise produces noise.

## Secrets

- Search the working tree and the committed history for keys, tokens, connection strings, and private URLs.
- Confirm no secret is present in frontend bundles, build output, logs, or screenshots.
- Environment examples must hold placeholders only.
- `.gitignore` does not protect a secret that is already committed. A committed secret must be treated as disclosed and rotated; removing it from the tip commit does not undo the exposure.

## Controls to review where applicable

- **Untrusted content**: no raw HTML injection from user or remote data (`innerHTML`, `dangerouslySetInnerHTML`, template injection); no `eval`, `new Function`, or dynamic script construction from data.
- **Server-side handlers, if any**: input validation on the server, authorization on every action, session and cookie flags (`HttpOnly`, `Secure`, `SameSite`), CSRF protection for state-changing requests, rate limiting, least-privilege credentials.
- **Response headers**: derive Content-Security-Policy and the rest from the actual hosting platform and the real asset origins the page loads. A CSP written from a template usually breaks the page or permits everything. Test the deployed headers and confirm the page still works. Enable HSTS only after HTTPS and full domain/subdomain coverage are confirmed.
- **Dependencies**: review additions and lockfile changes; minimize client-side third-party scripts; record asset and font licenses.
- **CI**: least-privilege `permissions:`, actions pinned to verified commit SHAs, no secrets exposed to workflows triggered by untrusted pull requests.

## Report

For each finding: severity, affected file or configuration, the evidence you observed, the realistic impact, the remediation, and the uncertainty that remains. Distinguish a confirmed reproducible issue from a suspicion worth checking.

Close with what you did not review and what a passing scanner does not establish. A tool finding nothing is evidence about that tool's coverage, not proof the application is secure.

## Local metadata is not a server header

A `<meta>` tag, a local config file, or a committed workflow file does not set a live response header, and a committed workflow is not a run that passed. Verify against the deployed response or say the control is unverified.
