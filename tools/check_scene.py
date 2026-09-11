"""Check the opening scene's artwork against the page that shows it.

    .venv/Scripts/python.exe tools/check_scene.py --out <dir>

Three things the other suites do not cover:

  1. the two theme variants have identical geometry, pixel for pixel, so
     switching theme cannot move anything;
  2. the live screen overlay lands exactly on the drawn glass, in both
     framings - measured against the asset's own pixels, not a screenshot;
  3. nothing drawn on the desk - the cables, the tower, the mouse, or the CSS
     band that continues the tabletop past the artwork - takes a click that was
     meant for the screen.

It reports what it measured. Run `node serve.mjs` first.
"""
import argparse
import struct, sys, zlib
from pathlib import Path
from playwright.sync_api import sync_playwright

def load(path):
    d = Path(path).read_bytes(); i, idat, w, h = 8, b"", 0, 0
    while i < len(d):
        ln = struct.unpack(">I", d[i:i+4])[0]; tag = d[i+4:i+8]; data = d[i+8:i+8+ln]
        if tag == b"IHDR": w, h = struct.unpack(">II", data[:8])
        if tag == b"IDAT": idat += data
        i += 12 + ln
    raw = zlib.decompress(idat); rows, st, pos = [], w*4, 0
    for _ in range(h):
        pos += 1; rows.append(raw[pos:pos+st]); pos += st
    return w, h, rows

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="artifacts/scene")
OUT = Path(ap.parse_args().out)
OUT.mkdir(parents=True, exist_ok=True)

fails = []
def check(name, ok, detail):
    print(("  ok   " if ok else "  FAIL ") + name + " -- " + str(detail))
    if not ok: fails.append(name)

print("theme geometry")
for name in ("machine", "machine-compact"):
    w, h, a = load(f"src/assets/pixel/{name}-dark.png")
    w2, h2, b = load(f"src/assets/pixel/{name}-light.png")
    bad = 0 if (w, h) != (w2, h2) else sum(
        1 for y in range(h) for x in range(w)
        if (a[y][x*4+3] == 0) != (b[y][x*4+3] == 0))
    check(f"{name}: both themes the same {w}x{h} shape",
          (w, h) == (w2, h2) and bad == 0, f"{bad} alpha mismatches")

BASE = "http://127.0.0.1:4321"
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for label, vw, vh in (("desktop", 1440, 900), ("phone", 390, 844)):
        ctx = br.new_context(viewport={"width": vw, "height": vh}, device_scale_factor=1)
        pg = ctx.new_page(); pg.goto(BASE + "/", wait_until="networkidle")
        # The opening legitimately covers the screen until the room is revealed,
        # so resolve it first: this check is about the finished room.
        pg.click("[data-skip]")
        pg.wait_for_timeout(400)

        # 2. the overlay against the artwork. Read the artwork's own pixels
        #    rather than a screenshot: same origin, so the canvas is untainted,
        #    and it compares the live rect against the asset with no decoding
        #    of Chromium's adaptive PNG filtering in between.
        probe = pg.evaluate("""() => {
          const img = [...document.querySelectorAll('.crt__art')]
            .find(e => e.getBoundingClientRect().width > 0);
          const btn = document.querySelector('[data-screen]');
          const ir = img.getBoundingClientRect(), sr = btn.getBoundingClientRect();
          const k = img.naturalWidth / ir.width;             // the integer scale
          const c = document.createElement('canvas');
          c.width = img.naturalWidth; c.height = img.naturalHeight;
          c.getContext('2d').drawImage(img, 0, 0);
          const ctx = c.getContext('2d');
          const at = (x, y) => [...ctx.getImageData(Math.round(x), Math.round(y), 1, 1).data].slice(0, 3);
          const x0 = (sr.x - ir.x) * k, y0 = (sr.y - ir.y) * k;
          const w = sr.width * k, h = sr.height * k;
          return {
            file: img.currentSrc.split('/').pop(), scale: k,
            rect: [Math.round(x0), Math.round(y0), Math.round(w), Math.round(h)],
            inside: [at(x0 + 2, y0 + 2), at(x0 + w - 3, y0 + 2),
                     at(x0 + 2, y0 + h - 3), at(x0 + w - 3, y0 + h - 3)],
            outside: [at(x0 - 3, y0 + h / 2), at(x0 + w + 2, y0 + h / 2),
                      at(x0 + w / 2, y0 - 3), at(x0 + w / 2, y0 + h + 2)],
          };
        }""")
        GLASS = {(16, 23, 58), (28, 42, 94), (201, 216, 236), (230, 239, 250)}
        ins = [tuple(c) for c in probe["inside"]]
        out = [tuple(c) for c in probe["outside"]]
        check(f"{label}: overlay lands on the drawn glass at all four corners",
              all(c in GLASS for c in ins),
              f"{probe['file']} {probe['rect']} at {probe['scale']}x -> {ins}")
        check(f"{label}: and the bezel just outside it is not glass",
              not any(c in GLASS for c in out), out)

        # 3. what a click actually resolves to, at the screen and over the parts
        #    this change added: the cables, the tower, the mouse, and the CSS
        #    band that continues the tabletop past the artwork.
        def hit(x, y):
            return pg.evaluate(
                "p => { const e = document.elementFromPoint(p.x, p.y);"
                " if (!e) return 'none';"
                " return e.closest('[data-screen]') ? 'screen'"
                "      : (e.className.baseVal || e.className || e.tagName); }",
                {"x": float(x), "y": float(y)})
        box = pg.eval_on_selector("[data-screen]",
            "el => { const r = el.getBoundingClientRect();"
            " return {x:r.x, y:r.y, w:r.width, h:r.height}; }")
        got = hit(box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)
        check(f"{label}: a click at the screen centre resolves to the screen button",
              got == "screen", got)
        art = pg.eval_on_selector("[data-crt]",
            "el => { const r = el.getBoundingClientRect();"
            " return {x:r.x, y:r.y, w:r.width, h:r.height}; }")
        probes = {
            "the cables, tower and keyboard area":
                (art["x"] + art["w"] * 0.62, art["y"] + art["h"] * 0.72),
            "the mouse": (art["x"] + art["w"] * 0.85, art["y"] + art["h"] * 0.76),
            "the desk band beyond the artwork":
                (art["x"] * 0.4, art["y"] + art["h"] * 0.82),
        }
        for why, (x, y) in probes.items():
            g = hit(x, y)
            check(f"{label}: {why} takes no click meant for the screen", g != "screen", g)
        ctx.close()
    br.close()

print(f"\n{len(fails)} failures")
sys.exit(1 if fails else 0)
