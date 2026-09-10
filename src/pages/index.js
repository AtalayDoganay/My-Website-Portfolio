import { layout } from '../components/layout.js';
import { room } from '../components/room.js';
import { desktop } from '../components/desktop.js';
import { opening } from '../data/site.js';

export const render = () =>
  layout({
    title: 'Home',
    path: '/',
    chrome: 'immersive',
    script: '/room.js',
    description:
      'Atalay Doganay is a computer science student at Cal Poly Pomona who builds browser games and small apps.',
    content: `${room({
      description: opening.screenDescription,
      fallback: opening.fallback,
    })}
${desktop({ heading: opening.desktopHeading, note: opening.desktopNote })}`,
  });
