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
     boot              - empty hold, three dots, three individual backspaces
     typing            - the two lines are printing, character by character
     revealing-room    - the camera is pulling back
     room-ready        - the room is up; a glove demonstrates a vertical press
     entering-desktop  - the camera is pushing in; input is ignored
     desktop           - the room is out of the way and the desktop has it

   ONE timer drives the introduction. Each step schedules the next, so there is
   never a second one behind it and a backgrounded tab cannot build a queue. The
   invitation uses CSS animations. A cancellable rAF observes their playhead
   for sound cues; it never schedules a separate repeating audio clock.

   Intro/camera durations are in TUNING. Invitation phases live in CSS keyframes.
   ========================================================================= */

(function () {
  'use strict';

  // --- Tunable ------------------------------------------------------------
  var TUNING = {
    bootHoldMs: 650, //  the lit tube alone, no text, before the first dot
    bootDotMs: 400, //  between each of the three dots
    bootClearMs: 400, //  the third dot's hold, before the first backspace
    backspaceMs: 120, //  between individual dot removals
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
    inviteCycleMs: 3600, // approach, a 100ms press, a 150ms lift, a 1900ms fade, ~1s dark; CSS uses this same duration and cues read its keyframes
  };

  var LINE_ONE = 'Welcome to my website...';
  var LINE_TWO = 'Hi, my name is Atalay Doganay...';
  var SPOKEN = 'Welcome to my website. Hi, my name is Atalay Doganay.';
  var INVITE_POINTER = 'CLICK!';
  var INVITE_TOUCH = 'TAP!';
  var SEEN_KEY = 'atalay.intro';

  // The sound control says what it will do, in the three states it can be in.
  var SOUND_ON_LABEL = 'Play intro with sound';
  var SOUND_OFF_LABEL = 'Mute';
  var SOUND_FAIL_LABEL = 'Sound unavailable';

  var root = document.documentElement;
  var room = document.querySelector('[data-room]');
  var desktop = document.querySelector('[data-desktop]');
  if (!room || !desktop) return;

  var world = room.querySelector('[data-world]');
  var screenEl = room.querySelector('[data-screen]');
  // The portfolio labels are part of the room. While the camera is pushed in,
  // during the move and on the desktop they are not usable, so they are inert
  // then: neither focusable nor clickable. setState keeps this in step.
  var lampsEl = room.querySelector('[data-lamps]');
  if (lampsEl) lampsEl.inert = true;
  var waitRow = room.querySelector('[data-line="1"]');
  var goBtn = room.querySelector('[data-go]');
  var goLabel = room.querySelector('[data-go-label]');
  var revealBtn = room.querySelector('[data-reveal]');
  var controls = room.querySelector('[data-intro-controls]');
  var skipBtn = room.querySelector('[data-skip]');
  var soundBtn = room.querySelector('[data-sound]');
  var spokenEl = room.querySelector('[data-spoken]');
  var handEl = room.querySelector('.invite__hand');
  var particleEl = room.querySelector('.burst__bit');
  room.style.setProperty('--invite-cycle', TUNING.inviteCycleMs + 'ms');
  if (handEl) {
    handEl.style.setProperty('--tip-x', handEl.dataset.tipX);
    handEl.style.setProperty('--tip-y', handEl.dataset.tipY);
  }

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
  var WIDE = { w: 576, h: 330 };
  var NARROW = { w: 180, h: 252 };
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
  // A browser will not let a page make a noise until someone has interacted
  // with it, and no amount of delay gets around that: a context created
  // without a gesture is born `suspended` and stays there. So the opening
  // always PLAYS silently, and sound is offered as an explicit replay.
  //
  // The path is short, and every part of it is checked before a note is made:
  //
  //     oscillator -> its own envelope gain -> MASTER gain -> ctx.destination
  //
  // The master gain is the mute and the one place the output level is set, so
  // muting is a single value change rather than a walk over live nodes.
  //
  // Nothing is ever scheduled ahead of the step happening now, so there is no
  // queue to accumulate while a tab is in the background - which is what keeps
  // `silence()` bounded: cancel the automation already written onto each live
  // gain, take it to zero over a few milliseconds so stopping does not click,
  // and stop the oscillator.

  var AudioCtx = window.AudioContext || window.webkitAudioContext;
  var MASTER_LEVEL = 0.6;
  var audio = null;
  var master = null;
  var soundOn = false;

  if (!AudioCtx && soundBtn) soundBtn.hidden = true;

  /** Build the context and the master gain. Safe to call repeatedly. */
  function buildAudio() {
    if (audio && master) return true;
    if (!AudioCtx) return false;
    try {
      audio = new AudioCtx();
      master = audio.createGain();
      master.gain.setValueAtTime(MASTER_LEVEL, audio.currentTime);
      master.connect(audio.destination);
    } catch (err) {
      audio = null;
      master = null;
      if (soundBtn) soundBtn.hidden = true;
      return false;
    }
    return true;
  }

  /** Resume the context, and resolve with whether it is ACTUALLY running.
   *
   * resume() is asynchronous. The previous version called it and then asked
   * straight away whether the context was running - which it is not yet - so
   * the first note after turning sound on was always dropped. Everything that
   * makes a sound now waits on this. Older WebKit returns undefined instead of
   * a promise, so that is normalised rather than assumed.
   */
  function unlockAudio() {
    if (!buildAudio()) return Promise.resolve(false);
    if (audio.state === 'running') return Promise.resolve(true);
    var resumed;
    try {
      resumed = audio.resume();
    } catch (err) {
      return Promise.resolve(false);
    }
    if (!resumed || typeof resumed.then !== 'function') {
      return Promise.resolve(audio.state === 'running');
    }
    return resumed.then(
      function () { return audio.state === 'running'; },
      function () { return false; }
    );
  }

  function audioReady() {
    return soundOn && document.visibilityState === 'visible' && !pageGone &&
      !!audio && !!master && audio.state === 'running';
  }

  // Every voice currently sounding, as the pair that has to be shut down.
  var voices = [];

  function voice(type, freq, ms, peak) {
    if (!audioReady()) return false;
    var now = audio.currentTime;
    var osc = audio.createOscillator();
    var gain = audio.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, now);
    // An exponential ramp cannot start at or pass through zero, so the floor
    // is a value below hearing rather than silence itself.
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(peak, now + 0.006);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + ms / 1000);
    osc.connect(gain);
    gain.connect(master);
    osc.start(now);
    osc.stop(now + ms / 1000 + 0.02);
    var live = { osc: osc, gain: gain };
    voices.push(live);
    osc.onended = function () {
      var at = voices.indexOf(live);
      if (at > -1) voices.splice(at, 1);
      try { osc.disconnect(); gain.disconnect(); } catch (err) { /* gone */ }
    };
    return true;
  }

  /** A short computer beep. One per dot. */
  function beep(freq, ms) {
    return voice('square', freq, ms, 0.16);
  }

  /** A soft key click, pitched a little differently each time so a line of
   *  them does not turn into one continuous tone. Spaces make no sound. */
  function keyClick(ch) {
    if (ch === ' ') return false;
    return voice('triangle', 1500 + ((ch.charCodeAt(0) * 37) % 260), 26, 0.075);
  }

  /** The return key: lower, and a touch longer than a letter. */
  function returnKey() {
    return voice('triangle', 680, 70, 0.1);
  }

  function backspace() {
    return voice('triangle', 420, 38, 0.075);
  }

  /** Filtered noise for a mechanical click and a softer particle-flight breath.
   * Both use the same master and cancellable voice list as the terminal. */
  function noise(ms, peak, high, low) {
    if (!audioReady()) return false;
    var now = audio.currentTime;
    var count = Math.ceil(audio.sampleRate * ms / 1000);
    var buffer = audio.createBuffer(1, count, audio.sampleRate);
    var data = buffer.getChannelData(0);
    for (var i = 0; i < count; i += 1) data[i] = Math.random() * 2 - 1;
    var source = audio.createBufferSource();
    source.buffer = buffer;
    var filter = audio.createBiquadFilter();
    filter.type = 'bandpass';
    filter.Q.value = 0.7;
    filter.frequency.setValueAtTime(high, now);
    filter.frequency.exponentialRampToValueAtTime(low, now + ms / 1000);
    var gain = audio.createGain();
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(peak, now + Math.min(0.018, ms / 4000));
    gain.gain.exponentialRampToValueAtTime(0.0001, now + ms / 1000);
    source.connect(filter);
    filter.connect(gain);
    gain.connect(master);
    var live = { osc: source, gain: gain };
    voices.push(live);
    source.onended = function () {
      var at = voices.indexOf(live);
      if (at > -1) voices.splice(at, 1);
      source.disconnect(); filter.disconnect(); gain.disconnect();
    };
    source.start(now);
    source.stop(now + ms / 1000);
    return true;
  }

  function mouseClick() { return noise(24, 0.15, 3600, 1400); }
  function particleFlight() { return noise(210, 0.045, 2800, 850); }

  /** Stop everything currently sounding - skip, mute, entry, or navigation.
   *
   * Cancelling the automation first is the part that matters: without it the
   * ramp already written onto the gain keeps running and the note finishes its
   * decay after it was supposed to have been stopped.
   */
  function silence() {
    if (!audio) { voices.length = 0; return; }
    var now = audio.currentTime;
    while (voices.length) {
      var live = voices.pop();
      try {
        live.gain.gain.cancelScheduledValues(now);
        live.gain.gain.setValueAtTime(Math.max(live.gain.gain.value, 0.0001), now);
        live.gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.004);
        live.osc.stop(now + 0.006);
      } catch (err) {
        /* already stopped */
      }
    }
  }

  function paintSoundButton() {
    if (!soundBtn) return;
    soundBtn.setAttribute('aria-pressed', soundOn ? 'true' : 'false');
    soundBtn.textContent = soundOn ? SOUND_OFF_LABEL : SOUND_ON_LABEL;
  }

  /** Mute: silence what is sounding now, and shut the one gain they all pass
   *  through so nothing later gets out either. */
  function muteSound() {
    soundOn = false;
    inviteMuted = true;
    stopInvitation();
    if (state === 'room-ready') room.dataset.invite = 'still';
    silence();
    if (master && audio) {
      try {
        master.gain.cancelScheduledValues(audio.currentTime);
        master.gain.setValueAtTime(0, audio.currentTime);
      } catch (err) { /* nothing live */ }
    }
    paintSoundButton();
  }

  /** The explicit, clearly labelled way to hear the opening.
   *
   * This is the only thing that turns sound on, and it only ever runs from a
   * real click or tap, because that is the only thing a browser accepts as
   * permission to make a noise. It replays the short opening from its initial
   * hold so all three beeps are actually heard. That is a deliberate replay on
   * request - not the intro playing again on every refresh.
   */
  function playIntroWithSound() {
    if (!soundBtn) return;
    if (soundOn) { muteSound(); return; }
    unlockAudio().then(function (running) {
      if (pageGone || document.visibilityState !== 'visible' ||
          state === 'desktop' || state === 'entering-desktop') return;
      if (!running) {
        // Permission refused, or there is no output device. Say so, rather
        // than leaving a pressed button that plays nothing.
        soundOn = false;
        paintSoundButton();
        soundBtn.disabled = true;
        soundBtn.textContent = SOUND_FAIL_LABEL;
        return;
      }
      soundOn = true;
      inviteMuted = false;
      try {
        master.gain.cancelScheduledValues(audio.currentTime);
        master.gain.setValueAtTime(MASTER_LEVEL, audio.currentTime);
      } catch (err) { /* fresh context */ }
      paintSoundButton();
      replayIntro();
      if (reduceQuery.matches && state === 'room-ready') startInvitation();
    });
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
    if (lampsEl) lampsEl.inert = next !== 'room-ready';
    if (next !== 'room-ready' && room.dataset.links === 'open') setLinks(false);
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

    // A. The tube is already lit and showing its own texture, with NOTHING on
    // it. It holds like that, and only then do the three dots arrive, one per
    // beep, evenly spaced. From the start of the opening:
    //
    //      650ms  .     beep one
    //     1050ms  ..    beep two
    //     1450ms  ...   beep three
    //     1850ms  ..    backspace one
    //     1970ms  .     backspace two
    //     2090ms        backspace three; typing follows
    //
    // The first delay is the hold; the other two are the gap between dots.
    for (i = 1; i <= 3; i += 1) {
      (function (n) {
        step(n === 1 ? TUNING.bootHoldMs : TUNING.bootDotMs, function () {
          caretRow = 1;
          lines[0] = new Array(n + 1).join('.');
          paint();
          beep(700, 70);
        });
      })(i);
    }
    for (i = 2; i >= 0; i -= 1) {
      (function (remaining) {
        step(remaining === 2 ? TUNING.bootClearMs : TUNING.backspaceMs, function () {
          lines[0] = new Array(remaining + 1).join('.');
          if (remaining === 0) setState('typing');
          paint();
          backspace();
        });
      })(i);
    }

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

  /** Skip has nothing left to skip once the room is up, but the sound control
   *  still has something to offer, so it stays. That is what makes the replay
   *  reachable: the opening is short, and without this the only way to hear it
   *  would be to click within the few seconds it is still running. */
  function hideControls() {
    if (skipBtn) skipBtn.hidden = true;
    if (controls && (!soundBtn || soundBtn.hidden)) controls.hidden = true;
  }

  /** Put the opening back to its first frame and play it again, with sound.
   *
   * Reached only from the sound control, so it always follows a real gesture.
   * Everything in flight is torn down first - the timer, the camera, any live
   * voice and the invitation - so a replay during the pullback cannot leave a
   * second animation running behind this one.
   */
  function replayIntro() {
    if (reduceQuery.matches) return;
    stopTimer();
    stopCamera();
    stopRevealTimer();
    clearEnterTimers();
    silence();
    stopInvitation();
    if (goBtn) {
      goBtn.hidden = true;
      goBtn.removeAttribute('data-pressed');
    }
    room.dataset.lines = 'on';
    lines[0] = '';
    lines[1] = '';
    caretRow = 0;
    typing = true;
    paint();
    if (spokenEl) spokenEl.textContent = '';
    if (skipBtn) skipBtn.hidden = false;
    if (controls) controls.hidden = false;
    setState('boot');
    measure();
    applyPose(poseAt(0));
    startedAt = Date.now();
    buildSequence();
    runSteps();
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

  var inviteFrame = null;
  var inviteMuted = false;
  var pageGone = false;
  var cueRun = null;

  function invitationAnimation(el, name) {
    return el && el.getAnimations().find(function (a) { return a.animationName === name; });
  }

  /** Follow the rendered CSS animation's playhead. The contact and first visible
   * flight offsets COME FROM its keyframes, so editing CSS cannot leave an
   * independent audio timer running at the old phase. Missed frames are dropped. */
  function followInvitation(realPress, continuing) {
    if (inviteFrame !== null) cancelAnimationFrame(inviteFrame);
    inviteFrame = null;
    if (reduceQuery.matches || pageGone || document.visibilityState !== 'visible') return;
    var hand = invitationAnimation(handEl, realPress ? 'hand-fire' : 'invite-hand');
    var flight = invitationAnimation(particleEl, realPress ? 'burst-fire' : 'burst');
    if (!hand || !flight) return;
    var duration = flight.effect.getTiming().duration;
    var frames = hand.effect.getKeyframes();
    var contactAt = realPress ? 0 : frames[2].computedOffset * duration;
    // The lamps stop taking input part-way through their fade, at the lamp
    // keyframe where pointer-events turns off. A lamp that still has keyboard
    // focus hands it back on that beat - never on a real press, which is
    // already on its way into the desktop.
    var releaseAt = realPress ? Infinity : lampCutoff(duration);
    var visible = flight.effect.getKeyframes().find(function (f) { return Number(f.opacity) > 0; });
    if (!visible) return;
    var flightAt = visible.computedOffset * duration;
    cueRun = continuing || { cycle: -1, contact: realPress, flight: false, release: false };
    if (realPress && audible()) mouseClick();
    function tick() {
      inviteFrame = null;
      if (pageGone || document.visibilityState !== 'visible' ||
          !['on', 'fire', 'finish'].includes(room.dataset.invite)) return;
      var elapsed = Number(flight.currentTime || 0);
      var cycle = realPress ? 0 : Math.floor(elapsed / duration);
      var t = realPress ? elapsed : elapsed % duration;
      if (cycle !== cueRun.cycle) {
        cueRun.cycle = cycle;
        cueRun.contact = realPress;
        cueRun.flight = false;
        cueRun.release = false;
      }
      if (flight.playState === 'running') {
        if (!cueRun.contact && t >= contactAt) {
          cueRun.contact = true;
          if (audible() && t - contactAt < 80) mouseClick();
        }
        if (!cueRun.flight && t >= flightAt) {
          cueRun.flight = true;
          if (audible() && t - flightAt < 80) particleFlight();
        }
        if (!cueRun.release && t >= releaseAt) {
          cueRun.release = true;
          returnFocusFromLamps();
        }
      }
      if (flight.playState !== 'finished') inviteFrame = requestAnimationFrame(tick);
    }
    inviteFrame = requestAnimationFrame(tick);
  }

  /** The beat, in ms of the cycle, on which the lamps refuse the pointer: read
   *  from their own keyframes, so the CSS fade can be retimed freely. */
  function lampCutoff(duration) {
    var lamp = lampsEl && lampsEl.querySelector('.lamp');
    var anim = invitationAnimation(lamp, 'lamp-cycle');
    if (!anim) return Infinity;
    var keys = anim.effect.getKeyframes();
    var live = false;
    for (var i = 0; i < keys.length; i++) {
      if (keys[i].pointerEvents === 'auto') live = true;
      else if (live && keys[i].pointerEvents === 'none') return keys[i].computedOffset * duration;
    }
    return Infinity;
  }

  /** The beat, in ms of the cycle, on which the lamps refuse the pointer: read
   *  from their own keyframes, so the CSS fade can be retimed freely. */
  function lampCutoff(duration) {
    var lamp = lampsEl && lampsEl.querySelector('.lamp');
    var anim = invitationAnimation(lamp, 'lamp-cycle');
    if (!anim) return Infinity;
    var keys = anim.effect.getKeyframes();
    var live = false;
    for (var i = 0; i < keys.length; i++) {
      if (keys[i].pointerEvents === 'auto') live = true;
      else if (live && keys[i].pointerEvents === 'none') return keys[i].computedOffset * duration;
    }
    return Infinity;
  }

  /** Sound is offered, never taken: the same observer runs silently until it is. */
  function audible() {
    return soundOn && !inviteMuted;
  }

  /** Focus must never be left on a lamp that is going dark. */
  function returnFocusFromLamps() {
    if (!lampsEl || room.dataset.links === 'open') return;
    var active = document.activeElement;
    if (!active || !lampsEl.contains(active)) return;
    var target = revealBtn || goBtn;
    if (target) target.focus({ preventScroll: true });
  }

  /** The manual reveal: a steady, fully lit menu until it is closed. While it
   *  is open the demonstration rests - the stylesheet removes its animations,
   *  so the glove sits raised and nothing cues - and the observer re-binds to
   *  the fresh animations when the menu closes. */
  function setLinks(open) {
    room.dataset.links = open ? 'open' : 'closed';
    if (revealBtn) {
      revealBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      revealBtn.textContent = open ? revealBtn.dataset.hide : revealBtn.dataset.show;
    }
    if (open) {
      if (inviteFrame !== null) cancelAnimationFrame(inviteFrame);
      inviteFrame = null;
    } else if (state === 'room-ready' && room.dataset.invite === 'on') {
      followInvitation(false);
    }
  }
  if (revealBtn) {
    revealBtn.addEventListener('click', function () {
      setLinks(room.dataset.links !== 'open');
    });
  }

  function inviteWord() {
    return hoverQuery.matches ? INVITE_POINTER : INVITE_TOUCH;
  }

  function startInvitation() {
    if (goLabel) goLabel.textContent = inviteWord();
    if (pageGone || inviteMuted || document.visibilityState !== 'visible') {
      room.dataset.invite = 'still';
      return;
    }
    if (room.dataset.invite === 'on') return;
    room.dataset.invite = 'on';
    followInvitation(false);
  }

  function stopInvitation() {
    if (inviteFrame !== null) cancelAnimationFrame(inviteFrame);
    inviteFrame = null;
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
    var demo = invitationAnimation(handEl, 'invite-hand');
    var phase = demo ? Number(demo.currentTime) % TUNING.inviteCycleMs : -1;
    var frames = demo ? demo.effect.getKeyframes() : [];
    // A click arriving while the demonstrated burst is still in flight accepts
    // that press. Finish its existing flight once; don't launch a second
    // burst/noise over it. The window runs from contact to the burst keyframe
    // where its last piece is gone.
    var flight = invitationAnimation(particleEl, 'burst');
    var flightKeys = flight ? flight.effect.getKeyframes() : [];
    var lastLit = -1;
    flightKeys.forEach(function (f, i) { if (Number(f.opacity) > 0) lastLit = i; });
    var flightEnd = lastLit >= 0 && lastLit + 1 < flightKeys.length
      ? flightKeys[lastLit + 1].computedOffset * TUNING.inviteCycleMs : -1;
    var acceptPress = demo && phase >= frames[2].computedOffset * TUNING.inviteCycleMs &&
      phase <= flightEnd;
    var previousCues = cueRun;
    setState('entering-desktop');
    if (inviteFrame !== null) cancelAnimationFrame(inviteFrame);
    inviteFrame = null;
    if (acceptPress && !inviteMuted && !reduceQuery.matches) {
      // Rewind to THIS iteration before limiting it to one. Changing iterations
      // first makes a later-cycle CSS animation finish and leave getAnimations().
      room.querySelectorAll('.invite__hand, .crt__go-face, .burst__bit').forEach(function (el) {
        el.getAnimations().forEach(function (a) { a.currentTime = phase; });
      });
      room.dataset.invite = 'finish';
      if (previousCues) previousCues.cycle = 0;
      followInvitation(false, previousCues);
    } else {
      silence();
      room.dataset.invite = inviteMuted ? 'still' : 'fire';
      if (!inviteMuted) followInvitation(true);
    }
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
    stopInvitation();
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
  if (soundBtn) {
    paintSoundButton();
    soundBtn.addEventListener('click', playIntroWithSound);
  }

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
    } else if (state === 'room-ready' && room.dataset.links === 'open') {
      setLinks(false); // Escape closes the manual menu and returns to its control
      if (revealBtn) revealBtn.focus();
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
    TUNING.bootHoldMs + 2 * TUNING.bootDotMs + TUNING.bootClearMs +
    2 * TUNING.backspaceMs +
    (LINE_ONE.length + LINE_TWO.length) * TUNING.typeMs + TUNING.lineHoldMs +
    TUNING.newlineMs + TUNING.doneHoldMs + TUNING.pullbackMs + 4000;

  window.addEventListener('pagehide', function () {
    pageGone = true;
    stopTimer(); stopRevealTimer(); stopCamera(); clearEnterTimers(); stopClock();
    stopInvitation(); silence();
  });
  window.addEventListener('pageshow', function () {
    if (!pageGone) return;
    pageGone = false;
    if (state === 'entering-desktop') finishEnter();
    else if (state === 'desktop') startClock();
    else if (state === 'room-ready') startInvitation();
    else skipIntro(false);
  });

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState !== 'visible') {
      stopInvitation(); silence();
      if (state === 'room-ready') room.dataset.invite = 'still';
      return;
    }
    if (state === 'room-ready') startInvitation();
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
      stopInvitation(); silence();
      if (state === 'room-ready') startInvitation();
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
    // The tube is lit and carries its own texture, but nothing is printed on
    // it yet - not even a caret. The first dot arrives after the hold.
    caretRow = 0;
    typing = true;
    lines[0] = '';
    lines[1] = '';
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
