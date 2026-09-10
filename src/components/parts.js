// Reusable page pieces: page headers, project entries, the aperture that stands in
// for a missing screenshot, contact cards, and the short work list on the home page.

import { esc, attrs, safeUrl } from '../lib/html.js';

/** The heading block every page opens with. */
export const pageHeader = ({ title, lead, body = [] }) => `    <header class="page-head">
      <h1>${esc(title)}</h1>
      ${lead ? `<p class="page-head__lead">${esc(lead)}</p>` : ''}
    </header>
${body.map((p) => `    <p class="prose">${esc(p)}</p>`).join('\n')}`;

/**
 * A view into a project. With no screenshot cleared for publication, the frame shows
 * an empty doorway rather than a stand-in image, and says so. This is deliberate:
 * an honest gap is better than a fabricated one.
 */
function aperture(project) {
  if (project.screenshot) {
    const { src, alt, width, height } = project.screenshot;
    const url = safeUrl(src, `screenshot for project "${project.id}"`);
    return `<figure class="view">
        <div class="view__frame">
          <img${attrs({ src: url, alt, width, height, loading: 'lazy', decoding: 'async', class: 'view__image' })}>
        </div>
      </figure>`;
  }
  return `<figure class="view view--empty">
        <div class="view__frame">
          <svg class="view__art" viewBox="0 0 180 320" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
            <defs>
              <linearGradient id="ap-${esc(project.id)}" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0"   stop-color="#DCE4EC"/>
                <stop offset=".55" stop-color="#E4E1EA"/>
                <stop offset="1"   stop-color="#EFEDE4"/>
              </linearGradient>
              <filter id="ap-blur-${esc(project.id)}" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="13"/>
              </filter>
            </defs>
            <rect width="180" height="320" fill="url(#ap-${esc(project.id)})"/>
            <g filter="url(#ap-blur-${esc(project.id)})" fill="#FBF9F4" opacity=".75">
              <ellipse cx="46" cy="104" rx="58" ry="17"/>
              <ellipse cx="138" cy="150" rx="50" ry="14"/>
              <ellipse cx="80" cy="236" rx="70" ry="20"/>
            </g>
            <rect x="0" y="262" width="180" height="58" fill="#B7C4AC" opacity=".55"/>
            <g fill="none" stroke="#A9A18C" stroke-width="2.5">
              <rect x="66" y="176" width="48" height="90"/>
            </g>
            <rect x="68.5" y="178.5" width="43" height="87.5" fill="#F4EFE0" opacity=".55"/>
          </svg>
        </div>
        <figcaption class="view__caption">No screenshot yet</figcaption>
      </figure>`;
}

/** One project, as a full-width entry rather than a card in a grid. */
export const projectEntry = (project) => `    <article class="project" id="${esc(project.id)}">
      <div class="project__head">
        <h2 class="project__name">${esc(project.name)}</h2>
        <p class="project__kind">${esc(project.kind)}</p>
      </div>
      ${aperture(project)}
      <div class="project__body">
        <p class="project__summary">${esc(project.summary)}</p>
${project.body.map((p) => `        <p class="prose">${esc(p)}</p>`).join('\n')}
        <dl class="facts">
${project.facts
  .map(
    (f) => `          <div class="facts__row">
            <dt>${esc(f.label)}</dt>
            <dd>${esc(f.value)}</dd>
          </div>`,
  )
  .join('\n')}
        </dl>
      </div>
    </article>`;

/** The short list of work on the home page. Links straight to the full entry. */
export const workList = (items) => `      <ul class="work">
${items
  .map(
    (p) => `        <li class="work__item">
          <a class="work__link" href="/projects/#${esc(p.id)}">
            <span class="work__name">${esc(p.name)}</span>
            <span class="work__kind">${esc(p.kind)}</span>
          </a>
        </li>`,
  )
  .join('\n')}
      </ul>`;

/** A contact channel. Only ever rendered for a confirmed public account. */
export const contactCard = (channel) => `        <li class="channels__item">
          <a class="channel" href="${esc(safeUrl(channel.href, `contact channel "${channel.label}"`))}">
            <span class="channel__label">${esc(channel.label)}</span>
            <span class="channel__value">${esc(channel.value)}</span>
          </a>
        </li>`;
