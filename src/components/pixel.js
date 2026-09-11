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

// A gloved hand pointing down and to the right, on a 12 x 16 native grid.
//
// Proportions come from Kenney's CC0 Cursor Pixel Pack (tiles 0134-0137,
// inspected at 26x): the index finger is SHORT and THICK against a chunky
// rectangular palm - about three pixels wide and five long against a nine by
// seven palm - and the read comes from the silhouette and its outline rather
// than from internal detail. A long thin finger on a round palm is what made
// the previous pointer look like a balloon on a stick. Nothing is copied: the
// pack's cursors are flat white, and this one is drawn in our own palette with
// a cuff, folded fingers, and deliberate highlight and shadow pixels.
//
// Layers paint in order: ink (silhouette), fill (glove), cuff, dim, hi.
export const HAND_POINT = {
  ink: [
    [3, 0, 6, 1], [2, 1, 8, 2], [1, 3, 10, 2],
    [0, 5, 11, 3],                              // the thumb, out to the left
    [1, 8, 10, 1],
    [2, 9, 9, 2],                               // the palm's closed bottom edge
    [6, 11, 5, 1], [7, 12, 4, 2], [8, 14, 3, 2],
  ],
  fill: [
    [3, 1, 6, 2],
    [2, 3, 8, 2], [1, 5, 9, 3], [2, 8, 8, 1], [3, 9, 7, 1],
    [7, 10, 3, 4], [8, 14, 2, 1],               // a short, THICK finger
  ],
  cuff: [[3, 1, 6, 2]],                         // a small band at the wrist
  dim: [
    [9, 4, 1, 5], [9, 9, 1, 1],                 // the shaded right flank
    [9, 12, 1, 2],                              // and down the finger
    [4, 9, 1, 1], [6, 9, 1, 1],                 // creases: three folded fingers
  ],
  hi: [
    [2, 4, 1, 1], [1, 5, 1, 2],                 // lit upper left, on the thumb
    [3, 3, 4, 1],
    [7, 10, 1, 3],
  ],
};

// The same glove mirrored to point down and to the LEFT, for a hand that sits
// above and to the right of the button it is demonstrating. Mirrored geometry,
// but the highlights and shadows are re-authored rather than flipped: the light
// stays up and to the left, so the lit edge belongs on the left of the new
// silhouette and the shaded flank on its right.
export const HAND_POINT_LEFT = {
  ink: [
    [3, 0, 6, 1], [2, 1, 8, 2], [1, 3, 10, 2],
    [1, 5, 11, 3],                              // the thumb, out to the right
    [1, 8, 10, 1], [1, 9, 9, 2],
    [1, 11, 5, 1], [1, 12, 4, 2], [1, 14, 3, 2],
  ],
  fill: [
    [3, 1, 6, 2], [2, 3, 8, 2], [2, 5, 9, 3],
    [2, 8, 8, 1], [2, 9, 7, 1],
    [2, 10, 3, 4], [2, 14, 2, 1],
  ],
  cuff: [[3, 1, 6, 2]],
  dim: [
    [9, 4, 1, 6], [9, 10, 1, 1],                // the shaded right flank
    [4, 11, 1, 3],                              // and down the right of the finger
    [5, 9, 1, 1], [7, 9, 1, 1],                 // creases: three folded fingers
  ],
  hi: [
    [2, 4, 1, 1], [2, 5, 1, 2], [4, 3, 4, 1],
    [2, 10, 1, 4],                              // the lit left edge of the finger
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
