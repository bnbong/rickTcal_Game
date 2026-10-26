#!/usr/bin/env python3
"""Asset pipeline: retouched 2x sheets -> web/public/assets (sprites, background, manifest).

Usage (from anywhere):  python3 web/tools/build-assets.py

Requires Pillow only (no numpy). Re-running overwrites the outputs deterministically.

How poses are extracted
-----------------------
The sheets are NOT uniform atlases. Every sheet is split into "cells" (polygons in
source-pixel coordinates). The alpha mask (alpha > ALPHA_CUT) is labelled into
connected components on a coarse block grid (BLOCK px). A component that lies
mostly (>= WHOLE_FRAC) inside one cell is assigned to that cell as a whole, so
parts that stick out of a rough grid (wings, hair, "!" marks) are kept with
their own pose. Only components that really straddle two cells are split at the
pixel level along the cell polygons (needed for the erpin right column, where the
dance pose's feet touch the caught pose's crown).
"""

from __future__ import annotations

import json
import os
import statistics
import sys
from collections import deque

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
SRC_DIR = os.path.join(ROOT, "assets", "concepts", "2026-10-23", "v4", "retouched", "upscaled-2x")
OUT_DIR = os.path.join(ROOT, "web", "public", "assets")
SPRITE_DIR = os.path.join(OUT_DIR, "sprites")
BG_DIR = os.path.join(OUT_DIR, "bg")

ALPHA_CUT = 8  # alpha <= this is treated as noise and cleared
BLOCK = 4  # component labelling granularity (source px)
WHOLE_FRAC = 0.85  # a component this much inside one cell is assigned whole

# Group scale targets (output px). See SPEC section 5.
TARGET_ERPIN_MAX_H = 540
TARGET_JOANNE_MAX_H = 540
TARGET_SHERUM_MAX_H = 720
TARGET_DESK_LONG_W = 1400
TARGET_GAUGE_W = 900

# Background: 2896x2172 -> 16:9 crop (full width x 1629) starting at BG_CROP_TOP,
# i.e. the crop centre sits below the image centre so most of the grass is kept
# (horizon lands ~60% down the frame).
BG_CROP_TOP = 430
BG_OUT = (1920, 1080)


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# Cells per sheet: list of (key, polygon). Later cells win on shared boundaries.
SHEETS = {
    "erpin-poses.png": [  # 3072x2048
        ("erpin_idle", rect(0, 0, 1536, 1032)),
        ("erpin_eat", rect(0, 1032, 1536, 2048)),
        # Right column: dance feet end at y=1038 (x<1900) while the caught pose's
        # crown tip starts at y=1037 (x~2225), so the boundary has a notch.
        ("erpin_dance", [(1536, 0), (3072, 0), (3072, 1037), (2195, 1037), (2195, 1039), (1536, 1039)]),
        ("erpin_caught", [(1536, 1039), (2195, 1039), (2195, 1037), (3072, 1037), (3072, 2048), (1536, 2048)]),
    ],
    "joanne-poses.png": [  # 2492x2526
        ("joanne_idle", rect(0, 0, 1260, 1260)),
        ("joanne_shocked", rect(1260, 0, 2492, 1260)),
        ("joanne_dance", rect(0, 1260, 1392, 2526)),
        ("joanne_bread", rect(1392, 1260, 2492, 2526)),
    ],
    "sherum-poses.png": [  # 3966x1586
        ("sherum_safe", rect(0, 0, 1360, 1586)),
        ("sherum_turning", rect(1360, 0, 2684, 1586)),
        ("sherum_watching", rect(2684, 0, 3966, 1586)),
    ],
    "props-sheet.png": [  # 3072x2048
        ("desk_long", rect(0, 0, 3072, 1150)),
        ("desk_small", rect(0, 1150, 1264, 2048)),
        ("bread_plate", rect(1264, 1150, 1896, 2048)),
        ("papers", rect(1896, 1150, 2612, 2048)),
        ("ink", rect(2612, 1150, 3072, 2048)),
    ],
    "ui-sheet.png": [  # 3072x2048
        ("ui_gauge_frame", rect(0, 0, 3072, 740)),
        ("ui_bread_icon", rect(0, 740, 864, 2048)),
        ("ui_dance_icon", rect(864, 740, 2090, 2048)),
        ("ui_pause_icon", rect(2090, 740, 3072, 1530)),
        ("ui_label", rect(2090, 1530, 3072, 2048)),
    ],
}

KEY_ORDER = [
    "erpin_idle", "erpin_dance", "erpin_eat", "erpin_caught",
    "joanne_idle", "joanne_shocked", "joanne_dance", "joanne_bread",
    "sherum_safe", "sherum_turning", "sherum_watching",
    "desk_long", "desk_small", "bread_plate", "papers", "ink",
    "ui_gauge_frame", "ui_bread_icon", "ui_dance_icon", "ui_pause_icon", "ui_label",
]

# Scale groups: (keys, metric, target). metric "h" = max height, ("w", key) = width of key.
GROUPS = [
    (["erpin_idle", "erpin_dance", "erpin_eat", "erpin_caught"], "h", TARGET_ERPIN_MAX_H),
    (["joanne_idle", "joanne_shocked", "joanne_dance", "joanne_bread"], "h", TARGET_JOANNE_MAX_H),
    (["sherum_safe", "sherum_turning", "sherum_watching"], "h", TARGET_SHERUM_MAX_H),
    (["desk_long", "desk_small", "bread_plate", "papers", "ink"], ("w", "desk_long"), TARGET_DESK_LONG_W),
    (["ui_gauge_frame", "ui_bread_icon", "ui_dance_icon", "ui_pause_icon", "ui_label"],
     ("w", "ui_gauge_frame"), TARGET_GAUGE_W),
]


def log(msg):
    print(msg, flush=True)


def binary_alpha(img):
    return img.getchannel("A").point(lambda v: 255 if v > ALPHA_CUT else 0)


def clean_alpha(img):
    """Zero alpha <= ALPHA_CUT (and RGB under fully transparent pixels)."""
    mask = binary_alpha(img)
    r, g, b, a = img.split()
    a = ImageChops.darker(a, mask)
    out = Image.merge("RGBA", (r, g, b, a))
    clear = Image.new("RGBA", img.size, (0, 0, 0, 0))
    return Image.composite(out, clear, mask)


def label_blocks(mask):
    """Connected components (4-neighbour) on a BLOCK-downsampled binary mask.

    Returns (labels list, bw, bh, ncomp). A block is set if any source pixel is set.
    """
    w, h = mask.size
    bw, bh = -(-w // BLOCK), -(-h // BLOCK)
    padded = Image.new("L", (bw * BLOCK, bh * BLOCK), 0)
    padded.paste(mask, (0, 0))
    small = padded.resize((bw, bh), Image.BOX)
    occ = small.tobytes()
    labels = [0] * (bw * bh)
    n = 0
    for start in range(bw * bh):
        if not occ[start] or labels[start]:
            continue
        n += 1
        labels[start] = n
        q = deque([start])
        while q:
            i = q.popleft()
            x, y = i % bw, i // bw
            for j, ok in ((i - 1, x > 0), (i + 1, x < bw - 1), (i - bw, y > 0), (i + bw, y < bh - 1)):
                if ok and occ[j] and not labels[j]:
                    labels[j] = n
                    q.append(j)
    return labels, bw, bh, n


def extract_sheet(img, cells):
    """Return {key: (RGBA crop trimmed to alpha bbox, (offset_x, offset_y))}."""
    w, h = img.size
    img = clean_alpha(img)
    mask = binary_alpha(img)
    labels, bw, bh, ncomp = label_blocks(mask)

    # Cell index map at source and block resolution (later cells overwrite earlier).
    cell_map = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(cell_map)
    for idx, (_, poly) in enumerate(cells, start=1):
        d.polygon(poly, fill=idx)
    cell_px = cell_map.load()

    # Per component: block counts per cell (using block centres).
    counts = [dict() for _ in range(ncomp + 1)]
    for i, lab in enumerate(labels):
        if lab:
            x = min(w - 1, (i % bw) * BLOCK + BLOCK // 2)
            y = min(h - 1, (i // bw) * BLOCK + BLOCK // 2)
            c = cell_px[x, y]
            counts[lab][c] = counts[lab].get(c, 0) + 1

    whole = {}  # comp -> cell idx
    split = []
    for lab in range(1, ncomp + 1):
        tot = sum(counts[lab].values())
        best, cnt = max(counts[lab].items(), key=lambda kv: kv[1])
        if best and cnt / tot >= WHOLE_FRAC:
            whole[lab] = best
        else:
            split.append(lab)
    if split:
        log(f"    split components (pixel-level by cell polygon): {len(split)}")

    split_set = set(split)
    out = {}
    for idx, (key, _) in enumerate(cells, start=1):
        whole_buf = bytearray(bw * bh)
        split_buf = bytearray(bw * bh)
        for i, lab in enumerate(labels):
            if lab:
                if whole.get(lab) == idx:
                    whole_buf[i] = 255
                elif lab in split_set:
                    split_buf[i] = 255

        def up(buf):
            m = Image.frombytes("L", (bw, bh), bytes(buf)).resize((bw * BLOCK, bh * BLOCK), Image.NEAREST)
            return m.crop((0, 0, w, h))

        pose_mask = up(whole_buf)
        if any(split_buf):
            in_cell = cell_map.point(lambda v, k=idx: 255 if v == k else 0)
            pose_mask = ImageChops.lighter(pose_mask, ImageChops.darker(up(split_buf), in_cell))

        r, g, b, a = img.split()
        a = ImageChops.darker(a, pose_mask)
        pose = Image.merge("RGBA", (r, g, b, a))
        bbox = binary_alpha(pose).getbbox()
        if not bbox:
            raise SystemExit(f"empty sprite for {key}")
        out[key] = (pose.crop(bbox), (bbox[0], bbox[1]))
        log(f"    {key}: src bbox {bbox} ({bbox[2] - bbox[0]}x{bbox[3] - bbox[1]})")
    return out


def is_greenish(p):
    return p[1] - max(p[0], p[2]) > 15


def erase_gauge_fill(img, cell_box):
    """Erase the painted green fill inside the gauge track (in place on img).

    Returns (track_rect_src (x0, y0, x1, y1) exclusive, fill_hex, track_hex).
    """
    px = img.load()
    cx0, cy0, cx1, cy1 = cell_box

    # Flood fill the inner track (bright, non-outline pixels) from a cream seed.
    def bright(p):
        return p[3] > 128 and p[0] + p[1] + p[2] > 330

    seed = None
    for sx in range((cx0 + cx1) * 2 // 3, cx1):
        sy = None
        # find a cream pixel on the gauge's vertical centre line
        col = [px[sx, y] for y in range(cy0, cy1)]
        # track centre = middle of the gauge's opaque span on this column
        ys = [i for i, p in enumerate(col) if p[3] > 128]
        if ys:
            sy = cy0 + (ys[0] + ys[-1]) // 2
            p = px[sx, sy]
            if bright(p) and not is_greenish(p):
                seed = (sx, sy)
                break
    if seed is None:
        raise SystemExit("gauge: track seed not found")

    region = Image.new("L", img.size, 0)
    rpx = region.load()
    q = deque([seed])
    rpx[seed] = 255
    x0 = x1 = seed[0]
    y0 = y1 = seed[1]
    while q:
        x, y = q.popleft()
        x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if cx0 <= nx < cx1 and cy0 <= ny < cy1 and not rpx[nx, ny] and bright(px[nx, ny]):
                rpx[nx, ny] = 255
                q.append((nx, ny))
    track = (x0, y0, x1 + 1, y1 + 1)

    greens = []
    creams = []
    g_end = x0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if rpx[x, y]:
                p = px[x, y]
                if is_greenish(p):
                    greens.append(p)
                    g_end = max(g_end, x)
    for y in range(y0 + 15, y1 - 15):
        for x in range(g_end + 40, x1 - 120):
            if rpx[x, y]:
                creams.append(px[x, y])
    if not greens:
        raise SystemExit("gauge: no green fill found")

    def med_hex(ps):
        return "#" + "".join(f"{int(statistics.median(p[i] for p in ps)):02x}" for i in range(3))

    fill_hex, track_hex = med_hex(greens), med_hex(creams)

    # Replace everything in the (slightly dilated) track left of the fill end with
    # texture copied from the cream part: mirrored around the track centre (so the
    # rounded left end gets the rounded right end), or shifted right where the
    # mirror would land on green as well.
    dil = region.crop(cell_box).filter(ImageFilter.MaxFilter(9))
    dpx = dil.load()
    limit = g_end + 10
    shift = (x1 - 200) - limit
    src = img.copy()
    spx = src.load()
    replaced = 0
    for y in range(max(cy0, y0 - 5), min(cy1, y1 + 6)):
        for x in range(max(cx0, x0 - 5), limit + 1):
            if not dpx[x - cx0, y - cy0]:
                continue
            sx = x0 + x1 - x
            if sx <= limit + 20:
                sx = x + shift
            px[x, y] = spx[sx, y]
            replaced += 1
    left = sum(1 for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if rpx[x, y] and is_greenish(px[x, y]))
    log(f"    gauge: track src {track}, green end x={g_end}, replaced {replaced}px, greenish left {left}")
    return track, fill_hex, track_hex


def group_scale(crops, keys, metric, target):
    if metric == "h":
        ref = max(crops[k][0].height for k in keys)
    else:
        ref = crops[metric[1]][0].width
    return target / ref


def resize_sprite(img, s):
    size = (max(1, round(img.width * s)), max(1, round(img.height * s)))
    return clean_alpha(img.resize(size, Image.LANCZOS))


def build_background():
    src = Image.open(os.path.join(SRC_DIR, "background-outdoors.png")).convert("RGB")
    w, h = src.size
    ch = round(w * 9 / 16)
    top = max(0, min(BG_CROP_TOP, h - ch))
    out = src.crop((0, top, w, top + ch)).resize(BG_OUT, Image.LANCZOS)
    os.makedirs(BG_DIR, exist_ok=True)
    out.save(os.path.join(BG_DIR, "background.png"), optimize=True)
    log(f"background: crop y {top}..{top + ch} of {w}x{h} -> {BG_OUT}")


def main():
    os.makedirs(SPRITE_DIR, exist_ok=True)
    crops = {}
    gauge_info = None
    for sheet, cells in SHEETS.items():
        log(f"sheet {sheet}")
        img = Image.open(os.path.join(SRC_DIR, sheet)).convert("RGBA")
        if sheet == "ui-sheet.png":
            gx0, gy0 = cells[0][1][0]
            gx1, gy1 = cells[0][1][2]
            gauge_info = erase_gauge_fill(img, (gx0, gy0, gx1, gy1))
        crops.update(extract_sheet(img, cells))

    missing = set(KEY_ORDER) - set(crops)
    if missing:
        raise SystemExit(f"missing keys: {sorted(missing)}")

    sprites = {}
    fill_rect = None
    for keys, metric, target in GROUPS:
        s = group_scale(crops, keys, metric, target)
        log(f"group {keys[0].split('_')[0]}: scale {s:.4f}")
        for k in keys:
            crop, (ox, oy) = crops[k]
            out = resize_sprite(crop, s)
            out.save(os.path.join(SPRITE_DIR, f"{k}.png"), optimize=True)
            sprites[k] = {"src": f"sprites/{k}.png", "w": out.width, "h": out.height,
                          "anchorX": 0.5, "anchorY": 1.0}
            if k == "ui_gauge_frame":
                tx0, ty0, tx1, ty1 = gauge_info[0]
                fx0 = round((tx0 - ox) * s)
                fy0 = round((ty0 - oy) * s)
                fx1 = round((tx1 - ox) * s)
                fy1 = round((ty1 - oy) * s)
                fill_rect = {"x": fx0, "y": fy0, "w": fx1 - fx0, "h": fy1 - fy0}

    build_background()

    manifest = {
        "version": 1,
        "background": {"src": "bg/background.png", "w": BG_OUT[0], "h": BG_OUT[1]},
        "sprites": {k: sprites[k] for k in KEY_ORDER},
        "gauge": {"fillRect": fill_rect, "fillColor": gauge_info[1], "trackColor": gauge_info[2]},
    }
    with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    total = 0
    for dirpath, _, files in os.walk(OUT_DIR):
        for fn in files:
            total += os.path.getsize(os.path.join(dirpath, fn))
    log(f"done: {len(sprites)} sprites, gauge fillRect {fill_rect}, total {total} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
