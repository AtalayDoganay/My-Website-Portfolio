import { layout } from '../components/layout.js';
import { pageHeader, projectEntry } from '../components/parts.js';
import { projects } from '../data/site.js';

export const render = () =>
  layout({
    title: projects.title,
    path: '/projects/',
    description:
      'BALL FIGHTERS, a browser auto-battler, and Next Class, a class reminder app for students.',
    content: `${pageHeader({ title: projects.title, lead: projects.lead })}

${projects.items.map(projectEntry).join('\n\n')}`,
  });
