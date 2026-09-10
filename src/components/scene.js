// The signature scene: a lit doorway standing alone in a meadow under drifting cloud.
// Original artwork, drawn as inline SVG so it stays crisp, weighs almost nothing, and
// takes its colours from the design tokens. No external image files, nothing fetched.
//
// Two variants share one composition, so moving between pages feels like staying put:
//   'field'   - the full scene, with the doorway. Home only.
//   'horizon' - the same land seen from further off, no doorway. Inner pages.
//
// Colours use var(--token, literal) so the scene still renders if a token is renamed.

import { esc } from '../lib/html.js';

// Cloud lobes. Four silhouettes rather than one repeated shape, so a band never
// reads as the same cutout stamped along a line.
const FORMS = [
  [[0, -6, 76, 26], [-50, 2, 44, 18], [46, 3, 50, 16], [-18, -25, 40, 26], [26, -16, 31, 20]],
  [[-6, -4, 62, 22], [-56, 3, 38, 15], [38, 1, 58, 19], [-30, -20, 34, 22], [18, -22, 44, 25]],
  [[8, -5, 84, 24], [-52, 4, 50, 17], [58, 5, 38, 13], [-6, -22, 46, 24], [-40, -14, 28, 17]],
  [[0, -3, 58, 20], [-42, 2, 52, 18], [44, 2, 44, 15], [-14, -19, 36, 22], [22, -14, 30, 18]],
];

/** A cumulus: overlapping lobes on a flat base, the way a cloud actually reads. */
const cumulus = (x, y, s, form = 0) => {
  const lobes = FORMS[form % FORMS.length];
  const width = Math.max(...lobes.map(([cx, , rx]) => Math.abs(cx) + rx));
  return (
    `<g transform="translate(${x} ${y}) scale(${s})">` +
    `<rect x="${-width}" y="-3" width="${width * 2}" height="17" rx="8.5"/>` +
    lobes.map(([cx, cy, rx, ry]) => `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}"/>`).join('') +
    '</g>'
  );
};

/** A far-off streak: what a cloud becomes near the horizon. */
const streak = (x, y, w, h) =>
  `<g transform="translate(${x} ${y})">` +
  `<rect x="${-w / 2}" y="${-h / 2}" width="${w}" height="${h}" rx="${h / 2}"/>` +
  `<ellipse cx="${-w * 0.16}" cy="${-h * 0.5}" rx="${w * 0.2}" ry="${h * 0.9}"/>` +
  `<ellipse cx="${w * 0.2}" cy="${-h * 0.35}" rx="${w * 0.15}" ry="${h * 0.7}"/>` +
  '</g>';

// Higher in the frame reads as nearer, so those clouds are larger and drift faster.
// Spacing is deliberately uneven: evenly spread clouds look like wallpaper.
const BANDS = {
  near: [cumulus(180, 150, 1.0, 0), cumulus(450, 108, 0.72, 2), cumulus(1010, 138, 0.92, 1),
         cumulus(1250, 176, 0.6, 3), cumulus(1510, 116, 0.82, 2)].join(''),
  mid: [cumulus(70, 244, 0.6, 1), cumulus(300, 218, 0.44, 3), cumulus(690, 252, 0.66, 0),
        cumulus(1120, 230, 0.52, 2), cumulus(1380, 256, 0.58, 1)].join(''),
  far: [
    streak(120, 332, 190, 12),
    streak(430, 346, 140, 9),
    streak(620, 336, 96, 7),
    streak(880, 330, 210, 11),
    streak(1180, 348, 130, 8),
    streak(1450, 334, 170, 10),
  ].join(''),
};

// The doorway. Its base sits inside the field; its top rises above the horizon line.
// Everything below the base is where the light falls, so it is kept clear of the
// mist that carries the field down into the page.
const DOORWAY = `
  <g class="scene__doorway">
    <ellipse class="scene__bloom" cx="800" cy="378" rx="150" ry="165"
             fill="var(--door-light, #F6E7C0)" filter="url(#sc-bloom)"/>
    <path class="scene__spill" d="M735 470 L865 470 L952 596 L648 596 Z"
          fill="var(--door-light, #F6E7C0)" filter="url(#sc-haze)" opacity=".62"/>
    <rect x="761" y="280" width="78" height="190" fill="url(#sc-opening)"/>
    <path d="M736 266 h128 v16 h-128 z" fill="var(--frame-lit, #EEE7D7)"/>
    <path d="M736 266 h128 v5 h-128 z" fill="#FBF7EC"/>
    <path d="M748 282 h13 v188 h-13 z" fill="var(--frame-lit, #EEE7D7)"/>
    <path d="M736 282 h12 v188 h-12 z" fill="#DDD5C2"/>
    <path d="M839 282 h13 v188 h-13 z" fill="var(--frame-shade, #C8C0AD)"/>
    <path d="M852 282 h12 v188 h-12 z" fill="#B5AD9A"/>
    <ellipse cx="808" cy="471" rx="66" ry="6" fill="#63795A" opacity=".3" filter="url(#sc-contact)"/>
  </g>`;

/**
 * @param {{variant?: 'field'|'horizon', label?: string}} options
 */
export function scene({ variant = 'horizon', label = '' } = {}) {
  const isField = variant === 'field';
  // The full scene is the page's focal image and is described. The horizon strip on
  // inner pages repeats it as atmosphere only, so it is hidden from assistive tech.
  const semantics = isField ? ` role="img" aria-label="${esc(label)}"` : ' aria-hidden="true"';
  // The strip is short, so it takes its own crop through the horizon rather than the
  // full frame - otherwise almost all of it is empty sky with the land squeezed out.
  const viewBox = isField ? '0 0 1600 600' : '0 190 1600 330';

  return `<div class="scene scene--${esc(variant)}">
  <svg class="scene__art" viewBox="${viewBox}" preserveAspectRatio="xMidYMid slice"
       focusable="false"${semantics}>
    <defs>
      <linearGradient id="sc-sky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0"   stop-color="var(--sky-high, #9FC4E2)"/>
        <stop offset=".30" stop-color="var(--sky, #C3D9E8)"/>
        <stop offset=".52" stop-color="var(--haze, #D9D3E6)"/>
        <stop offset=".62" stop-color="#E5DCE4"/>
        <stop offset="1"   stop-color="#F1EAE0"/>
      </linearGradient>
      <!-- Clouds take their tone from their height: bright overhead, dimmer near the land. -->
      <linearGradient id="sc-cloud" x1="0" y1="40" x2="0" y2="370" gradientUnits="userSpaceOnUse">
        <stop offset="0"   stop-color="#FDFCFA"/>
        <stop offset=".55" stop-color="#F0EEF6"/>
        <stop offset="1"   stop-color="#DCD6E6"/>
      </linearGradient>
      <!-- The field is hazy where it meets the sky, richest through the middle, and
           dissolves into low mist in the near foreground - which is what carries the
           landscape down into the page instead of stopping at a hard edge. -->
      <linearGradient id="sc-meadow" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0"   stop-color="#C6D0BB"/>
        <stop offset=".28" stop-color="#AEBFA0"/>
        <stop offset=".58" stop-color="var(--meadow-deep, #93A985)"/>
        <stop offset=".86" stop-color="#B6C1A7"/>
        <stop offset="1"   stop-color="#DCDACA"/>
      </linearGradient>
      <linearGradient id="sc-opening" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0"   stop-color="#FFFDF6"/>
        <stop offset=".45" stop-color="#FBF0D4"/>
        <stop offset="1"   stop-color="var(--door-light, #F6E7C0)"/>
      </linearGradient>
      <radialGradient id="sc-sun" cx=".5" cy=".5" r=".5">
        <stop offset="0" stop-color="#FFF4DC" stop-opacity=".9"/>
        <stop offset="1" stop-color="#FFF4DC" stop-opacity="0"/>
      </radialGradient>
      <linearGradient id="sc-grassfade" x1="0" y1="392" x2="0" y2="600" gradientUnits="userSpaceOnUse">
        <stop offset="0"   stop-color="#000"/>
        <stop offset=".45" stop-color="#777"/>
        <stop offset="1"   stop-color="#fff"/>
      </linearGradient>
      <mask id="sc-grassmask">
        <rect x="0" y="392" width="1600" height="208" fill="url(#sc-grassfade)"/>
      </mask>
      <!-- Two tile sizes with no common factor, so the texture never bands. -->
      <pattern id="sc-grass-a" width="11" height="13" patternUnits="userSpaceOnUse">
        <path d="M2 13 q1.3 -5 0.3 -8" stroke="#67805C" stroke-width=".9" fill="none" stroke-linecap="round"/>
        <path d="M8 13 q-1.1 -4 0.2 -6.5" stroke="#728A66" stroke-width=".9" fill="none" stroke-linecap="round"/>
      </pattern>
      <pattern id="sc-grass-b" width="17" height="19" patternUnits="userSpaceOnUse">
        <path d="M5 19 q1.7 -7 0.4 -11" stroke="#5E7754" stroke-width=".9" fill="none" stroke-linecap="round"/>
        <path d="M13 19 q-1.5 -6 0.3 -9" stroke="#7B9370" stroke-width=".9" fill="none" stroke-linecap="round"/>
      </pattern>
      <filter id="sc-cloud-near" x="-20%" y="-80%" width="140%" height="260%"><feGaussianBlur stdDeviation="11"/></filter>
      <filter id="sc-cloud-mid" x="-20%" y="-80%" width="140%" height="260%"><feGaussianBlur stdDeviation="9"/></filter>
      <filter id="sc-cloud-far" x="-20%" y="-80%" width="140%" height="260%"><feGaussianBlur stdDeviation="5"/></filter>
      <filter id="sc-contact" x="-60%" y="-300%" width="220%" height="700%"><feGaussianBlur stdDeviation="5"/></filter>
      <filter id="sc-soft" x="-40%" y="-200%" width="180%" height="500%"><feGaussianBlur stdDeviation="10"/></filter>
      <filter id="sc-haze" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="30"/></filter>
      <filter id="sc-bloom" x="-90%" y="-90%" width="280%" height="280%"><feGaussianBlur stdDeviation="48"/></filter>

      <g id="sc-near">${BANDS.near}</g>
      <g id="sc-mid">${BANDS.mid}</g>
      <g id="sc-far">${BANDS.far}</g>
    </defs>

    <rect width="1600" height="600" fill="url(#sc-sky)"/>
    <ellipse cx="800" cy="352" rx="640" ry="230" fill="url(#sc-sun)"/>

    <g class="scene__clouds scene__clouds--far" fill="url(#sc-cloud)" opacity=".4" filter="url(#sc-cloud-far)">
      <use href="#sc-far"/><use href="#sc-far" x="1600"/>
    </g>

    <!-- Two ridges, each a tone darker than the one behind it: distance, made visible. -->
    <path d="M0 380 C 210 360, 380 376, 560 368 C 760 358, 900 380, 1080 370
             C 1260 360, 1430 378, 1600 366 L1600 420 L0 420 Z" fill="#CBD2C6" opacity=".9"/>
    <path d="M0 394 C 190 376, 340 394, 520 389 C 700 382, 880 398, 1060 389
             C 1250 380, 1420 396, 1600 387 L1600 430 L0 430 Z" fill="#B6C2AC" opacity=".95"/>

    <g class="scene__clouds scene__clouds--mid" fill="url(#sc-cloud)" opacity=".56" filter="url(#sc-cloud-mid)">
      <use href="#sc-mid"/><use href="#sc-mid" x="1600"/>
    </g>

    <rect x="0" y="404" width="1600" height="196" fill="url(#sc-meadow)"/>
    <g filter="url(#sc-haze)" opacity=".3">
      <ellipse cx="300" cy="520" rx="320" ry="60" fill="#7C9273"/>
      <ellipse cx="1250" cy="560" rx="380" ry="70" fill="#7C9273"/>
    </g>
    <rect x="0" y="392" width="1600" height="208" fill="url(#sc-grass-a)" mask="url(#sc-grassmask)" opacity=".12"/>
    <rect x="0" y="392" width="1600" height="208" fill="url(#sc-grass-b)" mask="url(#sc-grassmask)" opacity=".1"/>
    <!-- Haze collecting where the land meets the sky. -->
    <rect x="0" y="386" width="1600" height="30" fill="#F0EAE4" opacity=".7" filter="url(#sc-soft)"/>
${isField ? DOORWAY : ''}
    <g class="scene__clouds scene__clouds--near" fill="url(#sc-cloud)" opacity=".74" filter="url(#sc-cloud-near)">
      <use href="#sc-near"/><use href="#sc-near" x="1600"/>
    </g>
  </svg>
  <div class="scene__settle" aria-hidden="true"></div>
</div>`;
}
