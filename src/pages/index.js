import { layout } from '../components/layout.js';
import { pageHeader, workList } from '../components/parts.js';
import { esc } from '../lib/html.js';
import { home, projects } from '../data/site.js';

export const render = () =>
  layout({
    title: 'Home',
    path: '/',
    variant: 'field',
    description:
      'Atalay Doganay is a computer science student at Cal Poly Pomona who builds browser games and small apps.',
    content: `${pageHeader({ title: home.title, lead: home.lead, body: home.body })}

    <section class="section" aria-labelledby="selected-work">
      <h2 class="section__title" id="selected-work">${esc(home.selectedHeading)}</h2>
      <p class="section__note">${esc(home.selectedNote)}</p>
${workList(projects.items)}
    </section>`,
  });
