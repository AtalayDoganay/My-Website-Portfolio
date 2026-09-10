import { layout } from '../components/layout.js';
import { pageHeader } from '../components/parts.js';
import { esc } from '../lib/html.js';
import { nav, notFound } from '../data/site.js';

export const render = () =>
  layout({
    title: notFound.title,
    path: '/404',
    description: 'That page does not exist.',
    content: `${pageHeader({ title: notFound.title, lead: notFound.lead, body: notFound.body })}

    <section class="section section--plain">
      <h2 class="visually-hidden">Pages on this site</h2>
      <ul class="work">
${nav
  .map(
    (item) => `        <li class="work__item">
          <a class="work__link" href="${esc(item.href)}"><span class="work__name">${esc(item.label)}</span></a>
        </li>`,
  )
  .join('\n')}
      </ul>
    </section>`,
  });
