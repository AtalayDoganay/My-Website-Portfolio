import { layout } from '../components/layout.js';
import { pageHeader, contactCard } from '../components/parts.js';
import { contact } from '../data/site.js';

export const render = () =>
  layout({
    title: contact.title,
    path: '/contact/',
    description: 'How to reach Atalay Doganay.',
    content: `${pageHeader({ title: contact.title, lead: contact.lead, body: contact.body })}

    <section class="section">
      <h2 class="visually-hidden">Where to find me</h2>
      <ul class="channels">
${contact.channels.map(contactCard).join('\n')}
      </ul>
    </section>`,
  });
