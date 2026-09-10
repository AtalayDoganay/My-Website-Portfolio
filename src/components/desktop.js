// The desktop we arrive at: early-2000s Windows-inspired, not Windows-copied.
//
// Original wallpaper (a night version of the meadow the rest of the site lives in),
// original Start glyph (the lit doorway from the other pages), beveled chrome built
// from tinted greys rather than the grey of any particular operating system.
//
// This phase is deliberately empty of applications. Nothing here is a control that
// does nothing: the Start button opens a real menu, the menu item really returns to
// the room, and the clock shows the real time.

import { esc } from '../lib/html.js';

export function desktop({ heading, note }) {
  return `<div class="desktop" data-desktop hidden inert>
  <div class="desktop__wall" aria-hidden="true">
    <span class="wall__sky"></span>
    <span class="wall__moon"></span>
    <span class="wall__ridge wall__ridge--far"></span>
    <span class="wall__ridge wall__ridge--near"></span>
    <span class="wall__door"></span>
    <span class="wall__mist"></span>
  </div>

  <div class="desktop__surface">
    <div class="plaque">
      <h1 class="plaque__title">${esc(heading)}</h1>
      <p class="plaque__note">${esc(note)}</p>
    </div>
  </div>

  <div class="taskbar">
    <button class="tb-btn tb-start" type="button" data-start
            aria-expanded="false" aria-controls="start-menu">
      <span class="tb-start__glyph" aria-hidden="true"></span>Start
    </button>
    <div class="tb-gap"></div>
    <div class="tb-tray">
      <span class="tb-clock" data-clock role="status" aria-label="Current time"></span>
    </div>
  </div>

  <div class="start-menu" id="start-menu" data-start-menu hidden>
    <div class="start-menu__rail" aria-hidden="true"></div>
    <ul class="start-menu__list">
      <li>
        <button class="start-menu__item" type="button" data-leave>
          <span class="start-menu__icon" aria-hidden="true"></span>Back to the room
        </button>
      </li>
    </ul>
  </div>
</div>`;
}
