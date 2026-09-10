// ---------------------------------------------------------------------------
// All site content lives here. Edit this file to change what the site says.
//
// Content rules (docs/PROJECT-BRIEF.md and CLAUDE.md):
//   - Nothing here may be invented. Every claim traces to a confirmed source.
//   - Provenance for each project claim is recorded in docs/CONTENT-SOURCES.md.
//   - No employers, dates, metrics, awards, demo links, release status, or a
//     contact email unless Atalay has explicitly confirmed it for publication.
//   - `screenshot: null` renders an honest empty-doorway placeholder. Do not
//     replace it with a stand-in image.
//
// Everything below is plain text. It is escaped before it reaches the page.
// ---------------------------------------------------------------------------

export const site = {
  name: 'Atalay Doganay',
  domain: 'atalaydoganay.com',
  // Not a live URL yet - the domain is a target, not a connected domain.
  // Used only for the copyright line and page titles.
  year: 2026,
};

export const nav = [
  { label: 'Home', href: '/' },
  { label: 'Projects', href: '/projects/' },
  { label: 'About', href: '/about/' },
  { label: 'Contact', href: '/contact/' },
];

// Not currently rendered: the home page is the opening scene. Kept because this is
// the introduction text the desktop will want when its portfolio surface is built.
export const home = {
  title: 'Atalay Doganay',
  lead: 'Computer science student at Cal Poly Pomona. I make browser games and small apps, and I am most interested in software engineering and indie game development.',
  body: [
    'Most of what I build is meant to run without ceremony. No account to make, no server to keep alive, and no build step if I can avoid one.',
  ],
  selectedHeading: 'Selected work',
  selectedNote: 'Two things I have been building.',
};

// ---------------------------------------------------------------------------
// The opening scene. The home page is the computer; the name is introduced on
// its screen and nowhere else on that view.
//
// The two typed lines live in src/scripts/room.js, next to the timing they are
// animated with. Everything here is the text that has to exist without it.
// ---------------------------------------------------------------------------
export const opening = {
  // A stable description for assistive tech. The typed characters are hidden
  // from screen readers, so this is what the screen is, not what it currently says.
  screenDescription:
    'An old computer screen typing a greeting from Atalay Doganay. Activate it to open the desktop.',

  // Describes the rendered machine for anyone who cannot see it.
  machineAlt:
    'A beige desktop computer from the late 1990s: a deep CRT monitor on a stand with a blank screen, and a keyboard on the desk in front of it.',

  desktopHeading: 'Atalay Doganay',
  desktopNote:
    'This is the desktop shell. The projects, the about page and the contact details will live here.',
  desktopItems: [
    'Start opens the menu, and the menu goes back to the room',
    'Close or minimise the window, then bring it back from the taskbar',
    'Escape also returns to the room',
  ],

  // Shown only when JavaScript is unavailable, so the site is still usable.
  fallback: {
    line: 'Hii, my name is Atalay Doganay...',
    note: 'The opening scene needs JavaScript. The rest of the site does not.',
    links: [
      { label: 'Projects', href: '/projects/' },
      { label: 'About', href: '/about/' },
      { label: 'Contact', href: '/contact/' },
    ],
  },
};

export const about = {
  title: 'About',
  lead: 'A short version.',
  body: [
    'I am a computer science student at Cal Poly Pomona. Before that I earned an Associate in Science in Computer Science at Orange Coast College.',
    'What I build falls into two piles. One is software engineering, where the interesting part is being correct about unglamorous things: time zones, per-platform limits, and what happens after the phone reboots. The other is indie game development, which is where I get to care about how something feels to watch.',
    'The two piles have more in common than they look. Both reward knowing exactly what the machine is doing.',
  ],
  educationHeading: 'Education',
  education: [
    { school: 'Cal Poly Pomona', detail: 'Computer Science, currently studying' },
    { school: 'Orange Coast College', detail: 'Associate in Science, Computer Science' },
  ],
};

export const contact = {
  title: 'Contact',
  lead: 'Ways to reach me.',
  body: [
    'Only accounts I have confirmed are listed here, so this is a short list for now.',
  ],
  // Add a channel by adding an entry. Never add one that is not confirmed:
  // an omitted channel is correct, a dead link is not.
  channels: [
    {
      label: 'GitHub',
      value: 'AtalayDoganay',
      href: 'https://github.com/AtalayDoganay',
      icon: 'github',
    },
  ],
};

export const projects = {
  title: 'Projects',
  lead: 'Two things I have been building.',
  items: [
    {
      id: 'ball-fighters',
      name: 'BALL FIGHTERS',
      kind: 'A browser auto-battler.',
      summary:
        'Pick two fighter balls, choose an arena, and the match plays itself out. It is built to be watched rather than played: a tall portrait window, short-form-video shaped.',
      body: [
        'The whole game is classic script files sharing one global, with no build step and no libraries, so it still runs by opening index.html straight off the disk. That constraint drove most of the engineering. No modules and no fetching local files, which means the pixel art is drawn on canvas or embedded as base64, and most of the audio is synthesised with Web Audio while the match runs.',
        'Five arenas present the same fight in different ways, from a plain dungeon pit to a tournament coliseum with a crowd, so the presentation layer is kept strictly separate from the simulation.',
      ],
      facts: [
        { label: 'Built with', value: 'Vanilla JavaScript, HTML canvas, Web Audio' },
        { label: 'Runs', value: 'In a browser, offline, from a local file' },
        { label: 'Shape', value: 'Portrait, 480 x 854' },
      ],
      screenshot: null, // No capture cleared for publication yet.
    },
    {
      id: 'next-class',
      name: 'Next Class',
      kind: 'A class reminder app for students.',
      summary:
        'A student should be able to glance at their phone and immediately know what class is next, when it starts, where it is, and how much time is left.',
      body: [
        'There is no account, no server and no sync. The schedule lives on the device, and the phone operating system delivers the reminders. Each one is registered as a weekly repeating trigger, so it keeps firing when the app is closed, swiped away, or the phone has been restarted.',
        'Most of the work is in the edges. Classes are stored as a weekday and a wall-clock time rather than a timestamp, so nine in the morning stays nine in the morning wherever you are. iOS allows only sixty-four pending notifications for an entire app, so the planner caps the set and drops a whole tier of reminders rather than an arbitrary slice of them.',
      ],
      facts: [
        { label: 'Built with', value: 'React Native and TypeScript on Expo' },
        { label: 'Reminders', value: 'Scheduled by the operating system as weekly repeating triggers' },
        { label: 'Data', value: 'Stored on the device. No account, no server' },
      ],
      screenshot: null, // No capture cleared for publication yet.
    },
  ],
};

export const notFound = {
  title: 'Not here',
  lead: 'That page does not exist.',
  body: ['The door you tried leads nowhere. Everything on this site is one of the four below.'],
};
