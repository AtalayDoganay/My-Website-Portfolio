/* ===========================================================================
   The opening scene's behaviour.

   ONE SCENE, ONE CAMERA. `.room__world` holds every physical thing - wall,
   grain, the tube's glow, the tabletop band that continues the desk past the
   artwork, the monitor, bezel, stand, tower, keyboard, mouse and cables - and a
   single transform on that element is the camera. There are exactly two poses:

     CLOSE - the monitor's glass covers the viewport
     REST  - the finished composition, translate(0,0) scale(1)

   The opening starts at CLOSE and pulls back to REST. Clicking pushes back to
   CLOSE and hands over to the desktop. Because one transform moves the whole
   scene, the equipment and the desk necessarily change size together and things
   outside the first frame arrive as the camera retreats; nothing is a separate
   display shrinking over a settled room.

   The introduction is printed into `.crt__glass`, which has `overflow: hidden`,
   so the text is attached to the physical glass and clipped by it at every
   frame - including the first one, when the camera is pushed all the way in.

   Six explicit states live on [data-room]:
     boot              - the tube is waiting; "Wait", then the dots
     typing            - the two lines are printing, character by character
     revealing-room    - the camera is pulling back
     room-ready        - the room is up, the introduction stands, the hand waves
     entering-desktop  - the camera is pushing in; input is ignored
     desktop           - the room is out of the way and the desktop has it

   ONE timer drives the introduction. Each step schedules the next, so there is
   never a second one behind it and a backgrounded tab cannot build a queue. The
   invitation is a CSS cycle on a container: no timer, nothing accumulating, and
   stopping it is one attribute.

   Every duration is in TUNING.
   ========================================================================= */

(function () {
  'use strict';

  // --- Tunable ------------------------------------------------------------
  var TUNING = {
    bootDotMs: 400, //  between each of the three dots
    bootHoldMs: 400, //  after the third dot, before typing starts
    typeMs: 42, //  per character
    lineHoldMs: 240, //  after the first line is complete
    newlineMs: 290, //  the carriage return onto the second line
    doneHoldMs: 480, //  both lines complete, before the camera moves
    pullbackMs: 1500, //  the camera retreating to the finished room (1.3-1.7s)
    clearLinesAt: 0.3, //  fraction of the pullback when the introduction clears
    pressHoldMs: 240, //  the press and burst before the camera starts moving
    burstLingerMs: 620, //  how long the burst stays up once entry has begun
    reducedMs: 260, //  the whole opening, when motion is reduced
    enterMs: 1150, //  the camera pushing back in on the glass
    desktopAt: 0.62, //  fraction of enterMs when the real desktop fades in
    fadeMs: 380, //  desktop fade, matches .desktop transition
  };

  var LINE_ONE = 'Welcome to my website...';
  var LINE_TWO = 'Hi, my name is Atalay Doganay...';
  var SPOKEN = 'Welcome to my website. Hi, my name is Atalay Doganay.';
  var INVITE_POINTER = 'CLICK!';
  var INVITE_TOUCH = 'TAP!';
  var SEEN_KEY = 'atalay.intro';

  var root = document.documentElement;
  var room = document.querySelector('[data-room]');
  var desktop = document.querySelector('[data-desktop]');
  if (!room || !desktop) return;

  var world = room.querySelector('[data-world]');
  var screenEl = room.querySelector('[data-screen]');
  var waitRow = room.querySelector('[data-line="1"]');
  var goBtn = room.querySelector('[data-go]');
  var goLabel = room.querySelector('[data-go-label]');
  var controls = room.querySelector('[data-intro-controls]');
  var skipBtn = room.querySelector('[data-skip]');
  var soundBtn = room.querySelector('[data-sound]');
  var spokenEl = room.querySelector('[data-spoken]');

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
  // The artwork is shown at a whole-number multiple AT REST, which is where the
  // pixel grid matters. The camera is free to pass through fractional scales
  // while it moves - snapping it to integers would make the pullback stutter.
  var WIDE = { w: 340, h: 180 };
  var NARROW = { w: 120, h: 168 };
  var narrowQuery = window.matchMedia(
    '(max-width: 34rem), (max-height: 26rem) and (max-width: 44rem),' +
      ' (orientation: portrait) and (max-width: 48rem)'
  );
  var WALL_W = 240;
  var WALL_H = 150;

  function applyScale() {
    var vw = window.innerWidth;
    var vh = window.innerHeight;
    var landscapePhone = vh < 520 && vw > vh;
    var widthShare = vw < 560 ? 1.0 : 0.96;
    var heightShare = landscapePhone ? 0.94 : vw < 560 ? 0.82 : 0.92;

    var art = narrowQuery.matches ? NARROW : WIDE;
    var scale = Math.floor(Math.min((vw * widthShare) / art.w, (vh * heightShare) / art.h));
    scale = Math.max(1, Math.min(scale, 12));
    root.style.setProperty('--px-scale', String(scale));

    var wall = Math.ceil(Math.max(vw / WALL_W, vh / WALL_H));
    root.style.setProperty('--wall-scale', String(Math.max(1, wall)));
  }

  applyScale();

  // --- the camera ---------------------------------------------------------

  var camAnim = null;
  var pose = { x: 0, y: 0, k: 1 };

  function transformOf(p) {
    return 'translate(' + p.x + 'px, ' + p.y + 'px) scale(' + p.k + ')';
  }

  function applyPose(p) {
    pose = p;
    world.style.transform = transformOf(p);
  }

  /** Measure the glass in the world's own coordinates.
   *
   * Taken with the camera at rest, because getBoundingClientRect reports the
   * TRANSFORMED box: reading it mid-move would compound the scale already
   * applied. The world's untransformed box is the viewport, so the screen's
   * rect in that state is also its position in the world's own coordinates.
   */
  var anchor = { x: 0, y: 0, k: 1 };

  function measure() {
    var previous = world.style.transform;
    world.style.transform = 'none';
    var worldBox = world.getBoundingClientRect();
    var glass = screenEl.getBoundingClientRect();

    // How far the longest printed line reaches from the middle of the glass, in
    // the glass's own layout pixels. Measured here, inside the untransformed
    // window, because it is what limits how far the camera may push in: the
    // readout is inset from the left edge, so the line is off-centre and its
    // left reach is the larger of the two.
    var reach = 0;
    if (waitRow) {
      var keep = waitRow.textContent;
      waitRow.textContent = LINE_TWO;
      var row = waitRow.getBoundingClientRect();
      var cx = glass.left + glass.width / 2;
      reach = Math.max(cx - row.left, row.right - cx);
      waitRow.textContent = keep;
    }
    world.style.transform = previous;

    var vw = window.innerWidth;
    var vh = window.innerHeight;
    if (!glass.width || !glass.height) {
      anchor = { x: vw / 2, y: vh / 2, k: 1 };
      return;
    }

    // Push in far enough that the glass covers the viewport - but never so far
    // that the introduction runs off the sides. A tall portrait phone needs
    // 5.9x to cover a 4:3 tube, and at 5.9x a thirty-character line is more than
    // twice the width of the screen. The line wins: the text has to be readable
    // the whole way through, and the pullback still starts right up against the
    // glass.
    var cover = Math.max(vw / glass.width, vh / glass.height);
    var fits = reach > 0 ? (vw / 2 - 14) / reach : cover;
    anchor = {
      x: glass.left - worldBox.left + glass.width / 2,
      y: glass.top - worldBox.top + glass.height / 2,
      k: Math.max(1, Math.min(cover, fits)),
    };
  }

  /** The camera pose at progress p: 0 is pushed in on the glass, 1 is the room.
   *
   * The scale is interpolated GEOMETRICALLY, not linearly. Linear interpolation
   * of a 5x scale spends most of the move within a whisker of the finished size
   * - halfway through a 5x pullback it is already at 1.3x, so the midpoint shows
   * a settled room rather than enlarged equipment. Geometric interpolation makes
   * each equal slice of time cover an equal RATIO, which is what reads as a
   * constant-speed dolly: halfway is sqrt(5) = 2.2x.
   *
   * The glass's centre is carried from the viewport centre to where it belongs
   * in the finished composition, so the camera is aimed at the tube the whole
   * way and everything else arrives around it.
   */
  function poseAt(p) {
    var k = Math.pow(anchor.k, 1 - p);
    var ax = window.innerWidth / 2 + (anchor.x - window.innerWidth / 2) * p;
    var ay = window.innerHeight / 2 + (anchor.y - window.innerHeight / 2) * p;
    return { x: ax - k * anchor.x, y: ay - k * anchor.y, k: k };
  }

  var REST = { x: 0, y: 0, k: 1 };

  /** Ease in and out, and exactly linear through the middle, so the midpoint
   *  lands where the geometry above intends it to. */
  function smoothstep(t) {
    return t * t * (3 - 2 * t);
  }

  /** Move the camera between two progress points, once.
   *
   * The destination is written to the inline style first, so the scene is
   * already correct if the animation is cancelled, interrupted, or unsupported.
   * The path is sampled into keyframes because the ease lives in the geometry,
   * not in a timing function. will-change goes on only for the duration of the
   * move - per the GSAP performance guidance - and comes off at the end, so the
   * artwork rasterises crisply at rest.
   */
  function moveCamera(fromP, toP, ms, done) {
    stopCamera();
    applyPose(poseAt(toP));
    if (!world.animate || reduceQuery.matches || ms <= 0) {
      if (done) done();
      return;
    }
    var frames = [];
    var steps = 30;
    for (var i = 0; i <= steps; i += 1) {
      var t = i / steps;
      var p = fromP + (toP - fromP) * smoothstep(t);
      frames.push({ offset: t, transform: transformOf(poseAt(p)) });
    }
    world.style.willChange = 'transform';
    camAnim = world.animate(frames, { duration: ms, easing: 'linear', fill: 'backwards' });
    camAnim.onfinish = function () {
      world.style.willChange = '';
      camAnim = null;
      if (done) done();
    };
    camAnim.oncancel = function () {
      world.style.willChange = '';
    };
  }

  function stopCamera() {
    if (camAnim) {
      camAnim.cancel();
      camAnim = null;
    }
    world.style.willChange = '';
  }

  // --- Sound --------------------------------------------------------------
  // Browsers block audio until a real gesture, so the introduction always runs
  // silently unless someone turns it on. Nothing is ever queued: a beep is
  // played by the step that is happening now, or not at all.

  var AudioCtx = window.AudioContext || window.webkitAudioContext;
  var audio = null;
  var soundOn = false;

  if (!AudioCtx && soundBtn) soundBtn.hidden = true;

  function toggleSound() {
    if (!AudioCtx || !soundBtn) return;
    if (soundOn) {
      soundOn = false;
    } else {
      try {
        if (!audio) audio = new AudioCtx();
        if (audio.state === 'suspended') audio.resume();
        soundOn = true;
      } catch (err) {
        soundBtn.hidden = true;
        return;
      }
    }
    soundBtn.setAttribute('aria-pressed', soundOn ? 'true' : 'false');
    if (soundOn) beep(880, 60);
    else silence();
  }

  // Every node that is currently making a sound, so an interruption can stop
  // all of them at once. Nothing is ever scheduled ahead: a sound belongs to the
  // step that is happening now, or it does not happen.
  var voices = [];

  function voice(type, freq, ms, peak) {
    if (!soundOn || !audio || audio.state !== 'running') return;
    var now = audio.currentTime;
    var osc = audio.createOscillator();
    var gain = audio.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, now);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(peak, now + 0.006);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + ms / 1000);
    osc.connect(gain);
    gain.connect(audio.destination);
    osc.start(now);
    osc.stop(now + ms / 1000 + 0.02);
    voices.push(osc);
    osc.onended = function () {
      var at = voices.indexOf(osc);
      if (at > -1) voices.splice(at, 1);
      osc.disconnect();
      gain.disconnect();
    };
  }

  /** A short, quiet computer beep. One per dot. */
  function beep(freq, ms) {
    voice('square', freq, ms, 0.05);
  }

  /** A soft key click, pitched a little differently each time so a line of
   *  them does not turn into one continuous tone. Spaces make no sound. */
  function keyClick(ch) {
    if (ch === ' ') return;
    voice('triangle', 1500 + ((ch.charCodeAt(0) * 37) % 260), 26, 0.022);
  }

  /** The return key: lower, and a touch longer than a letter. */
  function returnKey() {
    voice('triangle', 680, 70, 0.032);
  }

  /** Stop everything currently sounding - skip, entry, or navigation. */
  function silence() {
    while (voices.length) {
      var osc = voices.pop();
      try {
        osc.stop();
      } catch (err) {
        /* already stopped */
      }
    }
  }

  // --- The two lines ------------------------------------------------------

  var lines = ['', ''];
  var caretRow = 0; // 1, 2, or 0 for none
  var typing = false;

  function paintInto(selector, value) {
    var els = room.querySelectorAll(selector);
    for (var i = 0; i < els.length; i += 1) els[i].textContent = value;
  }

  function paintCaret(rowIndex, on) {
    var els = room.querySelectorAll('[data-caret="' + rowIndex + '"]');
    for (var i = 0; i < els.length; i += 1) {
      els[i].classList.toggle('is-on', on);
      els[i].classList.toggle('is-steady', on && typing);
    }
  }

  function paint() {
    paintInto('[data-line="1"]', lines[0]);
    paintInto('[data-line="2"]', lines[1]);
    paintCaret(1, caretRow === 1);
    paintCaret(2, caretRow === 2);
  }

  function announce() {
    if (spokenEl && spokenEl.textContent !== SPOKEN) spokenEl.textContent = SPOKEN;
  }

  // --- State --------------------------------------------------------------

  var state = 'boot';
  var timer = null;
  var enterTimers = [];
  var clockTimer = null;
  var steps = [];
  var cursor = 0;
  var startedAt = Date.now();
  var hovering = false;
  var focused = false;

  function setState(next) {
    state = next;
    room.dataset.state = next;
  }

  function stopTimer() {
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function step(delay, fn) {
    steps.push({ d: delay, fn: fn });
  }

  function runSteps() {
    stopTimer();
    if (cursor >= steps.length) return;
    var next = steps[cursor];
    timer = setTimeout(function () {
      timer = null;
      cursor += 1;
      if (next.fn) next.fn();
      runSteps();
    }, next.d);
  }

  function buildSequence() {
    steps = [];
    cursor = 0;
    var i;

    // A. the tube wakes up: a dot straight away, then two more, then a hold.
    for (i = 2; i <= 3; i += 1) {
      (function (n) {
        step(TUNING.bootDotMs, function () {
          lines[0] = new Array(n + 1).join('.');
          paint();
          beep(700, 70);
        });
      })(i);
    }
    step(TUNING.bootHoldMs, function () {
      lines[0] = '';
      setState('typing');
      paint();
    });

    // B. the introduction prints, a character at a time.
    for (i = 1; i <= LINE_ONE.length; i += 1) {
      (function (k) {
        step(TUNING.typeMs, function () {
          lines[0] = LINE_ONE.slice(0, k);
          paint();
          keyClick(LINE_ONE.charAt(k - 1));
        });
      })(i);
    }
    step(TUNING.lineHoldMs, null);
    step(TUNING.newlineMs, function () {
      caretRow = 2; // the cursor drops to the next line; line one stays
      paint();
      returnKey();
    });
    for (i = 1; i <= LINE_TWO.length; i += 1) {
      (function (k) {
        step(TUNING.typeMs, function () {
          lines[1] = LINE_TWO.slice(0, k);
          paint();
          keyClick(LINE_TWO.charAt(k - 1));
        });
      })(i);
    }

    // C. hold both lines, then pull the camera back through the whole scene.
    step(TUNING.doneHoldMs, function () {
      typing = false;
      announce();
      paint();
    });
    step(0, startPullback);
  }

  // --- C. the pullback ----------------------------------------------------

  function startPullback() {
    if (state !== 'boot' && state !== 'typing') return;
    stopTimer();
    setState('revealing-room');
    typing = false;
    caretRow = 0;
    paint();
    moveCamera(0, 1, reduceQuery.matches ? 0 : TUNING.pullbackMs, finishPullback);
    if (reduceQuery.matches) return finishPullback();
    // Part way back, the introduction clears and the invitation takes the glass.
    revealTimer = setTimeout(showInvitation,
                             TUNING.pullbackMs * TUNING.clearLinesAt);
  }

  function finishPullback() {
    if (state === 'room-ready') return;
    stopCamera();
    stopRevealTimer();
    applyPose(REST);
    hideControls();
    setState('room-ready');
    rememberIntro();
    showInvitation();
  }

  /** Clear the printed introduction and put the button on the glass. */
  function showInvitation() {
    stopRevealTimer();
    room.dataset.lines = 'off';
    lines[0] = '';
    lines[1] = '';
    caretRow = 0;
    typing = false;
    paint();
    if (goBtn) goBtn.hidden = false;
    startInvitation();
  }

  var revealTimer = null;

  function stopRevealTimer() {
    if (revealTimer !== null) {
      clearTimeout(revealTimer);
      revealTimer = null;
    }
  }

  /** Resolve immediately to the finished room, from any point in the opening. */
  function skipIntro(focusScreen) {
    if (state !== 'boot' && state !== 'typing' && state !== 'revealing-room') return;
    stopTimer();
    stopCamera();
    silence();
    cursor = steps.length;
    announce();
    applyPose(REST);
    hideControls();
    setState('room-ready');
    rememberIntro();
    showInvitation();
    if (focusScreen && goBtn) goBtn.focus();
  }

  function hideControls() {
    if (controls) controls.hidden = true;
  }

  function rememberIntro() {
    try {
      window.sessionStorage.setItem(SEEN_KEY, '1');
    } catch (err) {
      /* private mode: the introduction simply plays again */
    }
  }

  function introAlreadySeen() {
    try {
      return window.sessionStorage.getItem(SEEN_KEY) === '1';
    } catch (err) {
      return false;
    }
  }

  // --- D. the invitation --------------------------------------------------

  function inviteWord() {
    return hoverQuery.matches ? INVITE_POINTER : INVITE_TOUCH;
  }

  function startInvitation() {
    if (goLabel) goLabel.textContent = inviteWord();
    room.dataset.invite = 'on';
  }

  function stopInvitation() {
    room.dataset.invite = 'off';
  }

  function refreshHot() {
    var hot = hovering || focused;
    room.dataset.hot = hot ? 'on' : 'off';
  }

  // --- E. entering the desktop -------------------------------------------

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
    clearInvitation();
    stopCamera();
    showDesktop();
    setState('desktop');
    room.inert = true;
    showWindow(true);
    applyPose(REST); // the room is hidden now; leave the camera where it belongs
    startClock();
    if (startBtn) startBtn.focus();
  }

  /** A real click, tap, Enter or Space. Presses the button, fires one burst,
   *  and only then starts the camera - so the burst is still on screen as the
   *  entry begins rather than being deleted on the triggering frame.
   *
   *  The state moves out of `room-ready` immediately, which is what stops a
   *  second press from starting a second transition.
   */
  function activate() {
    if (state !== 'room-ready') return;
    setState('entering-desktop');
    silence();
    room.dataset.invite = 'fire';
    if (goBtn) goBtn.setAttribute('data-pressed', '');

    if (reduceQuery.matches) {
      enterTimers.push(setTimeout(startEntry, 80));
      enterTimers.push(setTimeout(clearInvitation, 200));
      return;
    }
    enterTimers.push(setTimeout(startEntry, TUNING.pressHoldMs));
    enterTimers.push(setTimeout(clearInvitation,
                                TUNING.pressHoldMs + TUNING.burstLingerMs));
  }

  function clearInvitation() {
    room.dataset.invite = 'off';
    if (goBtn) {
      goBtn.removeAttribute('data-pressed');
      goBtn.hidden = true;
    }
  }

  function startEntry() {
    if (state !== 'entering-desktop') return;

    if (reduceQuery.matches) {
      enterTimers.push(setTimeout(finishEnter, TUNING.reducedMs));
      return;
    }

    // The same camera, pushed back in on the same glass.
    measure();
    moveCamera(1, 0, TUNING.enterMs, null);
    enterTimers.push(setTimeout(showDesktop, TUNING.enterMs * TUNING.desktopAt));
    enterTimers.push(setTimeout(finishEnter, TUNING.enterMs + 70));
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

    // Back to the finished room, never back through the opening.
    applyPose(REST);
    setState('room-ready');
    room.inert = false;
    hovering = false;
    focused = false;
    refreshHot();
    showInvitation();
    if (goBtn) goBtn.focus();
  }

  // --- The window ---------------------------------------------------------

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

  if (skipBtn) skipBtn.addEventListener('click', function () { skipIntro(true); });
  if (soundBtn) soundBtn.addEventListener('click', toggleSound);

  // The button is a real one, so click, Enter and Space all arrive here.
  if (goBtn) {
    goBtn.addEventListener('click', activate);
    goBtn.addEventListener('pointerdown', function () {
      if (state === 'room-ready') goBtn.setAttribute('data-pressed', '');
    });
    goBtn.addEventListener('pointerup', function () {
      if (state === 'room-ready') goBtn.removeAttribute('data-pressed');
    });
    goBtn.addEventListener('pointerleave', function () {
      if (state === 'room-ready') goBtn.removeAttribute('data-pressed');
    });
    goBtn.addEventListener('pointerenter', function (event) {
      if (event.pointerType !== 'mouse' || !hoverQuery.matches) return;
      hovering = true;
      refreshHot();
    });
    goBtn.addEventListener('pointerleave', function () {
      if (!hovering) return;
      hovering = false;
      refreshHot();
    });
    goBtn.addEventListener('focus', function () {
      if (!goBtn.matches(':focus-visible')) return;
      focused = true;
      refreshHot();
    });
    goBtn.addEventListener('blur', function () {
      if (!focused) return;
      focused = false;
      refreshHot();
    });
  }

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
    if (state === 'boot' || state === 'typing' || state === 'revealing-room') {
      skipIntro(true); // Escape is the keyboard's Skip
    } else if (startMenu && !startMenu.hidden) {
      closeStartMenu();
      startBtn.focus();
    } else if (state === 'desktop') {
      leave();
    }
  });

  var resizeTimer = null;
  window.addEventListener('resize', onResize);
  window.addEventListener('orientationchange', function () {
    setTimeout(onResize, 120);
  });

  function onResize() {
    // A move mid-flight is aimed at a rect that no longer exists, so land it
    // rather than sit between states.
    if (state === 'entering-desktop') finishEnter();
    if (state === 'revealing-room') finishPullback();
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      applyScale();
      // The camera pose is measured from the screen's rect, which the new scale
      // has just moved, so anything still parked at CLOSE has to be re-aimed.
      if (state === 'boot' || state === 'typing') { measure(); applyPose(poseAt(0)); }
    }, 80);
  }

  // A backgrounded tab throttles timers. One chained timer cannot build up a
  // queue, but it can come back a long way behind, so if the opening has
  // outlived its whole budget it resolves to the finished room.
  var BUDGET =
    2 * TUNING.bootDotMs + TUNING.bootHoldMs +
    (LINE_ONE.length + LINE_TWO.length) * TUNING.typeMs + TUNING.lineHoldMs +
    TUNING.newlineMs + TUNING.doneHoldMs + TUNING.pullbackMs + 4000;

  window.addEventListener('pagehide', silence);

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState !== 'visible') { silence(); return; }
    if (state !== 'boot' && state !== 'typing') return;
    if (Date.now() - startedAt > BUDGET) skipIntro(false);
  });

  // Changing the theme only swaps palettes and which artwork is shown. The
  // camera, the state and the printed lines are untouched.
  document.addEventListener('themechange', function () {
    applyScale();
    if (state === 'boot' || state === 'typing') { measure(); applyPose(poseAt(0)); }
  });

  function applyPointerMode() {
    if (goLabel) goLabel.textContent = inviteWord();
  }
  if (hoverQuery.addEventListener) hoverQuery.addEventListener('change', applyPointerMode);

  if (reduceQuery.addEventListener) {
    reduceQuery.addEventListener('change', function () {
      if (state === 'boot' || state === 'typing') skipIntro(false);
    });
  }

  // --- Go -----------------------------------------------------------------
  // A returning visitor - back from an inner page, or out of the desktop and in
  // again - gets the finished room, not the opening a second time.

  if (introAlreadySeen()) {
    skipIntro(false);
  } else if (reduceQuery.matches) {
    // No character animation: the completed introduction, then the room.
    lines[0] = LINE_ONE;
    lines[1] = LINE_TWO;
    caretRow = 0;
    paint();
    announce();
    measure();
    applyPose(poseAt(0));
    setState('typing');
    setTimeout(startPullback, TUNING.reducedMs);
  } else {
    measure();
    applyPose(poseAt(0)); // start pushed in on the glass
    caretRow = 1;
    typing = true;
    lines[0] = '.'; // the first dot is already there; two more follow
    paint();
    // Start once the terminal face is in, so the line does not reflow under the
    // caret. Capped, so a slow font never holds the introduction hostage.
    var started = false;
    var begin = function () {
      if (started || state !== 'boot') return;
      started = true;
      measure(); // re-aim: the font may have changed the metrics
      applyPose(poseAt(0));
      startedAt = Date.now();
      buildSequence();
      runSteps();
    };
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(begin);
      setTimeout(begin, 600);
    } else {
      begin();
    }
  }
})();
