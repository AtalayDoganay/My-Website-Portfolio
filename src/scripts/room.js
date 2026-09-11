/* ===========================================================================
   The opening scene's behaviour: the typed introduction, the invitation on
   hover/focus/touch, and the flight into the screen.

   Three explicit states live on [data-room]:
     intro     - the machine is typing, and can be entered
     entering  - the zoom is running; input is ignored
     gone      - the room is out of the way and the desktop has it

   One timer drives the typing. It is cleared on pause and on entering, so
   there is never a second one running behind it.
   ========================================================================= */

(function () {
  'use strict';

  // --- Tunable ------------------------------------------------------------
  var TUNING = {
    typeMs: 85, //  per character while typing
    periodMs: 450, //  between each trailing period
    holdMs: 900, //  the pause before the line is erased
    deleteMs: 45, //  per character while erasing
    enterMs: 1400, //  the flight into the screen
    desktopAt: 0.6, //  fraction of enterMs when the real desktop starts fading in
    fadeMs: 380, //  desktop fade, matches .desktop transition
    reducedMs: 160, //  the whole transition, when motion is reduced
  };

  var LINE_ONE = 'Welcome to my website';
  var LINE_TWO = 'Hii, my name is Atalay Doganay...';
  var INVITE_POINTER = 'Click to know about me';
  var INVITE_TOUCH = 'Tap to know about me';

  var room = document.querySelector('[data-room]');
  var desktop = document.querySelector('[data-desktop]');
  if (!room || !desktop) return;

  var world = room.querySelector('[data-world]');
  var screenEl = room.querySelector('[data-screen]');
  var lineEl = room.querySelector('[data-line]');
  var hintEl = room.querySelector('[data-hint]');
  var startBtn = desktop.querySelector('[data-start]');
  var startMenu = desktop.querySelector('[data-start-menu]');
  var leaveBtn = desktop.querySelector('[data-leave]');
  var clockEl = desktop.querySelector('[data-clock]');
  var windowEl = desktop.querySelector('[data-window]');
  var taskBtn = desktop.querySelector('[data-task]');
  var restoreBtn = desktop.querySelector('[data-restore]');
  var closeBtn = desktop.querySelector('[data-window-close]');
  var minBtn = desktop.querySelector('[data-window-min]');

  var reduceQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  var hoverQuery = window.matchMedia('(hover: hover) and (pointer: fine)');

  // --- pixel scale --------------------------------------------------------
  // The artwork is drawn at 216x150 and must only ever be shown at a whole-number
  // multiple, or source pixels land on fractions of device pixels and the edges
  // crawl as the window resizes. The composition adapts by changing which whole
  // number it uses, never by taking a fractional one.
  var WIDE = { w: 216, h: 150 };
  var NARROW = { w: 120, h: 126 };
  var narrowQuery = window.matchMedia('(max-width: 34rem), (max-height: 26rem)');
  var WALL_W = 240;
  var WALL_H = 150;

  function applyScale() {
    var root = document.documentElement;
    var vw = window.innerWidth;
    var vh = window.innerHeight;
    var landscapePhone = vh < 520 && vw > vh;

    // How much of the viewport the machine may take. Narrow screens give it more,
    // which is what keeps the tube readable instead of merely smaller.
    var widthShare = vw < 560 ? 1.0 : 0.95;
    var heightShare = landscapePhone ? 0.88 : vw < 560 ? 0.7 : 0.78;

    var art = narrowQuery.matches ? NARROW : WIDE;
    var scale = Math.floor(Math.min((vw * widthShare) / art.w, (vh * heightShare) / art.h));
    scale = Math.max(1, Math.min(scale, 12));
    root.style.setProperty('--px-scale', String(scale));

    // The wallpaper is covered rather than fitted, so it rounds up.
    var wall = Math.ceil(Math.max(vw / WALL_W, vh / WALL_H));
    root.style.setProperty('--wall-scale', String(Math.max(1, wall)));
  }

  applyScale();

  // --- The script, flattened to one frame per step ------------------------
  // Each entry is the complete line as it should read after `delay` has passed.
  // Holding the whole string (rather than appending) keeps the display exact no
  // matter where the sequence is paused and resumed.
  var frames = [];
  function frame(delay, value) {
    frames.push({ delay: delay, value: value });
  }

  (function buildFrames() {
    var i;
    for (i = 1; i <= LINE_ONE.length; i += 1) frame(TUNING.typeMs, LINE_ONE.slice(0, i));
    frame(TUNING.periodMs, LINE_ONE + '.');
    frame(TUNING.periodMs, LINE_ONE + '..');
    frame(TUNING.periodMs, LINE_ONE + '...');

    var full = LINE_ONE + '...';
    frame(TUNING.holdMs, full); // hold the finished line
    for (i = full.length - 1; i >= 0; i -= 1) frame(TUNING.deleteMs, full.slice(0, i));
    for (i = 1; i <= LINE_TWO.length; i += 1) frame(TUNING.typeMs, LINE_TWO.slice(0, i));
  })();

  // --- Typing state -------------------------------------------------------
  var cursor = 0; // index of the next frame to apply
  var text = ''; // what the machine believes is on the glass
  var timer = null;
  var paused = false;
  var hovering = false;
  var focused = false;
  var state = 'intro';
  var enterTimers = [];
  var clockTimer = null;

  function stopTimer() {
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function invite() {
    return hoverQuery.matches ? INVITE_POINTER : INVITE_TOUCH;
  }

  function render() {
    lineEl.textContent = paused ? invite() : text;
    // The caret holds steady while characters are arriving and blinks when the
    // machine is waiting for you.
    var running = !paused && cursor < frames.length;
    room.dataset.typing = running ? 'running' : 'resting';
  }

  function run() {
    if (paused || state !== 'intro') return;
    if (cursor >= frames.length) {
      render();
      return;
    }
    var next = frames[cursor];
    stopTimer();
    timer = setTimeout(function () {
      timer = null;
      text = next.value;
      cursor += 1;
      render();
      run();
    }, next.delay);
  }

  function pause() {
    if (paused) return;
    paused = true;
    stopTimer(); // the pending frame is not consumed; cursor stays put
    render();
  }

  function resume() {
    if (!paused) return;
    paused = false;
    render(); // puts the previous text back, character for character
    run(); // and carries on from the same frame
  }

  function refreshInvitation() {
    var hot = hovering || focused;
    room.dataset.hot = hot ? 'on' : 'off';
    if (hot) pause();
    else resume();
  }

  function resetIntro() {
    stopTimer();
    cursor = 0;
    text = '';
    paused = false;
    hovering = false;
    focused = false;
    room.dataset.hot = 'off';
    if (reduceQuery.matches) {
      // No typewriter: show the finished introduction straight away.
      cursor = frames.length;
      text = LINE_TWO;
      render();
    } else {
      render();
      run();
    }
  }

  // --- Entering -----------------------------------------------------------

  function clearEnterTimers() {
    enterTimers.forEach(clearTimeout);
    enterTimers = [];
  }

  function showDesktop() {
    if (desktop.hasAttribute('data-shown')) return;
    desktop.hidden = false;
    desktop.removeAttribute('inert');
    void desktop.offsetWidth; // commit the unhidden state before transitioning
    desktop.setAttribute('data-shown', '');
  }

  function finishEnter() {
    if (state === 'desktop') return;
    clearEnterTimers();
    showDesktop();
    state = 'desktop';
    room.dataset.state = 'gone';
    room.inert = true;
    showWindow(true);   // every arrival looks the same
    // Release the scaled layer a frame later, once the room is out of sight.
    requestAnimationFrame(function () {
      world.style.transform = '';
      world.style.transformOrigin = '';
    });
    startClock();
    if (startBtn) startBtn.focus();
  }

  function enter() {
    if (state !== 'intro') return; // repeated activation does nothing
    state = 'entering';
    room.dataset.state = 'entering';
    stopTimer(); // no obsolete typing behind the transition
    paused = true;

    if (reduceQuery.matches) {
      enterTimers.push(setTimeout(finishEnter, TUNING.reducedMs));
      return;
    }

    // Fly from the screen's real rect: scale until it covers the viewport, and
    // slide its centre to the viewport centre. Everything else - bezel, desk,
    // room - is carried along and leaves the frame.
    var box = screenEl.getBoundingClientRect();
    var vw = window.innerWidth;
    var vh = window.innerHeight;
    var scale = Math.max(vw / box.width, vh / box.height);
    var cx = box.left + box.width / 2;
    var cy = box.top + box.height / 2;
    var origin = world.getBoundingClientRect();

    world.style.transformOrigin = cx - origin.left + 'px ' + (cy - origin.top) + 'px';

    requestAnimationFrame(function () {
      world.style.transform =
        'translate(' + (vw / 2 - cx) + 'px, ' + (vh / 2 - cy) + 'px) scale(' + scale + ')';
    });

    enterTimers.push(setTimeout(showDesktop, TUNING.enterMs * TUNING.desktopAt));
    enterTimers.push(setTimeout(finishEnter, TUNING.enterMs + 80));
  }

  function leave() {
    if (state !== 'desktop') return;
    closeStartMenu();
    stopClock();
    desktop.removeAttribute('data-shown');
    setTimeout(function () {
      if (state !== 'desktop') {
        desktop.hidden = true;
        desktop.setAttribute('inert', '');
      }
    }, TUNING.fadeMs);

    state = 'intro';
    room.dataset.state = 'intro';
    room.inert = false;
    resetIntro();
    if (screenEl) screenEl.focus();
  }

  // --- The window ---------------------------------------------------------
  // Minimise and close both put the window away; the taskbar button and the Start
  // menu bring it back. Nothing here pretends to do something it does not do.

  function showWindow(show) {
    if (!windowEl) return;
    windowEl.hidden = !show;
    if (taskBtn) taskBtn.setAttribute('aria-pressed', show ? 'true' : 'false');
  }

  // --- Start menu ---------------------------------------------------------

  function openStartMenu() {
    if (!startMenu) return;
    startMenu.hidden = false;
    startBtn.setAttribute('aria-expanded', 'true');
    if (leaveBtn) leaveBtn.focus();
  }

  function closeStartMenu() {
    if (!startMenu || startMenu.hidden) return;
    startMenu.hidden = true;
    startBtn.setAttribute('aria-expanded', 'false');
  }

  function toggleStartMenu() {
    if (startMenu.hidden) openStartMenu();
    else {
      closeStartMenu();
      startBtn.focus();
    }
  }

  // --- Clock --------------------------------------------------------------

  function paintClock() {
    if (!clockEl) return;
    clockEl.textContent = new Date().toLocaleTimeString([], {
      hour: 'numeric',
      minute: '2-digit',
    });
  }

  function startClock() {
    paintClock();
    stopClock();
    clockTimer = setInterval(paintClock, 20000);
  }

  function stopClock() {
    if (clockTimer !== null) {
      clearInterval(clockTimer);
      clockTimer = null;
    }
  }

  // --- Wiring -------------------------------------------------------------

  screenEl.addEventListener('click', enter);

  screenEl.addEventListener('pointerenter', function (event) {
    if (event.pointerType !== 'mouse' || !hoverQuery.matches) return;
    hovering = true;
    refreshInvitation();
  });

  screenEl.addEventListener('pointerleave', function () {
    if (!hovering) return;
    hovering = false;
    refreshInvitation();
  });

  screenEl.addEventListener('focus', function () {
    // Only a keyboard-style focus is an invitation; clicking should not pause.
    if (!screenEl.matches(':focus-visible')) return;
    focused = true;
    refreshInvitation();
  });

  screenEl.addEventListener('blur', function () {
    if (!focused) return;
    focused = false;
    refreshInvitation();
  });

  if (startBtn) startBtn.addEventListener('click', toggleStartMenu);
  if (leaveBtn) leaveBtn.addEventListener('click', leave);

  if (closeBtn) closeBtn.addEventListener('click', function () {
    showWindow(false);
    if (taskBtn) taskBtn.focus();
  });
  if (minBtn) minBtn.addEventListener('click', function () {
    showWindow(false);
    if (taskBtn) taskBtn.focus();
  });
  if (taskBtn) taskBtn.addEventListener('click', function () {
    showWindow(windowEl.hidden);
  });
  if (restoreBtn) restoreBtn.addEventListener('click', function () {
    showWindow(true);
    closeStartMenu();
    if (closeBtn) closeBtn.focus();
  });

  document.addEventListener('click', function (event) {
    if (state !== 'desktop' || !startMenu || startMenu.hidden) return;
    if (startMenu.contains(event.target) || startBtn.contains(event.target)) return;
    closeStartMenu();
  });

  document.addEventListener('keydown', function (event) {
    if (event.key !== 'Escape') return;
    if (startMenu && !startMenu.hidden) {
      closeStartMenu();
      startBtn.focus();
    } else if (state === 'desktop') {
      leave();
    }
  });

  // A resize mid-flight would leave the zoom aimed at a rect that no longer
  // exists, so land immediately rather than sit between states.
  var resizeTimer = null;
  window.addEventListener('resize', function () {
    // A resize mid-flight would leave the zoom aimed at a rect that no longer
    // exists, so land immediately rather than sit between states.
    if (state === 'entering') finishEnter();
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(applyScale, 80);
  });
  window.addEventListener('orientationchange', function () {
    setTimeout(applyScale, 120);
  });

  // Changing the theme must not disturb anything: it only swaps palettes and which
  // artwork is shown. The sequence, the window state and the transition are all
  // untouched, and this listener exists only to keep the pixel scale correct if a
  // theme ever changes the composition's metrics.
  document.addEventListener('themechange', applyScale);

  // Touch has no hover, so the invitation is always on the glass.
  function applyPointerMode() {
    if (hoverQuery.matches) {
      room.dataset.invite = 'off';
      hintEl.textContent = '';
    } else {
      room.dataset.invite = 'on';
      hintEl.textContent = INVITE_TOUCH;
    }
  }
  applyPointerMode();
  if (hoverQuery.addEventListener) hoverQuery.addEventListener('change', applyPointerMode);

  if (reduceQuery.addEventListener) {
    reduceQuery.addEventListener('change', function () {
      if (state === 'intro') resetIntro();
    });
  }

  // Start once the terminal face is in, so the line does not reflow under the
  // caret. Capped, so a slow font never holds the introduction hostage.
  var started = false;
  function begin() {
    if (started) return;
    started = true;
    resetIntro();
  }
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(begin);
    setTimeout(begin, 600);
  } else {
    begin();
  }
})();
