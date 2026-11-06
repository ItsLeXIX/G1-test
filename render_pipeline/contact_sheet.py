"""blender -b --factory-startup -P contact_sheet.py -- <out_dir> <n1,n2,...> [<sheet.png>]

Grid of the rendered images, each labelled "#n" and its GPU render time (from
timings.json); skipped/failed images get a grey tile labelled "#n --".
Labels use a built-in 5x7 bitmap font so no imaging library is needed.
"""
import json
import os
import sys

import bpy
import numpy as np

FONT = {  # 5x7, rows top to bottom
    "0": "01110 10001 10011 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    "#": "01010 01010 11111 01010 11111 01010 01010", "s": "00000 00000 01111 10000 01110 00001 11110",
    "-": "00000 00000 00000 11111 00000 00000 00000", " ": "00000 00000 00000 00000 00000 00000 00000",
    ".": "00000 00000 00000 00000 00000 01100 01100",
}


def text(canvas, s, x, y, scale=4, colour=(1, 1, 1, 1)):
    """Draw s with its top-left at (x, y) (y from the top of the canvas)."""
    H = canvas.shape[0]
    for ch in s:
        rows = FONT.get(ch, FONT[" "]).split()
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit == "1":
                    y0 = H - (y + (r + 1) * scale)
                    canvas[y0:y0 + scale, x + c * scale:x + (c + 1) * scale] = colour
        x += 6 * scale


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    out_dir, names = a[:2]
    sheet = a[2] if len(a) > 2 else os.path.join(out_dir, "contact_sheet.png")
    names = names.split(",")
    timings = json.load(open(os.path.join(out_dir, "timings.json")))
    tw, th, pad, lab = 600, 250, 12, 40
    cols = 4
    rows = (len(names) + cols - 1) // cols
    W, H = cols * (tw + pad) + pad, rows * (th + lab + pad) + pad
    canvas = np.zeros((H, W, 4), np.float32)
    canvas[:] = (0.12, 0.12, 0.13, 1)
    for i, n in enumerate(names):
        r, c = divmod(i, cols)
        x0 = pad + c * (tw + pad)
        ytop = pad + r * (th + lab + pad)
        t = timings.get(n, {})
        p = os.path.join(out_dir, f"{n}.png")
        if os.path.exists(p) and "render_s" in t:
            im = bpy.data.images.load(p)
            im.scale(tw, th)
            px = np.empty(tw * th * 4, np.float32)
            im.pixels.foreach_get(px)
            y0 = H - (ytop + lab + th)
            canvas[y0:y0 + th, x0:x0 + tw] = px.reshape(th, tw, 4)
            label = f"#{n}  {(t.get('gpu_render_s') or t['render_s']):.0f}s"
        else:
            y0 = H - (ytop + lab + th)
            canvas[y0:y0 + th, x0:x0 + tw] = (0.3, 0.3, 0.32, 1)
            label = f"#{n}  --"
        text(canvas, label, x0, ytop + 6)
    o = bpy.data.images.new("sheet", W, H, alpha=True)
    o.pixels.foreach_set(canvas.ravel())
    o.filepath_raw = sheet
    o.file_format = "PNG"
    o.save()


main()
