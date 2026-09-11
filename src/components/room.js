// The opening scene: a pixel-art computer standing in a pixel room.
//
// The desk is drawn by tools/pixel_art.py on a 340x180 integer grid with a fixed
// palette - not a downscaled render and not a pixelation filter. Two images come out
// of the same geometry code, one per theme, so they line up pixel for pixel and the
// screen sits at identical coordinates in both. Both are in the markup and CSS shows
// whichever the theme calls for, so switching is instant and never moves anything.
//
// ONE SCENE, ONE CAMERA. Everything physical - the wall, its grain, the tube's glow,
// the tabletop band that continues past the artwork, the monitor, bezel, stand, tower,
// keyboard, mouse and cables - lives inside `.room__world`. That element is the camera
// target, and it is the only thing that ever moves: the opening starts with the camera
// pushed in on the glass and pulls back to reveal the desk, and clicking pushes it back
// in before the desktop takes over. There is no second copy of the display and nothing
// animates on its own, so the whole setup necessarily changes size together.
//
// The live text lives INSIDE `.crt__glass`, which has `overflow: hidden`. It is
// therefore attached to the physical glass and clipped by it at every frame of the
// camera move, including the first one.
//
// Skip, sound and the theme switch sit OUTSIDE the world, so the camera never carries
// them.

import { esc } from '../lib/html.js';
import { themeToggle, pixelSprite, HAND_POINT_LEFT } from './pixel.js';

/** Two rows of terminal text with their own carets.
 *
 * Emitted without a single space between the elements: the readout sets
 * `white-space: pre` so a typed line keeps its spacing exactly, which also means
 * any newline in this markup would become a real blank line on the glass.
 */
const readout = () =>
  `<span class="crt__rows">` +
  [1, 2]
    .map(
      (n) =>
        `<span class="crt__row"><span class="crt__text" data-line="${n}"></span>` +
        `<span class="crt__caret" data-caret="${n}"></span></span>`,
    )
    .join('') +
  `</span>`;

/** The invitation: a raised button, a gloved hand demonstrating it, and a burst.
 *
 * All of it lives INSIDE `.crt__glass`, which clips it, so the whole thing is
 * part of the physical screen rather than decoration floating over the machine.
 * Everything is sized in container units of the glass, so it holds its
 * proportions at every framing.
 *
 * The button is the only interactive element: `.crt__screen` is a plain div now,
 * because a button inside a button is not valid and cannot be operated.
 */
function invitation({ label }) {
  // Bounded and explicit: three exclamation marks, two question marks, four
  // stars. They all launch from the button's top edge.
  const marks = [
    ['e', 1], ['e', 2], ['e', 3], ['q', 4], ['q', 5],
    ['s', 6], ['s', 7], ['s', 8], ['s', 9],
  ];
  const body = marks
    .map(([kind, n]) =>
      kind === 's'
        ? `<i class="burst__bit burst__bit--${n} burst__star"></i>`
        : `<i class="burst__bit burst__bit--${n} burst__mark">${kind === 'e' ? '!' : '?'}</i>`)
    .join('');
  return `<span class="invite" data-invite-layer aria-hidden="true">
      <span class="burst">${body}</span>
      <span class="invite__hand">${pixelSprite(HAND_POINT_LEFT, { w: 12, h: 16 })}</span>
    </span>
    <button class="crt__go" type="button" data-go hidden
            aria-describedby="crt-description"><span class="crt__go-face"
      ><span class="crt__go-label" data-go-label>${esc(label)}</span></span></button>`;
}

export function computer({ alt, pointerLabel }) {
  return `<div class="crt" data-crt>
  <img class="crt__art crt__art--wide crt__art--dark" src="/assets/pixel/machine-dark.png"
       alt="${esc(alt)}" width="340" height="180" decoding="async" fetchpriority="high">
  <img class="crt__art crt__art--wide crt__art--light" src="/assets/pixel/machine-light.png"
       alt="" aria-hidden="true" width="340" height="180" decoding="async">
  <img class="crt__art crt__art--narrow crt__art--dark" src="/assets/pixel/machine-compact-dark.png"
       alt="" aria-hidden="true" width="120" height="168" decoding="async">
  <img class="crt__art crt__art--narrow crt__art--light" src="/assets/pixel/machine-compact-light.png"
       alt="" aria-hidden="true" width="120" height="168" decoding="async">

  <div class="crt__screen" data-screen>
    <span class="crt__glass">
      <span class="crt__wall" aria-hidden="true"></span>
      <span class="crt__readout" aria-hidden="true">${readout()}</span>
${invitation({ label: pointerLabel })}
      <span class="crt__scan" aria-hidden="true"></span>
      <span class="crt__bloom" aria-hidden="true"></span>
    </span>
  </div>
</div>`;
}

/** The room: the wall, the desk, the controls, and a no-script fallback. */
export function room({ description, machineAlt, fallback, opening }) {
  return `<div class="room" data-room data-state="boot" data-invite="off">
  <div class="room__world" data-world>
    <div class="room__env" aria-hidden="true">
      <span class="room__wall"></span>
      <span class="room__grain"></span>
      <span class="room__glow"></span>
      <span class="room__desk"></span>
    </div>
    <div class="room__stage">
      ${computer({ alt: machineAlt, pointerLabel: opening.invitePointer })}
    </div>
  </div>

  <div class="room__switch">
    ${themeToggle({ className: 'theme-toggle--room' })}
  </div>

  <div class="room__controls" data-intro-controls>
    <button class="room__btn" type="button" data-skip>${esc(opening.skipLabel)}</button>
    <button class="room__btn" type="button" data-sound aria-pressed="false">${esc(opening.soundLabel)}</button>
  </div>

  <p id="crt-description" class="visually-hidden">${esc(description)}</p>
  <p class="visually-hidden" role="status" data-spoken></p>
  <noscript>
    <div class="room__noscript">
      <p>${esc(fallback.line)}</p>
      <p>${esc(fallback.note)}</p>
      <ul>
${fallback.links
  .map((l) => `        <li><a href="${esc(l.href)}">${esc(l.label)}</a></li>`)
  .join('\n')}
      </ul>
    </div>
  </noscript>
</div>`;
}
