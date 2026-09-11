// Small pixel icons, drawn as SVG rectangles on an integer grid.
//
// SVG rather than PNG so they take `currentColor` and therefore the theme's outline
// colour without a second file, and so they stay exact at any integer scale.
// shape-rendering: crispEdges keeps the browser from softening the squares.

import { esc } from '../lib/html.js';

/** @param {Array<[number,number,number,number]>} rects  x, y, w, h on the grid */
export function pixelIcon(rects, { size = 16, className = '', label = null } = {}) {
  const body = rects
    .map(([x, y, w, h]) => `<rect x="${x}" y="${y}" width="${w}" height="${h}"/>`)
    .join('');
  const semantics = label
    ? ` role="img" aria-label="${esc(label)}"`
    : ' aria-hidden="true" focusable="false"';
  return `<svg class="px-icon${className ? ' ' + esc(className) : ''}" viewBox="0 0 ${size} ${size}"${semantics} shape-rendering="crispEdges" fill="currentColor">${body}</svg>`;
}

// A sun: a blocky disc with four cardinal rays and four corner pips.
export const SUN = [
  [6, 4, 4, 1], [4, 6, 1, 4], [11, 6, 1, 4], [6, 11, 4, 1],
  [5, 5, 6, 6],
  [7, 0, 2, 2], [7, 14, 2, 2], [0, 7, 2, 2], [14, 7, 2, 2],
  [2, 2, 2, 2], [12, 2, 2, 2], [2, 12, 2, 2], [12, 12, 2, 2],
];

// A crescent moon, cut from the same disc so the two icons sit at the same weight.
export const MOON = [
  [6, 1, 4, 1], [4, 2, 3, 1], [3, 3, 3, 1], [2, 4, 3, 1],
  [2, 5, 3, 1], [1, 6, 3, 1], [1, 7, 3, 1], [1, 8, 3, 1],
  [2, 9, 3, 1], [2, 10, 3, 1], [3, 11, 3, 1], [4, 12, 3, 1], [6, 13, 4, 1],
];

// A little window, used as the desktop's program mark.
export const WINDOW_MARK = [
  [1, 2, 14, 1], [1, 12, 14, 1], [1, 2, 1, 11], [14, 2, 1, 11],
  [1, 5, 14, 1],
  [11, 3, 2, 1],
];

// The lit doorway that appears everywhere else on the site: the Start mark.
export const DOORWAY = [
  [4, 2, 8, 1], [4, 2, 1, 13], [11, 2, 1, 13],
  [5, 3, 6, 12],
];

/**
 * The theme switch. Both icons are always in the markup; CSS shows whichever the
 * current theme calls for, so switching never waits on JavaScript to redraw.
 */
export function themeToggle({ className = '' } = {}) {
  return `<button class="theme-toggle${className ? ' ' + esc(className) : ''}" type="button"
          data-theme-toggle aria-label="Switch theme">
  <span class="theme-toggle__box" aria-hidden="true">
    <span class="theme-toggle__sun">${pixelIcon(SUN)}</span>
    <span class="theme-toggle__moon">${pixelIcon(MOON)}</span>
  </span>
</button>`;
}
