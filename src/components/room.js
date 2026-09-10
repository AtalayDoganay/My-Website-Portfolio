// The opening scene: a large beige CRT computer standing in a dark, hazy room.
//
// The computer is drawn as original inline SVG - no stock art, nothing fetched. The
// geometry is deliberately built like an object: a front bezel with a bevel, a right
// side panel in perspective, vents, a button strip, a power light, a tilt stand, a
// keyboard on the desk, and a cable. A rounded rectangle would not read as a machine.
//
// The screen itself is NOT part of the SVG. It is a real <button> positioned exactly
// over the SVG's screen aperture, so the typed text is real DOM text - selectable,
// focusable, measurable - and the zoom can animate from its actual rect.

import { esc } from '../lib/html.js';

// ---------------------------------------------------------------------------
// Geometry. The SVG viewBox and the screen aperture inside it. SCREEN is exported
// as percentages so the CSS can place the interactive element over the aperture
// without either side guessing.
// ---------------------------------------------------------------------------
const VIEW = { w: 1000, h: 900 };
const BEZEL = { x: 90, y: 56, w: 700, h: 566, r: 40 };
const GLASS = { x: 186, y: 96, w: 508, h: 400, r: 22 };

export const SCREEN_BOX = {
  left: (GLASS.x / VIEW.w) * 100,
  top: (GLASS.y / VIEW.h) * 100,
  width: (GLASS.w / VIEW.w) * 100,
  height: (GLASS.h / VIEW.h) * 100,
};

// The viewer stands to the right of the machine and slightly below its top edge, so
// the right side panel is visible and recedes toward this vanishing point.
const VP = { x: 1180, y: 300 };
const DEPTH = 0.17;

/** Push a front-face point back toward the vanishing point. */
const back = (x, y, depth = DEPTH) => [
  +(x + (VP.x - x) * depth).toFixed(1),
  +(y + (VP.y - y) * depth).toFixed(1),
];

const poly = (points, attrs) =>
  `<polygon points="${points.map(([x, y]) => `${x},${y}`).join(' ')}"${attrs}/>`;

// --- Keyboard --------------------------------------------------------------
// Keys are generated rather than hand-placed: five rows on a plane in perspective,
// each row a little wider and a little taller as it comes toward the viewer.
const KB = {
  farL: 246, farR: 706, farY: 722,
  nearL: 196, nearR: 762, nearY: 818,
};

function keyboardKeys() {
  const rows = [15, 14, 13, 12, 9];
  const out = [];
  const lerp = (a, b, t) => a + (b - a) * t;

  for (let r = 0; r < rows.length; r += 1) {
    const t0 = r / rows.length;
    const t1 = (r + 0.78) / rows.length;
    const yTop = lerp(KB.farY, KB.nearY, t0);
    const yBot = lerp(KB.farY, KB.nearY, t1);
    const lTop = lerp(KB.farL, KB.nearL, t0);
    const rTop = lerp(KB.farR, KB.nearR, t0);
    const lBot = lerp(KB.farL, KB.nearL, t1);
    const rBot = lerp(KB.farR, KB.nearR, t1);

    const n = rows[r];
    const gapTop = (rTop - lTop) * 0.012;
    const gapBot = (rBot - lBot) * 0.012;
    const wTop = (rTop - lTop - gapTop * (n - 1)) / n;
    const wBot = (rBot - lBot - gapBot * (n - 1)) / n;

    for (let k = 0; k < n; k += 1) {
      // The last row carries a space bar: five slots fused into one key.
      const isSpace = r === rows.length - 1 && k === 4;
      if (r === rows.length - 1 && k > 4 && k < 8) continue;
      const span = isSpace ? 4 : 1;
      const x0t = lTop + k * (wTop + gapTop);
      const x1t = x0t + wTop * span + gapTop * (span - 1);
      const x0b = lBot + k * (wBot + gapBot);
      const x1b = x0b + wBot * span + gapBot * (span - 1);
      out.push(
        poly(
          [
            [x0t.toFixed(1), yTop.toFixed(1)],
            [x1t.toFixed(1), yTop.toFixed(1)],
            [x1b.toFixed(1), yBot.toFixed(1)],
            [x0b.toFixed(1), yBot.toFixed(1)],
          ],
          ' fill="url(#kb-key)"',
        ),
      );
    }
  }
  return out.join('');
}

// --- Vents on the right side panel -----------------------------------------
function sideVents() {
  const out = [];
  for (let i = 0; i < 8; i += 1) {
    const y = 176 + i * 26;
    const [ax, ay] = back(788, y);
    const [bx, by] = back(788, y + 5);
    out.push(
      poly(
        [
          [778, y],
          [ax, ay],
          [bx, by],
          [778, y + 5],
        ],
        ' fill="#211F1B" opacity=".85"',
      ),
    );
  }
  return out.join('');
}

const SIDE_TOP = BEZEL.y + BEZEL.r * 0.85;
const SIDE_BOT = BEZEL.y + BEZEL.h - BEZEL.r * 0.85;
const [sTopX, sTopY] = back(BEZEL.x + BEZEL.w, SIDE_TOP);
const [sBotX, sBotY] = back(BEZEL.x + BEZEL.w, SIDE_BOT);

/**
 * The machine. `label` is the accessible description of the whole scene; the screen
 * button carries its own name.
 */
export function computer() {
  return `<div class="crt">
  <svg class="crt__body" viewBox="0 0 ${VIEW.w} ${VIEW.h}" fill="none"
       aria-hidden="true" focusable="false">
    <defs>
      <!-- Beige plastic, lit cold from the screen and warm-dark elsewhere. -->
      <linearGradient id="plastic-face" x1="0" y1="0" x2=".35" y2="1">
        <stop offset="0"   stop-color="#D8D4C7"/>
        <stop offset=".42" stop-color="#BFBAAB"/>
        <stop offset="1"   stop-color="#8E8A7E"/>
      </linearGradient>
      <linearGradient id="plastic-side" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0"   stop-color="#7E7A6C"/>
        <stop offset=".55" stop-color="#605D53"/>
        <stop offset="1"   stop-color="#46443C"/>
      </linearGradient>
      <linearGradient id="plastic-stand" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0"   stop-color="#B4AFA1"/>
        <stop offset="1"   stop-color="#6E6B60"/>
      </linearGradient>
      <linearGradient id="plastic-base" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0"   stop-color="#C6C1B3"/>
        <stop offset="1"   stop-color="#7A776C"/>
      </linearGradient>
      <linearGradient id="kb-face" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0"   stop-color="#BDB8AA"/>
        <stop offset="1"   stop-color="#8B8779"/>
      </linearGradient>
      <linearGradient id="kb-key" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0"   stop-color="#D3CFC2"/>
        <stop offset="1"   stop-color="#A5A194"/>
      </linearGradient>
      <!-- The screen is the only light in the room: it spills onto the bezel. -->
      <radialGradient id="screen-spill" cx=".44" cy=".36" r=".58">
        <stop offset="0"   stop-color="#8FEBFA" stop-opacity=".5"/>
        <stop offset=".42" stop-color="#8FEBFA" stop-opacity=".2"/>
        <stop offset="1"   stop-color="#8FEBFA" stop-opacity="0"/>
      </radialGradient>
      <!-- A thin catch of pink along the far edge, where the room's other light
           grazes the casing. Any wider and it stops reading as plastic. -->
      <linearGradient id="rim-pink" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0"    stop-color="#FF9BD6" stop-opacity="0"/>
        <stop offset=".72"  stop-color="#FF9BD6" stop-opacity="0"/>
        <stop offset=".93"  stop-color="#F0A6CE" stop-opacity=".13"/>
        <stop offset="1"    stop-color="#FFC2E8" stop-opacity=".22"/>
      </linearGradient>
      <linearGradient id="aperture" x1="0" y1="0" x2=".2" y2="1">
        <stop offset="0"   stop-color="#0A0D18"/>
        <stop offset="1"   stop-color="#04060E"/>
      </linearGradient>
      <filter id="contact" x="-40%" y="-120%" width="180%" height="360%">
        <feGaussianBlur stdDeviation="16"/>
      </filter>
      <filter id="soft-glow" x="-60%" y="-60%" width="220%" height="220%">
        <feGaussianBlur stdDeviation="14"/>
      </filter>
      <filter id="led-glow" x="-300%" y="-300%" width="700%" height="700%">
        <feGaussianBlur stdDeviation="6"/>
      </filter>
    </defs>

    <!-- Shadow pooled under the machine, on the desk -->
    <ellipse cx="470" cy="742" rx="330" ry="34" fill="#05060F" opacity=".72" filter="url(#contact)"/>
    <ellipse cx="470" cy="826" rx="300" ry="26" fill="#05060F" opacity=".5" filter="url(#contact)"/>

    <!-- ---------------- Keyboard ---------------- -->
    ${poly(
      [
        [KB.farL - 12, KB.farY - 14],
        [KB.farR + 12, KB.farY - 14],
        [KB.nearR + 14, KB.nearY + 18],
        [KB.nearL - 14, KB.nearY + 18],
      ],
      ' fill="url(#kb-face)"',
    )}
    ${poly(
      [
        [KB.farL - 12, KB.farY - 14],
        [KB.farR + 12, KB.farY - 14],
        [KB.farR + 12, KB.farY - 8],
        [KB.farL - 12, KB.farY - 8],
      ],
      ' fill="#E2DED1" opacity=".55"',
    )}
    ${keyboardKeys()}
    ${poly(
      [
        [KB.nearL - 14, KB.nearY + 12],
        [KB.nearR + 14, KB.nearY + 12],
        [KB.nearR + 14, KB.nearY + 18],
        [KB.nearL - 14, KB.nearY + 18],
      ],
      ' fill="#5F5C53"',
    )}
    <!-- Keyboard cable, running back to the machine -->
    <path d="M470 708 C 470 690, 520 682, 545 676" stroke="#4A4840" stroke-width="7"
          stroke-linecap="round" opacity=".85"/>

    <!-- ---------------- Stand ---------------- -->
    ${poly(
      [
        [352, 618],
        [528, 618],
        [546, 690],
        [334, 690],
      ],
      ' fill="url(#plastic-stand)"',
    )}
    ${poly(
      [
        [528, 618],
        [566, 640],
        [578, 700],
        [546, 690],
      ],
      ' fill="url(#plastic-side)"',
    )}
    <path d="M306 688 h268 a18 18 0 0 1 17 12 l10 30 a10 10 0 0 1 -10 13 h-312
             a10 10 0 0 1 -10 -13 l10 -30 a18 18 0 0 1 17 -12 z" fill="url(#plastic-base)"/>
    <path d="M306 688 h268 a18 18 0 0 1 17 12 h-302 a18 18 0 0 1 17 -12 z"
          fill="#E4E0D3" opacity=".5"/>

    <!-- ---------------- Right side panel (recedes toward the vanishing point) -->
    ${poly(
      [
        [BEZEL.x + BEZEL.w - 30, SIDE_TOP],
        [sTopX, sTopY],
        [sBotX, sBotY],
        [BEZEL.x + BEZEL.w - 30, SIDE_BOT],
      ],
      ' fill="url(#plastic-side)"',
    )}
    ${sideVents()}
    ${poly(
      [
        [BEZEL.x + BEZEL.w - 30, SIDE_TOP],
        [sTopX, sTopY],
        [sBotX, sBotY],
        [BEZEL.x + BEZEL.w - 30, SIDE_BOT],
      ],
      ' fill="url(#rim-pink)"',
    )}
    <!-- the moulded edge where the side meets the front -->
    <path d="M${sTopX} ${sTopY} L${sBotX} ${sBotY}" stroke="#4A483F" stroke-width="3" opacity=".8"/>

    <!-- ---------------- Front bezel ---------------- -->
    <rect x="${BEZEL.x}" y="${BEZEL.y}" width="${BEZEL.w}" height="${BEZEL.h}"
          rx="${BEZEL.r}" fill="url(#plastic-face)"/>
    <!-- top and left bevel highlight, bottom-right bevel shadow -->
    <path d="M${BEZEL.x + 10} ${BEZEL.y + BEZEL.r} a30 30 0 0 1 30 -30 h${BEZEL.w - 80}
             a30 30 0 0 1 30 30" stroke="#EFEBDE" stroke-width="4" opacity=".55" fill="none"/>
    <path d="M${BEZEL.x + 6} ${BEZEL.y + BEZEL.h - BEZEL.r} a34 34 0 0 0 34 34 h${BEZEL.w - 80}
             a34 34 0 0 0 34 -34" stroke="#5C5950" stroke-width="5" opacity=".5" fill="none"/>
    <!-- moulding seam around the glass -->
    <rect x="${GLASS.x - 16}" y="${GLASS.y - 16}" width="${GLASS.w + 32}" height="${GLASS.h + 32}"
          rx="${GLASS.r + 12}" fill="none" stroke="#6E6B61" stroke-width="2" opacity=".6"/>
    <rect x="${GLASS.x - 8}" y="${GLASS.y - 8}" width="${GLASS.w + 16}" height="${GLASS.h + 16}"
          rx="${GLASS.r + 6}" fill="#3A382F" opacity=".85"/>

    <!-- the recessed aperture the real screen element sits in -->
    <rect x="${GLASS.x}" y="${GLASS.y}" width="${GLASS.w}" height="${GLASS.h}"
          rx="${GLASS.r}" fill="url(#aperture)"/>

    <!-- ---------------- Chin: buttons, light, moulded strip ---------------- -->
    <rect x="${GLASS.x}" y="530" width="150" height="10" rx="5" fill="#8D8A7E" opacity=".5"/>
    <g>
      <rect x="470" y="556" width="52" height="20" rx="10" fill="#A9A598"/>
      <rect x="470" y="556" width="52" height="9"  rx="4.5" fill="#CBC7BA" opacity=".7"/>
      <rect x="534" y="556" width="34" height="20" rx="10" fill="#A9A598"/>
      <rect x="580" y="556" width="34" height="20" rx="10" fill="#A9A598"/>
      <rect x="626" y="556" width="34" height="20" rx="10" fill="#A9A598"/>
    </g>
    <!-- power switch, larger and set apart -->
    <circle cx="242" cy="566" r="19" fill="#B3AFA2"/>
    <circle cx="242" cy="566" r="19" fill="none" stroke="#6E6B61" stroke-width="2" opacity=".7"/>
    <circle cx="242" cy="563" r="15" fill="#C7C3B6"/>
    <path d="M242 556 v10" stroke="#6B6860" stroke-width="3" stroke-linecap="round"/>
    <circle cx="242" cy="563" r="9" fill="none" stroke="#6B6860" stroke-width="2.5"
            stroke-dasharray="38 14" transform="rotate(-90 242 563)"/>
    <!-- power light -->
    <circle class="crt__led" cx="300" cy="566" r="7" fill="#5CF2C8"/>
    <circle class="crt__led-glow" cx="300" cy="566" r="12" fill="#5CF2C8" filter="url(#led-glow)" opacity=".8"/>
    <!-- two moulded screws in the chin -->
    <circle cx="130" cy="600" r="4" fill="#7C7970" opacity=".6"/>
    <circle cx="750" cy="600" r="4" fill="#7C7970" opacity=".6"/>

    <!-- the screen's light falling across the bezel: drawn last, over the plastic -->
    <rect x="${BEZEL.x}" y="${BEZEL.y}" width="${BEZEL.w}" height="${BEZEL.h}" rx="${BEZEL.r}"
          fill="url(#screen-spill)" class="crt__spill"/>
  </svg>

  <button class="crt__screen" type="button" data-screen
          aria-label="Enter the computer" aria-describedby="crt-description">
    <span class="crt__glass">
      <span class="crt__wall" aria-hidden="true"></span>
      <span class="crt__readout" aria-hidden="true"><span class="crt__line" data-line></span
        ><span class="crt__caret" data-caret></span></span>
      <span class="crt__hint" data-hint aria-hidden="true"></span>
      <span class="crt__scan" aria-hidden="true"></span>
      <span class="crt__curve" aria-hidden="true"></span>
      <span class="crt__gloss" aria-hidden="true"></span>
    </span>
  </button>
</div>`;
}

/** The room: environment, machine, and the no-JavaScript fallback. */
export function room({ description, fallback }) {
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
      ${computer()}
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
