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
          <span class="view__placeholder" aria-hidden="true"></span>
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
