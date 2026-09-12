"""Browser checks for the built site.

Written for the project-local `webapp-testing` skill (.claude/skills/webapp-testing).
Run it through that skill's server helper so the preview server is started and
stopped for you:

    .venv/Scripts/python.exe .claude/skills/webapp-testing/scripts/with_server.py \
        --server "npm run preview" --port 4321 -- \
        .venv/Scripts/python.exe tools/check_pages.py --out <screenshot dir>

It reports what it actually observed and asserts nothing it did not measure.
"""

import argparse
import base64
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:4321"
PAGES = [
    ("home", "/"),
    ("projects", "/projects/"),
    ("about", "/about/"),
    ("contact", "/contact/"),
    ("404", "/nope/"),
]
WIDTHS = [("desktop", 1280, 900), ("mobile", 390, 844)]


# Relative luminance and contrast ratio, per WCAG 2.1.
def _lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(rgb):
    r, g, b = rgb
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(fg, bg):
    l1, l2 = _luminance(fg), _luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def parse_rgb(value):
    """rgb()/rgba() with 0-255 channels, or the color(srgb r g b) form that
    Chromium reports for colours produced by color-mix(); those channels are 0-1."""
    value = value.strip()
    if value.startswith("color("):
        body = value[value.index("(") + 1:value.rindex(")")].replace("/", " ").split()
        nums = [float(n) * 255 for n in body[1:4]]      # body[0] is the colour space
    else:
        cleaned = value.replace("rgba", "").replace("rgb", "").strip("() ").replace("/", ",")
        nums = [float(n) for n in cleaned.replace(" ", ",").split(",") if n.strip()]
    if len(nums) < 3:
        return None
    return tuple(int(round(n)) for n in nums[:3])


CONTRAST_JS = r"""
() => {
  const out = [];
  const bgOf = (el) => {
    let node = el;
    while (node) {
      const bg = getComputedStyle(node).backgroundColor;
      const m = bg.match(/[\d.]+/g);
      if (m && (m.length < 4 || parseFloat(m[3]) > 0.6)) return bg;
      node = node.parentElement;
    }
    return 'rgb(255, 255, 255)';
  };
  const sel = 'p, li, a, h1, h2, h3, dt, dd, figcaption, span';
  for (const el of document.querySelectorAll(sel)) {
    const text = (el.textContent || '').trim();
    if (!text || el.querySelector(sel)) continue;
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    out.push({
      text: text.slice(0, 40),
      color: cs.color,
      bg: bgOf(el),
      size: parseFloat(cs.fontSize),
      weight: cs.fontWeight,
      tag: el.tagName,
    });
  }
  return out;
}
"""

FOCUS_JS = r"""
() => {
  const a = document.activeElement;
  if (!a || a === document.body) return null;
  const cs = getComputedStyle(a);
  const r = a.getBoundingClientRect();
  return {
    tag: a.tagName,
    text: (a.textContent || '').trim().slice(0, 32),
    href: a.getAttribute('href'),
    outline: cs.outlineWidth + ' ' + cs.outlineStyle + ' ' + cs.outlineColor,
    onScreen: r.width > 0 && r.height > 0 && r.bottom > 0,
    y: Math.round(r.y),
  };
}
"""

MOTION_JS = r"""
() => [...document.querySelectorAll('.scene__clouds, .scene__bloom')].map((el) => ({
  cls: el.getAttribute('class'),
  name: getComputedStyle(el).animationName,
  duration: getComputedStyle(el).animationDuration,
}))
"""

TOUCH_JS = r"""
() => [...document.querySelectorAll('a, button')].map((el) => {
  const r = el.getBoundingClientRect();
  return { text: (el.textContent || '').trim().slice(0, 24), w: Math.round(r.width), h: Math.round(r.height) };
}).filter((t) => t.h > 0 && t.h < 40)
"""

# The masthead sits on the scene, so its real background is painted artwork, not the
# band's flat CSS colour. Reading the computed background there would check the wrong
# thing, so the artwork is screenshotted with the text hidden and its actual pixels
# sampled: dark text is judged against the darkest pixel it could land on.
SAMPLE_JS = r"""
(dataUrl) => new Promise((resolve) => {
  const img = new Image();
  img.onload = () => {
    const c = document.createElement('canvas');
    c.width = img.width; c.height = img.height;
    const ctx = c.getContext('2d');
    ctx.drawImage(img, 0, 0);
    const px = ctx.getImageData(0, 0, c.width, c.height).data;
    let darkest = null, dl = Infinity, lightest = null, ll = -Infinity;
    const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    for (let i = 0; i < px.length; i += 4) {
      const L = 0.2126 * lin(px[i]) + 0.7152 * lin(px[i + 1]) + 0.0722 * lin(px[i + 2]);
      if (L < dl) { dl = L; darkest = [px[i], px[i + 1], px[i + 2]]; }
      if (L > ll) { ll = L; lightest = [px[i], px[i + 1], px[i + 2]]; }
    }
    resolve({ darkest, lightest });
  };
  img.src = dataUrl;
})
"""


def sample_band_behind_text(browser, page, out):
    """Return the darkest and lightest pixel the scene paints behind the masthead.

    The home page is an immersive scene with no masthead; there is nothing to sample.
    """
    if not page.query_selector(".masthead"):
        return None
    box = page.evaluate(
        "() => { const m = document.querySelector('.masthead');"
        " const r = m.getBoundingClientRect();"
        " return { x: r.x, y: r.y, width: r.width, height: r.height }; }"
    )
    page.evaluate("() => { document.querySelector('.masthead').style.visibility = 'hidden'; }")
    png = page.screenshot(clip=box)
    page.evaluate("() => { document.querySelector('.masthead').style.visibility = ''; }")
    (out / "band-behind-masthead.png").write_bytes(png)

    data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    blank = browser.new_page()
    blank.goto("about:blank")
    result = blank.evaluate(SAMPLE_JS, data_url)
    blank.close()
    return result


AXE = Path("tools/vendor/axe.min.js")

AXE_JS = r"""
() => axe.run(document, {
  resultTypes: ['violations'],
  runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice'] },
}).then((r) => r.violations.map((v) => ({
  id: v.id,
  impact: v.impact,
  help: v.help,
  nodes: v.nodes.slice(0, 3).map((n) => n.target.join(' ')),
})))
"""


def run_axe(page, path, label, findings):
    """Real axe-core scan. Reports Unavailable rather than silently passing."""
    if not AXE.exists():
        return False
    page.add_script_tag(path=str(AXE))
    for v in page.evaluate(AXE_JS):
        findings.append(
            "[{}] {} {} ({}): {} -- {}".format(
                label, path, v["id"], v["impact"], v["help"], "; ".join(v["nodes"])
            )
        )
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="directory for screenshots")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    f = {
        "console": [],
        "requests_failed": [],
        "overflow": [],
        "contrast": [],
        "small_targets": [],
        "focus_order": [],
        "fonts": [],
        "text_on_artwork": [],
        "axe": [],
        "axe_status": "not run",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for label, width, height in WIDTHS:
            ctx = browser.new_context(
                viewport={"width": width, "height": height}, device_scale_factor=2
            )
            page = ctx.new_page()
            # /nope/ is requested on purpose to exercise the 404 page, and the 404
            # status it returns is logged by the browser as a console error. That one
            # is expected, so it is attributed and skipped rather than counted.
            here = {"path": ""}

            def on_console(msg, lab=label):
                if msg.type in ("error", "warning") and here["path"] != "/nope/":
                    f["console"].append("[{}] {}: {}".format(lab, msg.type, msg.text))

            def on_failed(req, lab=label):
                f["requests_failed"].append("[{}] {} :: {}".format(lab, req.url, req.failure))

            def on_response(res, lab=label):
                if res.status >= 400 and "/nope/" not in res.url:
                    f["requests_failed"].append(
                        "[{}] HTTP {} {}".format(lab, res.status, res.url)
                    )

            page.on("console", on_console)
            page.on("requestfailed", on_failed)
            page.on("response", on_response)

            for name, path in PAGES:
                here["path"] = path
                page.goto(BASE + path, wait_until="networkidle")
                page.wait_for_timeout(400)
                page.screenshot(path=str(out / "{}-{}.png".format(name, label)), full_page=True)

                box = page.evaluate(
                    "() => ({ sw: document.documentElement.scrollWidth,"
                    " cw: document.documentElement.clientWidth })"
                )
                if box["sw"] > box["cw"] + 1:
                    f["overflow"].append(
                        "[{}] {}: scrollWidth {} > clientWidth {}".format(
                            label, path, box["sw"], box["cw"]
                        )
                    )

                for item in page.evaluate(CONTRAST_JS):
                    fg, bg = parse_rgb(item["color"]), parse_rgb(item["bg"])
                    if not fg or not bg:
                        continue
                    ratio = contrast(fg, bg)
                    large = item["size"] >= 24 or (
                        item["size"] >= 18.66 and int(item["weight"]) >= 700
                    )
                    need = 3.0 if large else 4.5
                    if ratio < need:
                        f["contrast"].append(
                            "[{}] {} <{}> {:.2f}:1 needs {} - {} on {} - {!r}".format(
                                label, path, item["tag"], ratio, need,
                                item["color"], item["bg"], item["text"],
                            )
                        )

                if run_axe(page, path, label, f["axe"]):
                    f["axe_status"] = "ran (axe-core 4.10.2, wcag2a/aa + wcag21a/aa + best-practice)"
                else:
                    f["axe_status"] = (
                        "UNAVAILABLE - tools/vendor/axe.min.js is missing. Fetch it with: "
                        "curl -o tools/vendor/axe.min.js "
                        "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"
                    )

                if label == "mobile":
                    for t in page.evaluate(TOUCH_JS):
                        f["small_targets"].append("[{}] {}: {}x{}".format(path, t["text"], t["w"], t["h"]))

                if label == "desktop" and name == "home":
                    f["fonts"] = page.evaluate(
                        "() => [...document.fonts].map((x) => x.family + ' ' + x.weight + ' ' + x.status)"
                    )

                # Text sitting on the scene, checked against the artwork's real pixels.
                sky = sample_band_behind_text(browser, page, out)
                if sky is None:
                    continue
                worst = tuple(sky["darkest"])
                for item in page.evaluate(
                    "() => [...document.querySelectorAll('.masthead a')].map((el) => ({"
                    " text: (el.textContent || '').trim().slice(0, 24),"
                    " color: getComputedStyle(el).color,"
                    " size: parseFloat(getComputedStyle(el).fontSize),"
                    " weight: getComputedStyle(el).fontWeight,"
                    " onPill: getComputedStyle(el).backgroundColor !== 'rgba(0, 0, 0, 0)' }))"
                ):
                    if item["onPill"]:
                        continue  # sits on its own opaque fill, already covered above
                    fg = parse_rgb(item["color"])
                    ratio = contrast(fg, worst)
                    large = item["size"] >= 24
                    need = 3.0 if large else 4.5
                    verdict = "ok" if ratio >= need else "FAIL"
                    f["text_on_artwork"].append(
                        "[{}] {} {!r} {} {:.2f}:1 vs darkest artwork pixel rgb{} (needs {})".format(
                            label, path, item["text"], verdict, ratio, worst, need
                        )
                    )
                    if ratio < need:
                        f["contrast"].append(
                            "[{}] {} masthead {!r} {:.2f}:1 on painted sky rgb{} (needs {})".format(
                                label, path, item["text"], ratio, worst, need
                            )
                        )

            ctx.close()

        # Keyboard walk of the home page.
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        page.goto(BASE + "/", wait_until="networkidle")
        for i in range(9):
            page.keyboard.press("Tab")
            page.wait_for_timeout(220)  # let the skip link finish sliding into view
            info = page.evaluate(FOCUS_JS)
            if info is None:
                break
            f["focus_order"].append(info)
            if i == 0:
                page.screenshot(path=str(out / "focus-skiplink.png"))
            if i == 2:
                page.screenshot(path=str(out / "focus-nav.png"))
        ctx.close()

        # Reduced motion.
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900}, reduced_motion="reduce"
        )
        page = ctx.new_page()
        page.goto(BASE + "/", wait_until="networkidle")
        page.wait_for_timeout(300)
        page.screenshot(path=str(out / "home-reduced-motion.png"), full_page=True)
        f["reduced_motion"] = page.evaluate(MOTION_JS)
        ctx.close()

        browser.close()

    print(json.dumps(f, indent=1))
    problems = (
        len(f["console"])
        + len(f["requests_failed"])
        + len(f["overflow"])
        + len(f["contrast"])
        + len(f["axe"])
    )
    print(
        "\naxe: {}".format(f["axe_status"])
        + "\nproblems: {}  (console {}, failed requests {}, overflow {}, contrast {}, axe {})".format(
            problems,
            len(f["console"]),
            len(f["requests_failed"]),
            len(f["overflow"]),
            len(f["contrast"]),
            len(f["axe"]),
        )
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
