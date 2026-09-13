// The opening scene: a pixel-art computer standing in a pixel room.
//
// The desk is drawn by tools/pixel_art.py on a 576x330 integer grid with a fixed
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
// camera move, including the first one. So do the demonstrating hand and the button.
//
// The BURST does not. It is a sibling of the screen rather than a child of it, so
// nothing clips it and the marks cross the glass boundary, pass in front of the
// moulding, and travel out into the room. It is still inside `.room__world`, so the
// camera carries it with everything else.
//
// Skip, sound and the theme switch sit OUTSIDE the world, so the camera never carries
// them.

import { esc, safeUrl } from '../lib/html.js';
import { themeToggle, pixelSprite, lampIcon, HAND_PRESS, HAND_ANCHOR } from './pixel.js';

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

/** The invitation's parts that belong to the SCREEN: the demonstrating hand and
 * the button it presses.
 *
 * Both live inside `.crt__glass`, which clips them, so they are part of the
 * physical screen rather than decoration floating over the machine. They are
 * sized in container units of the glass, so they hold their proportions at
 * every framing.
 *
 * The button is the only interactive element: `.crt__screen` is a plain div,
 * because a button inside a button is not valid and cannot be operated.
 */
function invitation({ label }) {
  return `<span class="invite" data-invite-layer aria-hidden="true">
      <span class="invite__hand" data-tip-x="${HAND_ANCHOR.x / HAND_ANCHOR.w}"
            data-tip-y="${HAND_ANCHOR.y / HAND_ANCHOR.h}">${pixelSprite(HAND_PRESS, HAND_ANCHOR)}</span>
    </span>
    <button class="crt__go" type="button" data-go hidden
            aria-describedby="crt-description"><span class="crt__go-face"
      ><span class="crt__go-label" data-go-label>${esc(label)}</span></span></button>`;
}

/** The burst, which belongs to the ROOM rather than to the screen.
 *
 * It is a sibling of `.crt__screen`, not a child of it, and that is the whole
 * point: `.crt__glass` clips its contents, so anything launched from inside it
 * can only ever pile up against the bezel. Out here nothing clips, so the marks
 * cross the glass boundary, pass in FRONT of the moulding and carry on into the
 * room before they fade.
 *
 * It is still inside `.room__world`, so the camera carries it exactly like
 * every other physical thing, and its origin is written from the same measured
 * variables that place the screen and the button - so it emits from where the
 * button actually is, at any framing, rather than from a second guess at it.
 *
 * Bounded and explicit: three exclamation marks, three question marks, four
 * stars. Ten pieces, no timer, and nothing takes input.
 */
function burst() {
  const marks = [
    ['e', 1], ['e', 2], ['e', 3],
    ['q', 4], ['q', 5], ['q', 6],
    ['s', 7], ['s', 8], ['s', 9], ['s', 10],
  ];
  const body = marks
    .map(([kind, n]) =>
      kind === 's'
        ? `<i class="burst__bit burst__bit--${n} burst__star"></i>`
        : `<i class="burst__bit burst__bit--${n} burst__mark">${kind === 'e' ? '!' : '?'}</i>`)
    .join('');
  return `  <span class="crt__fx" data-fx aria-hidden="true">
    <span class="burst">${body}</span>
  </span>`;
}

export function computer({ alt, pointerLabel }) {
  return `<div class="crt" data-crt>
  <img class="crt__art crt__art--wide crt__art--dark" src="/assets/pixel/machine-dark.png"
       alt="${esc(alt)}" width="576" height="330" decoding="async" fetchpriority="high">
  <img class="crt__art crt__art--wide crt__art--light" src="/assets/pixel/machine-light.png"
       alt="" aria-hidden="true" width="576" height="330" decoding="async">
  <img class="crt__art crt__art--narrow crt__art--dark" src="/assets/pixel/machine-compact-dark.png"
       alt="" aria-hidden="true" width="180" height="252" decoding="async">
  <img class="crt__art crt__art--narrow crt__art--light" src="/assets/pixel/machine-compact-light.png"
       alt="" aria-hidden="true" width="180" height="252" decoding="async">

  <div class="crt__screen" data-screen>
    <span class="crt__glass">
      <span class="crt__wall" aria-hidden="true"></span>
      <span class="crt__readout" aria-hidden="true">${readout()}</span>
      <span class="crt__scan" aria-hidden="true"></span>
      <span class="crt__bloom" aria-hidden="true"></span>
${invitation({ label: pointerLabel })}
    </span>
  </div>
${burst()}
</div>`;
}

/** The portfolio lamps: four labels on the wall around the computer.
 *
 * They are plain links, present and readable the whole time; the press of the
 * demonstrated key lights them for a moment (see room.css). They live inside
 * `.room__world`, so the camera carries them like the desk, and after the
 * stage in the DOM, so the first Tab still reaches the key. The page script
 * makes them inert whenever the room is not at rest.
 */
function lamps(items) {
  const body = items
    .map((item) => {
      const text = (item.lines || [item.label])
        .map((line) => `<span class="lamp__line">${esc(line)}</span>`)
        .join(' ');
      return `    <a class="lamp lamp--${esc(item.id)}" href="${esc(safeUrl(item.href, `opening.lamps ${item.id}`))}" data-lamp="${esc(item.id)}">
      <span class="lamp__glow" aria-hidden="true"></span>
      <span class="lamp__icon" aria-hidden="true">${lampIcon(item.id)}</span>
      <span class="lamp__text">${text}</span>
    </a>`;
    })
    .join('\n');
  return `<nav class="room__lamps" id="room-lamps" data-lamps aria-label="Portfolio">\n${body}\n    </nav>`;
}

/** The room: the wall, the desk, the controls, and a no-script fallback. */
export function room({ description, machineAlt, fallback, opening }) {
  return `<div class="room" data-room data-state="boot" data-invite="off">
  <div class="room__world" data-world>
    <div class="room__env" aria-hidden="true">
      <span class="room__wall"></span>
      <span class="room__grain"></span>
      <span class="room__desk"></span>
    </div>
    <div class="room__stage">
      ${computer({ alt: machineAlt, pointerLabel: opening.invitePointer })}
    </div>
    ${lamps(opening.lamps || [])}
  </div>

  <div class="room__switch">
    ${themeToggle({ className: 'theme-toggle--room' })}
  </div>

  <div class="room__controls" data-intro-controls>
    <button class="room__btn" type="button" data-skip>${esc(opening.skipLabel)}</button>
    <button class="room__btn" type="button" data-sound aria-pressed="false">${esc(opening.soundLabel)}</button>
    <button class="room__btn" type="button" data-reveal aria-expanded="false" aria-controls="room-lamps"
            data-show="${esc(opening.revealLabel)}" data-hide="${esc(opening.concealLabel)}">${esc(opening.revealLabel)}</button>
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
