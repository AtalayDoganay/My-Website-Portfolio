// The desktop behind the glass: an early-2000s Windows-era shell.
//
// The era is referenced, not copied. The title bar gradient, the bevels, the inset
// fields, the compact toolbar and the taskbar proportions are all built here from
// this site's own colours. There is no Microsoft logo, no Luna artwork, no borrowed
// icon set, and the wallpaper is the site's own night meadow.
//
// This phase builds the shell only. Every control that looks operable is operable:
// the Start button opens a real menu, the menu item really leaves, the window really
// closes, and the clock shows the real time. Nothing here is a painted-on affordance.

import { esc } from '../lib/html.js';

/** The three window controls, at the size the era actually used. */
const windowButtons = () => `      <div class="win__buttons">
        <button class="win__btn win__btn--min" type="button" data-window-min
                aria-label="Minimise this window"><span aria-hidden="true"></span></button>
        <button class="win__btn win__btn--max" type="button" disabled
                aria-label="Maximise (this window cannot be resized)"><span aria-hidden="true"></span></button>
        <button class="win__btn win__btn--close" type="button" data-window-close
                aria-label="Close this window"><span aria-hidden="true"></span></button>
      </div>`;

export function desktop({ heading, note, items }) {
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
    <section class="win" data-window aria-labelledby="win-title">
      <div class="win__bar">
        <span class="win__icon" aria-hidden="true"></span>
        <h1 class="win__title" id="win-title">${esc(heading)}</h1>
${windowButtons()}
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
        <span class="win__status-cell win__status-grip" aria-hidden="true"></span>
      </div>
    </section>
  </div>

  <div class="taskbar">
    <button class="tb-start" type="button" data-start
            aria-expanded="false" aria-controls="start-menu">
      <span class="tb-start__glyph" aria-hidden="true"></span><span class="tb-start__word">start</span>
    </button>
    <div class="tb-tasks">
      <button class="tb-task" type="button" data-task aria-pressed="true">
        <span class="win__icon win__icon--small" aria-hidden="true"></span>${esc(heading)}
      </button>
    </div>
    <div class="tb-tray">
      <span class="tb-tray__icon" aria-hidden="true"></span>
      <span class="tb-clock" data-clock role="status" aria-label="Current time"></span>
    </div>
  </div>

  <div class="start-menu" id="start-menu" data-start-menu hidden>
    <div class="start-menu__head">
      <span class="start-menu__avatar" aria-hidden="true"></span>
      <span class="start-menu__user">${esc(heading)}</span>
    </div>
    <ul class="start-menu__list">
      <li>
        <button class="start-menu__item" type="button" data-restore>
          <span class="start-menu__icon" aria-hidden="true"></span>
          <span><strong>Reopen window</strong><small>Show the window again</small></span>
        </button>
      </li>
    </ul>
    <div class="start-menu__foot">
      <button class="start-menu__leave" type="button" data-leave>
        <span class="start-menu__icon start-menu__icon--door" aria-hidden="true"></span>Back to the room
      </button>
    </div>
  </div>
</div>`;
}
