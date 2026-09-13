import { layout } from '../components/layout.js';
import { pageHeader } from '../components/parts.js';
import { esc } from '../lib/html.js';
import { about } from '../data/site.js';

export const render = () =>
  layout({
    title: about.title,
    path: '/about/',
    description:
      'Atalay Doganay studies computer science at Cal Poly Pomona and holds an Associate in Science in Computer Science from Orange Coast College.',
    content: `${pageHeader({ title: about.title, lead: about.lead, body: about.body })}

    <section class="section" aria-labelledby="${esc(about.credentialsId)}">
      <h2 class="section__title" id="${esc(about.credentialsId)}">${esc(about.credentialsHeading)}</h2>
      <h3 class="section__subtitle" id="education">${esc(about.educationHeading)}</h3>
      <dl class="facts facts--wide">
${about.education
  .map(
    (e) => `        <div class="facts__row">
          <dt>${esc(e.school)}</dt>
          <dd>${esc(e.detail)}</dd>
        </div>`,
  )
  .join('\n')}
      </dl>
${about.credentialsNotes.map((n) => `      <p class="section__note">${esc(n)}</p>`).join('\n')}
    </section>`,
  });
