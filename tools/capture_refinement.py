"""Repeatable, same-scale artwork captures from the actual local page.

Run --stage before before editing assets, then --stage after. Browser screenshots
are unscaled; the same native crop rectangles and viewports are used both times.
"""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:4321"
VIEWPORTS = {"desktop": (1440, 900), "phone": (390, 844), "landscape": (844, 390)}
# Crop rectangles are in ARTWORK pixels and are deliberately generous, so the
# same rectangle covers a part before and after it is redrawn or moved.
WIDE_CROPS = {"support": (70, 118, 170, 62), "keyboard": (110, 150, 300, 66),
              "mouse": (350, 150, 140, 70), "equipment": (30, 0, 460, 235),
              "desk": (0, 0, 510, 270)}
NARROW_CROPS = {"support": (8, 140, 140, 50), "mouse": (118, 172, 60, 48),
                "desk": (0, 0, 180, 252)}
# The viewpoint pass moved the wide canvas to 576 x 330; crops are chosen by
# the displayed artwork's native width so before/after keep matching parts.
WIDE_CROPS_576 = {"support": (140, 180, 170, 70), "keyboard": (200, 236, 250, 62),
                  "mouse": (410, 240, 100, 60), "equipment": (100, 20, 420, 280),
                  "desk": (0, 0, 576, 330)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("before", "after"), required=True)
    ap.add_argument("--out", default="docs/evidence/refinement")
    args = ap.parse_args()
    out = Path(args.out) / args.stage
    out.mkdir(parents=True, exist_ok=True)
    measurements = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for device, (width, height) in VIEWPORTS.items():
            for theme in ("dark", "light"):
                ctx = browser.new_context(viewport={"width": width, "height": height},
                                          color_scheme=theme, device_scale_factor=1,
                                          has_touch=device != 'desktop', is_mobile=device != 'desktop')
                page = ctx.new_page()
                page.add_init_script("sessionStorage.setItem('atalay.intro','1')")
                page.goto(BASE, wait_until="networkidle")
                page.wait_for_function("document.querySelector('[data-room]').dataset.state === 'room-ready'")
                page.wait_for_timeout(280)
                # Park the visual animation only. No audio was enabled in this context.
                page.evaluate("""() => document.querySelectorAll('.invite__hand, .crt__go-face, .burst__bit')
                    .forEach(el => el.getAnimations().forEach(a => { a.pause(); a.currentTime = 700; }))""")
                page.screenshot(path=str(out / f"{device}-{theme}.png"))
                if device != "landscape":
                    page.locator('[data-screen]').screenshot(path=str(out / f"hand-monitor-{device}-{theme}.png"))
                    page.locator('.invite__hand svg').screenshot(path=str(out / f"hand-native-{device}-{theme}.png"))
                    if device == "desktop":
                        svg = page.locator('.invite__hand svg').evaluate("el => el.outerHTML")
                        alone = ctx.new_page()
                        alone.set_viewport_size({"width": 328, "height": 352})
                        alone.set_content(f'''<html data-theme="{theme}"><head>
                          <link rel="stylesheet" href="{BASE}/styles.css"></head>
                          <body style="margin:32px;background:var(--glass)">
                          <div style="width:264px">{svg}</div></body></html>''', wait_until="networkidle")
                        alone.screenshot(path=str(out / f"hand-alone-{theme}.png"))
                        alone.close()
                    page.evaluate("""() => document.querySelector('.invite__hand').getAnimations()
                        .forEach(a => { a.pause(); a.currentTime = 200; })""")
                    page.locator('[data-screen]').screenshot(path=str(out / f"hand-raised-{device}-{theme}.png"))
                hide = page.add_style_tag(content=".invite, .crt__go, .crt__fx { visibility: hidden !important; }")
                art = page.locator('.crt__art:visible')
                metrics = art.evaluate("""el => { const r = el.getBoundingClientRect(); return {
                    x:r.x, y:r.y, width:r.width, height:r.height,
                    native:[el.naturalWidth,el.naturalHeight], scale:r.width/el.naturalWidth}; }""")
                measurements.append({"device": device, "theme": theme, **metrics})
                page.screenshot(path=str(out / f"equipment-{device}-{theme}.png"))
                wide = WIDE_CROPS_576 if metrics["native"][0] == 576 else WIDE_CROPS
                crops = wide if device == "desktop" else NARROW_CROPS if device == "phone" else {}
                if crops:
                    for name, (x, y, w, h) in crops.items():
                        k = metrics["scale"]
                        suffix = "" if device == "desktop" else f"-{device}"
                        page.screenshot(path=str(out / f"{name}{suffix}-{theme}.png"), clip={
                            "x": metrics["x"] + x * k, "y": metrics["y"] + y * k,
                            "width": w * k, "height": h * k})
                hide.evaluate("el => el.remove()")
                ctx.close()
        if args.stage == "after":
            for theme in ("dark", "light"):
                ctx = browser.new_context(viewport={"width": 1280, "height": 800}, color_scheme=theme)
                pg = ctx.new_page()
                pg.clock.install(time="2026-09-11T12:00:00Z")
                pg.goto(BASE, wait_until="networkidle")
                pg.clock.pause_at("2026-09-11T12:01:00Z")
                pg.locator('[data-sound]').click(force=True)
                pg.wait_for_function("document.querySelector('[data-sound]').getAttribute('aria-pressed') === 'true'")
                pg.clock.run_for(1460)
                for n, advance in ((3, 0), (2, 400), (1, 120), (0, 120)):
                    if advance:
                        pg.clock.run_for(advance)
                    actual = pg.locator('[data-line="1"]').inner_text()
                    assert actual == '.' * n, (n, actual)
                    pg.screenshot(path=str(out / f"deletion-{theme}-{n}.png"))
                ctx.close()
            review = out.parent / 'index.html'
            if review.exists():
                ctx = browser.new_context(viewport={"width": 1900, "height": 1000})
                pg = ctx.new_page()
                pg.goto(review.resolve().as_uri(), wait_until="networkidle")
                for theme in ('dark', 'light'):
                    pg.locator(f'#equipment-{theme}').screenshot(
                        path=str(out.parent / f'comparison-{theme}.png'))
                ctx.close()
        browser.close()
    (out / "dimensions.json").write_text(json.dumps(measurements, indent=2), encoding="utf-8")
    print(json.dumps(measurements, indent=2))


if __name__ == "__main__":
    main()
