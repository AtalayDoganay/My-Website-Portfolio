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

    <section class="section" aria-labelledby="education">
      <h2 class="section__title" id="education">${esc(about.educationHeading)}</h2>
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
    </section>`,
  });
