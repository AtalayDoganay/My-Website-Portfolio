// The desktop behind the glass: early-2000s Windows-era layout, rebuilt on the
// pixel grid. Blue title bar, compact window controls, bevelled window, Start
// button, taskbar - all of it drawn with hard one-pixel edges and the theme's
// outline colour, with pixel-art icons rather than smooth ones.
//
// The era is referenced, not copied: no Microsoft logo, no Luna artwork, no
// borrowed icon set. Every control that looks operable is operable.

import { esc } from '../lib/html.js';
import { pixelIcon, themeToggle, WINDOW_MARK, DOORWAY } from './pixel.js';

const CLOSE = [[3, 3, 2, 2], [5, 5, 2, 2], [7, 7, 2, 2], [9, 9, 2, 2], [11, 11, 2, 2],
               [11, 3, 2, 2], [9, 5, 2, 2], [5, 9, 2, 2], [3, 11, 2, 2]];
const MINIMISE = [[3, 10, 10, 2]];
const MAXIMISE = [[3, 3, 10, 1], [3, 3, 1, 10], [12, 3, 1, 10], [3, 12, 10, 1], [3, 4, 10, 1]];

export function desktop({ heading, note, items }) {
  return `<div class="desktop" data-desktop hidden inert>
  <div class="desktop__wall" aria-hidden="true">
    <img class="desktop__paper desktop__paper--dark" src="/assets/pixel/wallpaper-dark.png"
         alt="" width="240" height="150" decoding="async">
    <img class="desktop__paper desktop__paper--light" src="/assets/pixel/wallpaper-light.png"
         alt="" width="240" height="150" decoding="async">
  </div>

  <div class="desktop__surface">
    <section class="win" data-window aria-labelledby="win-title">
      <div class="win__bar">
        <span class="win__icon" aria-hidden="true">${pixelIcon(WINDOW_MARK)}</span>
        <h1 class="win__title" id="win-title">${esc(heading)}</h1>
        <div class="win__buttons">
          <button class="win__btn" type="button" data-window-min aria-label="Minimise this window">${pixelIcon(MINIMISE)}</button>
          <button class="win__btn" type="button" disabled aria-label="Maximise (this window cannot be resized)">${pixelIcon(MAXIMISE)}</button>
          <button class="win__btn win__btn--close" type="button" data-window-close aria-label="Close this window">${pixelIcon(CLOSE)}</button>
        </div>
      </div>

      <div class="win__menubar" role="presentation">
        <span class="win__menu"><u>F</u>ile</span>
        <span class="win__menu"><u>E</u>dit</span>
        <span class="win__menu"><u>V</u>iew</span>
        <span class="win__menu"><u>H</u>elp</span>
      </div>

      <div class="win__body">
        <p class="win__lead">${esc(note)}</p>
        <ul class="win__list">
${items.map((i) => `          <li><span class="win__bullet" aria-hidden="true"></span>${esc(i)}</li>`).join('\n')}
        </ul>
        <div class="win__field" role="presentation">
          <span class="win__field-label">Status</span>
          <span class="win__field-value">Shell only. Nothing else is wired up yet.</span>
        </div>
      </div>

      <div class="win__status">
        <span class="win__status-cell win__status-cell--grow">Ready</span>
        <span class="win__status-cell">1 item</span>
      </div>
    </section>
  </div>

  <div class="taskbar">
    <button class="tb-start" type="button" data-start aria-expanded="false" aria-controls="start-menu">
      <span class="tb-start__glyph" aria-hidden="true">${pixelIcon(DOORWAY)}</span>start
    </button>
    <div class="tb-tasks">
      <button class="tb-task" type="button" data-task aria-pressed="true">
        <span class="tb-task__icon" aria-hidden="true">${pixelIcon(WINDOW_MARK)}</span>${esc(heading)}
      </button>
    </div>
    <div class="tb-tray">
      ${themeToggle({ className: 'theme-toggle--tray' })}
      <span class="tb-clock" data-clock role="status" aria-label="Current time"></span>
    </div>
  </div>

  <div class="start-menu" id="start-menu" data-start-menu hidden>
    <div class="start-menu__head">
      <span class="start-menu__avatar" aria-hidden="true">${pixelIcon(DOORWAY)}</span>
      <span class="start-menu__user">${esc(heading)}</span>
    </div>
    <ul class="start-menu__list">
      <li>
        <button class="start-menu__item" type="button" data-restore>
          <span class="start-menu__icon" aria-hidden="true">${pixelIcon(WINDOW_MARK)}</span>
          <span><strong>Reopen window</strong><small>Show the window again</small></span>
        </button>
      </li>
    </ul>
    <div class="start-menu__foot">
      <button class="start-menu__leave" type="button" data-leave>
        <span class="start-menu__icon" aria-hidden="true">${pixelIcon(DOORWAY)}</span>Back to the room
      </button>
    </div>
  </div>
</div>`;
}
