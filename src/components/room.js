// The opening scene: a beige CRT computer standing in a dark, hazy room.
//
// The machine is a pre-rendered image, not an illustration. It is modelled and
// rendered from scratch by tools/model_crt.py in Blender - see docs/ASSETS.md for
// provenance. Nothing about it is downloaded, licensed from anyone, or traced.
//
// The screen is NOT part of the image: the render leaves the tube blank on purpose.
// A real <button> is laid over the glass at the exact rectangle the renderer
// measured, so the typed text is live DOM text, the hit area is the glass, and the
// flight into the screen can animate from its actual position.
//
// The camera was level and framed by lens shift, so the screen plane stays parallel
// to the image plane and projects as a true axis-aligned rectangle. That is why this
// overlay needs no perspective transform - build.mjs refuses to build if the
// renderer ever reports otherwise.

import { esc } from '../lib/html.js';

const ASSET = '/assets/scene/crt.webp';
const ASSET_HALF = '/assets/scene/crt@half.webp';

export function computer({ alt }) {
  return `<div class="crt">
  <img class="crt__art"
       src="${ASSET}"
       srcset="${ASSET_HALF} 1300w, ${ASSET} 2600w"
       sizes="(max-width: 56rem) 96vw, 62vw"
       alt="${esc(alt)}"
       width="2600" height="1642"
       decoding="async" fetchpriority="high">

  <button class="crt__screen" type="button" data-screen
          aria-label="Enter the computer" aria-describedby="crt-description">
    <span class="crt__glass">
      <span class="crt__wall" aria-hidden="true"></span>
      <span class="crt__readout" aria-hidden="true"><span class="crt__line" data-line></span
        ><span class="crt__caret" data-caret></span></span>
      <span class="crt__hint" data-hint aria-hidden="true"></span>
      <span class="crt__scan" aria-hidden="true"></span>
      <span class="crt__sheen" aria-hidden="true"></span>
    </span>
  </button>
</div>`;
}

/** The room: environment, machine, and the no-JavaScript fallback. */
export function room({ description, machineAlt, fallback }) {
  return `<div class="room" data-room data-state="intro">
  <div class="room__world" data-world>
    <div class="room__env" aria-hidden="true">
      <span class="room__sky"></span>
      <span class="room__horizon"></span>
      <span class="room__haze room__haze--far"></span>
      <span class="room__haze room__haze--near"></span>
      <span class="room__desk"></span>
      <span class="room__pool"></span>
      <span class="room__bloom"></span>
    </div>
    <div class="room__stage">
      ${computer({ alt: machineAlt })}
    </div>
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
