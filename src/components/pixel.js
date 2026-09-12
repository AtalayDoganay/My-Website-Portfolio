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
 * Build a sprite's silhouette and its interior from one description: the span
 * of solid pixels on each row, as [x, width].
 *
 * A pixel is INTERIOR when it and its four neighbours are all solid, so the
 * outline closes by itself - including where the silhouette steps in sharply,
 * which is exactly where a hand-listed inset gets it wrong and leaves the
 * outline open. Authoring a shape then means describing its profile once
 * instead of keeping two lists of rectangles in agreement.
 *
 * @param {Array<[number, number] | null>} rows  one [x, width] per row, top down
 * @returns {{ink: Array<[number,number,number,number]>, fill: Array<...>}}
 */
export function fromRows(rows) {
  const solid = (x, y) => {
    const span = rows[y];
    return !!span && x >= span[0] && x < span[0] + span[1];
  };
  const ink = [];
  const fill = [];
  rows.forEach((span, y) => {
    if (!span) return;
    ink.push([span[0], y, span[1], 1]);
    // Collect interior pixels into runs, so the SVG carries a rectangle per
    // run rather than one per pixel.
    let runStart = null;
    for (let x = span[0]; x <= span[0] + span[1]; x += 1) {
      const inside =
        x < span[0] + span[1] &&
        solid(x, y) && solid(x - 1, y) && solid(x + 1, y) &&
        solid(x, y - 1) && solid(x, y + 1);
      if (inside && runStart === null) runStart = x;
      if (!inside && runStart !== null) {
        fill.push([runStart, y, x - runStart, 1]);
        runStart = null;
      }
    }
  });
  return { ink, fill };
}

/**
 * A two-tone sprite: the same integer grid, but an ink layer and a lit layer so
 * a shape can carry the design's one-unit outline without a second element.
 * The layers are classed rather than filled inline, so they take their colours
 * from the theme like everything else.
 *
 * @param {{ink: Array<[number,number,number,number]>, lit: Array<[number,number,number,number]>}} layers
 */
export function pixelSprite(layers, { w = 16, h = 16, className = '' } = {}) {
  const group = (cls, rects) =>
    !rects || !rects.length
      ? ''
      : `<g class="${cls}">` +
        rects.map(([x, y, rw, rh]) => `<rect x="${x}" y="${y}" width="${rw}" height="${rh}"/>`).join('') +
        '</g>';
  const body = ['ink', 'fill', 'cuff', 'dim', 'hi']
    .map((name) => group('px-sprite__' + name, layers[name]))
    .join('');
  return `<svg class="px-sprite${className ? ' ' + esc(className) : ''}" viewBox="0 0 ${w} ${h}"
       aria-hidden="true" focusable="false" shape-rendering="crispEdges">${body}</svg>`;
}

// A friendly pointing glove. The SHORT index is on the thumb side of the
// palm; three curled fingers sit together to its right. The thumb wraps in
// from the left. Placement uses the fingertip, never the centre of the palm.
export const HAND_ANCHOR = { w: 22, h: 24, x: 7.5, y: 24 };
const HAND_PRESS_ROWS = [
  [8, 9], [7, 11], [7, 11], [7, 11], [7, 11], // cuff
  [6, 13], [5, 15], [3, 18], [2, 19],          // palm and thumb
  [1, 21], [1, 21], [1, 21], [2, 20],
  [4, 18], [5, 17], [5, 17], [5, 16], [5, 14], // three folded fingers
  [5, 5], [5, 5], [5, 5], [5, 5], [5, 5], [6, 3], // index and round tip
];

export const HAND_PRESS = {
  ...fromRows(HAND_PRESS_ROWS),
  cuff: [[8, 1, 9, 3]],
  dim: [
    [8, 4, 9, 1], [18, 7, 1, 3], [20, 10, 1, 5],
    [4, 8, 1, 3], [3, 11, 3, 1], [5, 12, 1, 1], // thumb curled onto palm
    [10, 11, 1, 6], [14, 11, 1, 6], [18, 11, 1, 5], // folded finger seams
    [11, 16, 3, 1], [15, 16, 3, 1], [19, 15, 1, 1],
    [8, 17, 1, 5], // index shadow
  ],
  hi: [
    [7, 6, 9, 1], [6, 7, 1, 4], [2, 9, 1, 2],
    [11, 10, 2, 1], [15, 10, 2, 1], [19, 10, 1, 1],
    [6, 14, 1, 8],
  ],
};

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
