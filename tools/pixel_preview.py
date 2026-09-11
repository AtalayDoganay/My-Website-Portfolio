"""Upscale a pixel asset with nearest neighbour, for inspecting it at working size.

    python tools/pixel_preview.py <src.png> <dst.png> <scale> [#rrggbb]
"""
import binascii, struct, sys, zlib


def load(path):
    d = open(path, "rb").read()
    i, idat, w, h = 8, b"", 0, 0
    while i < len(d):
        ln = struct.unpack(">I", d[i:i + 4])[0]
        tag, data = d[i + 4:i + 8], d[i + 8:i + 8 + ln]
        if tag == b"IHDR":
            w, h = struct.unpack(">II", data[:8])
        if tag == b"IDAT":
            idat += data
        i += 12 + ln
    raw = zlib.decompress(idat)
    rows, st, pos = [], w * 4, 0
    for _ in range(h):
        pos += 1
        rows.append(raw[pos:pos + st])
        pos += st
    return w, h, rows


def save(path, w, h, rows):
    raw = bytearray()
    for r in rows:
        raw.append(0)
        raw += r

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    open(path, "wb").write(png)


src, dst, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
bg = sys.argv[4].lstrip("#") if len(sys.argv) > 4 else "070a18"
back = bytes(int(bg[i:i + 2], 16) for i in (0, 2, 4)) + b"\xff"
w, h, rows = load(src)
out = []
for y in range(h):
    row = bytearray()
    for x in range(w):
        px = rows[y][x * 4:x * 4 + 4]
        row += (back if px[3] == 0 else px) * n
    out.extend([bytes(row)] * n)
save(dst, w * n, h * n, out)
print(f"{src} -> {dst} at {n}x ({w * n}x{h * n})")
