/* ===========================================================================
   Theme state for the whole site.

   Loaded SYNCHRONOUSLY in <head>, before any pixel is painted, so the correct
   theme is on <html> from the first frame and nothing flashes. That is also why
   this is a separate file rather than an inline script: it keeps the site's
   "no inline script anywhere" rule intact while still blocking paint.

   Order of preference:
     1. an explicit choice the visitor made, remembered in localStorage
     2. the operating system's preference
   The OS is followed live only while no explicit choice is stored.

   Toggles are bound by delegation, so this can run before any button exists and
   every page gets a working control without shipping a second script.
   ========================================================================= */

(function () {
  'use strict';

  var KEY = 'atalay.theme';
  var THEMES = { dark: 1, light: 1 };
  var root = document.documentElement;
  var media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: light)') : null;

  // If storage is unavailable - private mode, blocked cookies - switching still
  // has to work for this page, so the choice is held in memory as well.
  var memory = null;

  function stored() {
    try {
      var value = window.localStorage.getItem(KEY);
      return THEMES[value] ? value : null;
    } catch (err) {
      return null;
    }
  }

  function remember(theme) {
    memory = theme;
    try {
      window.localStorage.setItem(KEY, theme);
      return true;
    } catch (err) {
      return false;
    }
  }

  function systemTheme() {
    return media && media.matches ? 'light' : 'dark';
  }

  function apply(theme) {
    root.setAttribute('data-theme', theme);
    // Tell the browser too, so form controls and scrollbars follow.
    root.style.colorScheme = theme;
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', theme === 'light' ? '#E7EFF9' : '#070A18');
  }

  function chosen() {
    return stored() || memory;
  }

  apply(chosen() || systemTheme());

  // --- toggles ------------------------------------------------------------

  function syncToggles() {
    var theme = root.getAttribute('data-theme');
    var next = theme === 'dark' ? 'light' : 'dark';
    var nodes = document.querySelectorAll('[data-theme-toggle]');
    for (var i = 0; i < nodes.length; i += 1) {
      nodes[i].setAttribute('aria-label', 'Switch to the ' + next + ' theme');
      nodes[i].setAttribute('title', 'Switch to the ' + next + ' theme');
    }
  }

  function setTheme(theme) {
    if (!THEMES[theme]) return;
    apply(theme);
    remember(theme);
    syncToggles();
    document.dispatchEvent(new CustomEvent('themechange', { detail: { theme: theme } }));
  }

  document.addEventListener('click', function (event) {
    var target = event.target.closest ? event.target.closest('[data-theme-toggle]') : null;
    if (!target) return;
    event.preventDefault();
    setTheme(root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
  });

  if (media && media.addEventListener) {
    media.addEventListener('change', function () {
      // Only follow the system while the visitor has not chosen for themselves.
      if (chosen()) return;
      apply(systemTheme());
      syncToggles();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', syncToggles);
  } else {
    syncToggles();
  }

  window.siteTheme = { get: function () { return root.getAttribute('data-theme'); }, set: setTheme };
})();
