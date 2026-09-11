// The opening scene: a pixel-art computer standing in a pixel room.
//
// The machine is drawn by tools/pixel_art.py on a 216x150 integer grid with a fixed
// palette - not a downscaled render and not a pixelation filter. Two images come out
// of the same geometry code, one per theme, so they line up pixel for pixel and the
// screen sits at identical coordinates in both. Both are in the markup and CSS shows
// whichever the theme calls for, so switching is instant and never moves anything.
//
// The monitor is drawn in an oblique projection with its depth running back and to
// the LEFT, which turns it to face slightly right: you see its left casing. The
// front face - and so the tube - stays a true rectangle on the grid, which is what
// lets the live text sit on the pixel grid without being resampled or sheared.

import { esc } from '../lib/html.js';
import { themeToggle } from './pixel.js';

export function computer({ alt }) {
  return `<div class="crt" data-crt>
  <img class="crt__art crt__art--wide crt__art--dark" src="/assets/pixel/machine-dark.png"
       alt="${esc(alt)}" width="216" height="150" decoding="async" fetchpriority="high">
  <img class="crt__art crt__art--wide crt__art--light" src="/assets/pixel/machine-light.png"
       alt="" aria-hidden="true" width="216" height="150" decoding="async">
  <img class="crt__art crt__art--narrow crt__art--dark" src="/assets/pixel/machine-compact-dark.png"
       alt="" aria-hidden="true" width="120" height="126" decoding="async">
  <img class="crt__art crt__art--narrow crt__art--light" src="/assets/pixel/machine-compact-light.png"
       alt="" aria-hidden="true" width="120" height="126" decoding="async">

  <button class="crt__screen" type="button" data-screen
          aria-label="Enter the computer" aria-describedby="crt-description">
    <span class="crt__glass">
      <span class="crt__wall" aria-hidden="true"></span>
      <span class="crt__readout" aria-hidden="true"><span class="crt__line" data-line></span
        ><span class="crt__caret" data-caret></span></span>
      <span class="crt__hint" data-hint aria-hidden="true"></span>
      <span class="crt__scan" aria-hidden="true"></span>
    </span>
  </button>
</div>`;
}

/** The room: sky, floor, the machine, the theme switch, and a no-script fallback. */
export function room({ description, machineAlt, fallback }) {
  return `<div class="room" data-room data-state="intro">
  <div class="room__world" data-world>
    <div class="room__env" aria-hidden="true">
      <span class="room__sky"></span>
      <span class="room__stars"></span>
      <span class="room__ridge"></span>
      <span class="room__floor"></span>
      <span class="room__glow"></span>
    </div>
    <div class="room__stage">
      ${computer({ alt: machineAlt })}
    </div>
  </div>

  <div class="room__switch">
    ${themeToggle({ className: 'theme-toggle--room' })}
  </div>

  <p id="crt-description" class="visually-hidden">${esc(description)}</p>
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
