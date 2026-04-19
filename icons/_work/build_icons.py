#!/usr/bin/env python3
"""
Visit Bulgaria — App Icon Generator.

Source: ../../brand-bar_icon.svg (the Bulgaria rose + БЪЛГАРИЯ wordmark, single colour #004F46).

For an app icon the wordmark is unreadable at ~60 pt, so we isolate the rose and
compose it onto platform-specific canvases per Apple HIG + Android adaptive icon spec.

Outputs:
  app-icon/
    master/
      primary-1024.png         # teal bg + white rose (main) — aligns with cool-neutral product UI
      alt-brand-faithful-1024.png   # cream bg + teal rose (alt) — lockup-faithful
      rose-foreground-1024.png # rose on transparent (for Android adaptive foreground)
      rose-monochrome-1024.png # rose silhouette (for Android themed icon)
    ios/AppIcon.appiconset/
      icon-1024.png + Contents.json   # modern single-size entry
    android/
      mipmap-anydpi-v26/ic_launcher.xml                # adaptive spec
      mipmap-xxxhdpi/ic_launcher_foreground.png  (432)
      mipmap-xxxhdpi/ic_launcher_background.png  (432)
      mipmap-xxxhdpi/ic_launcher_monochrome.png  (432)
      mipmap-{xxhdpi,xhdpi,hdpi,mdpi}/ic_launcher.png  (legacy round+square fallback)
      playstore-512.png
    preview/
      home-screen-ios.png
      home-screen-android.png
"""

from __future__ import annotations
import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter
from collections import deque

# ---- Config -----------------------------------------------------------------
# Paths are resolved relative to this script so the repo is portable.
WORK = Path(__file__).resolve().parent
OUT = WORK.parent                      # …/icons/
SRC_SVG = OUT / "brand-bar_icon.svg"

# Brand colours
TEAL = (0x00, 0x4F, 0x46)          # #004F46 — logo colour
CREAM = (0xF7, 0xEF, 0xE1)         # warm off-white — used only for brand-faithful alt background
WHITE = (0xFF, 0xFF, 0xFF)         # primary rose fill — matches the cool-neutral product UI (#ffffff cards)
# Slight darker teal for the radial gradient vignette
TEAL_DARK = (0x00, 0x38, 0x32)     # #003832

# Icon compositing
MASTER_PX = 1024                   # iOS App Store + source of truth
ROSE_SAFE_RATIO = 0.68             # rose occupies ~68% of the canvas diagonal span
                                   # fits Apple HIG visual bounds (~80% hard limit)
                                   # and Android safe zone (66% circle)
ANDROID_FG_PX = 432                # 108dp × 4 (xxxhdpi) for adaptive foreground
ANDROID_FG_SAFE_RATIO = 0.60       # rose sits within the 66dp launcher safe circle

# ---- Helpers ----------------------------------------------------------------

def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def render_svg_to_png(svg: Path, out: Path, width: int) -> None:
    """Rasterize the source SVG at a given pixel width via Inkscape."""
    run([
        "inkscape", str(svg),
        "--export-type=png",
        f"--export-filename={out}",
        f"--export-width={width}",
        "--export-background-opacity=0",
    ])


def find_rose_bbox(full_render: Image.Image) -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) of the rose only.

    The rose and the БЪЛГАРИЯ wordmark touch vertically (letter tops overlap
    the rose's descending stroke row), so we can't look for an empty row.
    Instead we find the `valley` in per-row ink counts between the two big
    content blocks and cut there.
    """
    w, h = full_render.size
    alpha = full_render.split()[-1]

    # Per-row ink count (fast: numpy-like but using bytes).
    row_ink = []
    for y in range(h):
        row = alpha.crop((0, y, w, y + 1)).tobytes()
        row_ink.append(sum(1 for b in row if b > 8))

    # Top of rose = first non-zero row.
    top = next(i for i, c in enumerate(row_ink) if c > 0)

    # Valley search in the middle band (35%-75% of height) — that's where the
    # gap between rose and wordmark lives.
    lo, hi = int(h * 0.35), int(h * 0.75)
    valley_y = lo + min(range(hi - lo), key=lambda i: row_ink[lo + i])

    # Walk up from the valley until we re-enter the rose proper.
    # Use 20% of per-row peak — skips the thin brushstroke descender tail but
    # lands on the rose's visual body, which produces a clean silhouette at
    # icon sizes (the tail doesn't read below ~60 pt anyway).
    peak = max(row_ink)
    threshold = peak * 0.20
    rose_bottom = valley_y
    for y in range(valley_y, top, -1):
        if row_ink[y] >= threshold:
            rose_bottom = y
            break

    # Horizontal bbox inside (top, rose_bottom).
    px = alpha.load()
    left, right = w, 0
    for y in range(top, rose_bottom + 1):
        for x in range(w):
            if px[x, y] > 8:
                if x < left:
                    left = x
                if x > right:
                    right = x
    return (left, top, right + 1, rose_bottom + 1)


def keep_largest_component(src: Image.Image, min_ratio: float = 0.05) -> Image.Image:
    """Flood-fill the alpha channel, keep only components >= min_ratio of the
    largest one. Dropped pixels are set transparent.

    Removes the brushstroke descender and stray specks, leaving the main rose.
    Downsamples for speed (full 4K BFS is fine but we work at 1024).
    """
    src = src.convert("RGBA")
    w, h = src.size
    a = src.split()[-1]
    ink = [[1 if a.getpixel((x, y)) > 8 else 0 for x in range(w)] for y in range(h)]
    labels = [[0] * w for _ in range(h)]
    sizes: list[int] = [0]
    next_label = 1
    for y in range(h):
        for x in range(w):
            if ink[y][x] and labels[y][x] == 0:
                # BFS
                q = deque([(x, y)])
                labels[y][x] = next_label
                size = 0
                while q:
                    cx, cy = q.popleft()
                    size += 1
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h and ink[ny][nx] and labels[ny][nx] == 0:
                            labels[ny][nx] = next_label
                            q.append((nx, ny))
                sizes.append(size)
                next_label += 1
    if not sizes[1:]:
        return src
    biggest = max(sizes[1:])
    keep_min = biggest * min_ratio
    out = src.copy()
    px = out.load()
    for y in range(h):
        for x in range(w):
            lbl = labels[y][x]
            if lbl and sizes[lbl] < keep_min:
                r, g, b, _ = px[x, y]
                px[x, y] = (r, g, b, 0)
    return out


def recolor(src: Image.Image, rgb: tuple[int, int, int]) -> Image.Image:
    """Replace every non-transparent pixel's colour with `rgb`, preserving alpha."""
    src = src.convert("RGBA")
    r, g, b, a = src.split()
    new_r = Image.new("L", src.size, rgb[0])
    new_g = Image.new("L", src.size, rgb[1])
    new_b = Image.new("L", src.size, rgb[2])
    return Image.merge("RGBA", (new_r, new_g, new_b, a))


def radial_gradient_bg(size: int, centre_rgb, edge_rgb) -> Image.Image:
    """Render a subtle radial gradient: centre → edge. Light from top-left."""
    img = Image.new("RGB", (size, size), edge_rgb)
    px = img.load()
    cx, cy = size * 0.38, size * 0.35  # light source upper-left-ish
    max_d = math.hypot(size, size) * 0.85
    cr, cg, cb = centre_rgb
    er, eg, eb = edge_rgb
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - cx, y - cy) / max_d
            t = min(1.0, max(0.0, d))
            # ease (smoothstep)
            t = t * t * (3 - 2 * t)
            px[x, y] = (
                int(cr * (1 - t) + er * t),
                int(cg * (1 - t) + eg * t),
                int(cb * (1 - t) + eb * t),
            )
    return img


def place_rose(canvas: Image.Image, rose: Image.Image, safe_ratio: float,
               y_offset_ratio: float = -0.015) -> Image.Image:
    """Place the rose centred on `canvas`, fitting inside the safe-area circle.

    safe_ratio is the rose's **diameter** as a fraction of the canvas edge.
    """
    cw, ch = canvas.size
    target_edge = int(cw * safe_ratio)
    rose = rose.copy()
    # fit rose inside target_edge square maintaining aspect ratio
    rose.thumbnail((target_edge, target_edge), Image.LANCZOS)
    rw, rh = rose.size
    x = (cw - rw) // 2
    y = (ch - rh) // 2 + int(ch * y_offset_ratio)
    out = canvas.convert("RGBA").copy()
    out.alpha_composite(rose, (x, y))
    return out


def to_rgb_no_alpha(img: Image.Image, bg_rgb) -> Image.Image:
    """Flatten RGBA onto a solid background — iOS icons must not have alpha."""
    bg = Image.new("RGB", img.size, bg_rgb)
    bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
    return bg


# ---- Main pipeline ----------------------------------------------------------

def main() -> None:
    OUT.mkdir(exist_ok=True)
    WORK.mkdir(exist_ok=True)
    master_dir = OUT / "master"
    master_dir.mkdir(exist_ok=True)

    # 1. Render source SVG at a large size so the rose crop stays crisp.
    render = WORK / "source-4096.png"
    render_svg_to_png(SRC_SVG, render, width=4096)
    full = Image.open(render).convert("RGBA")

    # 2. Isolate the rose — strip wordmark + underline stroke.
    bbox = find_rose_bbox(full)
    print(f"  rose bbox: {bbox}  (from canvas {full.size})")
    rose_raw = full.crop(bbox)

    # Save the isolated rose at master resolution for reuse.
    # Scale the tight rose crop up into a square canvas with small breathing room.
    rw, rh = rose_raw.size
    square = max(rw, rh)
    padded = Image.new("RGBA", (square, square), (0, 0, 0, 0))
    padded.paste(rose_raw, ((square - rw) // 2, (square - rh) // 2))
    rose_square = padded.resize((MASTER_PX, MASTER_PX), Image.LANCZOS)

    # Drop the brushstroke descender + any stray specks — keep only the
    # main rose body for a clean icon silhouette.
    rose_square = keep_largest_component(rose_square, min_ratio=0.05)

    # Foreground on transparent — Android adaptive foreground source.
    (master_dir / "rose-foreground-1024.png").write_bytes(b"")  # touch
    rose_square.save(master_dir / "rose-foreground-1024.png")

    # Monochrome version (recolored to pure black for themed-icon tinting).
    mono = recolor(rose_square, (0, 0, 0))
    mono.save(master_dir / "rose-monochrome-1024.png")

    # White rose for the primary icon — aligns with cool-neutral product UI.
    rose_white = recolor(rose_square, WHITE)

    # 3. Build PRIMARY master (teal bg + white rose + subtle gradient).
    bg_primary = radial_gradient_bg(MASTER_PX, centre_rgb=TEAL, edge_rgb=TEAL_DARK)
    primary = place_rose(bg_primary, rose_white, safe_ratio=ROSE_SAFE_RATIO)
    primary = to_rgb_no_alpha(primary, TEAL)
    primary.save(master_dir / "primary-1024.png", optimize=True)

    # 4. Build ALTERNATE (cream bg + teal rose — brand-bar-faithful).
    bg_alt = radial_gradient_bg(MASTER_PX, centre_rgb=(0xFD, 0xF7, 0xEB), edge_rgb=CREAM)
    rose_teal = recolor(rose_square, TEAL)
    alt = place_rose(bg_alt, rose_teal, safe_ratio=ROSE_SAFE_RATIO)
    alt = to_rgb_no_alpha(alt, CREAM)
    alt.save(master_dir / "alt-brand-faithful-1024.png", optimize=True)

    # --- iOS ---------------------------------------------------------------
    ios_dir = OUT / "ios" / "AppIcon.appiconset"
    ios_dir.mkdir(parents=True, exist_ok=True)
    primary.save(ios_dir / "icon-1024.png", optimize=True)

    contents = {
        "images": [{
            "filename": "icon-1024.png",
            "idiom": "universal",
            "platform": "ios",
            "size": "1024x1024",
        }],
        "info": {"author": "xcode", "version": 1},
    }
    (ios_dir / "Contents.json").write_text(json.dumps(contents, indent=2))

    # Dark variant (iOS 18+ — same rose on darker teal)
    dark_bg = radial_gradient_bg(MASTER_PX, centre_rgb=(0x00, 0x2A, 0x26),
                                 edge_rgb=(0x00, 0x17, 0x14))
    dark = place_rose(dark_bg, rose_white, safe_ratio=ROSE_SAFE_RATIO)
    dark = to_rgb_no_alpha(dark, (0x00, 0x17, 0x14))
    dark.save(ios_dir / "icon-1024-dark.png", optimize=True)

    # Tinted variant (iOS 18+ — grayscale, system tints)
    tinted = recolor(rose_square, (255, 255, 255))
    bg_tint = Image.new("RGB", (MASTER_PX, MASTER_PX), (0, 0, 0))
    tint_img = place_rose(bg_tint, tinted, safe_ratio=ROSE_SAFE_RATIO)
    tint_img = to_rgb_no_alpha(tint_img, (0, 0, 0))
    tint_img.save(ios_dir / "icon-1024-tinted.png", optimize=True)

    contents["images"] = [
        {"filename": "icon-1024.png", "idiom": "universal", "platform": "ios", "size": "1024x1024"},
        {"filename": "icon-1024-dark.png", "idiom": "universal", "platform": "ios",
         "size": "1024x1024", "appearances": [{"appearance": "luminosity", "value": "dark"}]},
        {"filename": "icon-1024-tinted.png", "idiom": "universal", "platform": "ios",
         "size": "1024x1024", "appearances": [{"appearance": "luminosity", "value": "tinted"}]},
    ]
    (ios_dir / "Contents.json").write_text(json.dumps(contents, indent=2))

    # --- Android adaptive icon --------------------------------------------
    android_dir = OUT / "android"
    android_dir.mkdir(exist_ok=True)

    densities = {
        "mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192,
    }
    # Adaptive foreground/background live at 108dp (432 px @ xxxhdpi).
    # Foreground: transparent rose (white) on transparent canvas, sized to safe ratio.
    fg_canvas = Image.new("RGBA", (ANDROID_FG_PX, ANDROID_FG_PX), (0, 0, 0, 0))
    fg = place_rose(fg_canvas, rose_white, safe_ratio=ANDROID_FG_SAFE_RATIO)
    # Background: solid teal (no gradient — Android adaptive masks can crop wildly)
    bg = Image.new("RGB", (ANDROID_FG_PX, ANDROID_FG_PX), TEAL)
    # Monochrome: rose as solid black on transparent, same safe zone
    mono_canvas = Image.new("RGBA", (ANDROID_FG_PX, ANDROID_FG_PX), (0, 0, 0, 0))
    mono_fg = place_rose(mono_canvas, mono, safe_ratio=ANDROID_FG_SAFE_RATIO)

    xxx = android_dir / "mipmap-xxxhdpi"
    xxx.mkdir(exist_ok=True)
    fg.save(xxx / "ic_launcher_foreground.png", optimize=True)
    bg.save(xxx / "ic_launcher_background.png", optimize=True)
    mono_fg.save(xxx / "ic_launcher_monochrome.png", optimize=True)

    # Legacy square+round launcher fallback for pre-O devices.
    # Compose primary icon clipped to a squircle mask per density.
    for d, size in densities.items():
        ddir = android_dir / f"mipmap-{d}"
        ddir.mkdir(exist_ok=True)
        ic = primary.resize((size, size), Image.LANCZOS)
        ic.save(ddir / "ic_launcher.png", optimize=True)
        # Round variant (circular mask)
        circle_mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(circle_mask).ellipse((0, 0, size, size), fill=255)
        round_ic = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        round_ic.paste(ic, (0, 0), circle_mask)
        round_ic.save(ddir / "ic_launcher_round.png", optimize=True)

    # mipmap-anydpi-v26 — adaptive XML descriptors
    v26 = android_dir / "mipmap-anydpi-v26"
    v26.mkdir(exist_ok=True)
    (v26 / "ic_launcher.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
    <monochrome android:drawable="@mipmap/ic_launcher_monochrome" />
</adaptive-icon>
""")
    (v26 / "ic_launcher_round.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
    <monochrome android:drawable="@mipmap/ic_launcher_monochrome" />
</adaptive-icon>
""")

    # Play Store asset: 512×512 full-bleed PNG 32-bit.
    primary.resize((512, 512), Image.LANCZOS).save(
        android_dir / "playstore-512.png", optimize=True
    )

    # --- Previews ---------------------------------------------------------
    preview_dir = OUT / "preview"
    preview_dir.mkdir(exist_ok=True)
    make_preview_ios(primary, preview_dir / "home-screen-ios.png")
    make_preview_android_squircle(primary, preview_dir / "home-screen-android.png")
    make_size_grid(primary, preview_dir / "size-grid.png")

    print("\nDone. Output at:", OUT)


def squircle_mask(size: int, radius_ratio: float = 0.2237) -> Image.Image:
    """Approximation of iOS squircle via rounded-rect (close enough for previews)."""
    mask = Image.new("L", (size, size), 0)
    r = int(size * radius_ratio)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), radius=r, fill=255)
    return mask


def make_preview_ios(primary: Image.Image, out: Path) -> None:
    """Mock iOS home-screen tile with squircle mask + drop shadow."""
    W = 640
    canvas = Image.new("RGB", (W, W), (24, 24, 28))
    # Subtle wallpaper gradient
    px = canvas.load()
    for y in range(W):
        t = y / W
        px[0, y]  # ensure load
        for x in range(W):
            r = int(30 * (1 - t) + 12 * t)
            g = int(34 * (1 - t) + 18 * t)
            b = int(46 * (1 - t) + 30 * t)
            px[x, y] = (r, g, b)
    # Place the icon at 60% width, centred
    tile = primary.resize((int(W * 0.56), int(W * 0.56)), Image.LANCZOS)
    mask = squircle_mask(tile.size[0])
    masked = Image.new("RGBA", tile.size, (0, 0, 0, 0))
    masked.paste(tile, (0, 0), mask)
    # Drop shadow
    shadow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 110), (0, 0, tile.size[0], tile.size[1]), mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=14))
    pos = ((W - tile.size[0]) // 2, (W - tile.size[1]) // 2)
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.alpha_composite(shadow, (pos[0] + 4, pos[1] + 18))
    canvas_rgba.alpha_composite(masked, pos)
    canvas_rgba.convert("RGB").save(out, optimize=True)


def make_preview_android_squircle(primary: Image.Image, out: Path) -> None:
    """Mock an Android launcher with squircle + circle mask side-by-side."""
    W = 900
    H = W // 2
    canvas = Image.new("RGB", (W, H), (246, 246, 248)).convert("RGBA")
    tile_size = int(W * 0.32)
    mask_sq = squircle_mask(tile_size, radius_ratio=0.28)
    mask_circle = Image.new("L", (tile_size, tile_size), 0)
    ImageDraw.Draw(mask_circle).ellipse((0, 0, tile_size, tile_size), fill=255)
    tile = primary.resize((tile_size, tile_size), Image.LANCZOS).convert("RGBA")

    def paste_onto(canvas_rgba, mask, x):
        masked = Image.new("RGBA", (tile_size, tile_size), (0, 0, 0, 0))
        masked.paste(tile, (0, 0), mask)
        sh = Image.new("RGBA", (tile_size, tile_size), (0, 0, 0, 0))
        sh.paste((0, 0, 0, 60), (0, 0, tile_size, tile_size), mask)
        big_sh = Image.new("RGBA", canvas_rgba.size, (0, 0, 0, 0))
        y = (H - tile_size) // 2
        big_sh.paste(sh, (x + 3, y + 10))
        big_sh = big_sh.filter(ImageFilter.GaussianBlur(radius=10))
        canvas_rgba.alpha_composite(big_sh, (0, 0))
        canvas_rgba.alpha_composite(masked, (x, y))
        return canvas_rgba

    canvas = paste_onto(canvas, mask_sq, int(W * 0.10))
    canvas = paste_onto(canvas, mask_circle, int(W * 0.58))
    canvas.convert("RGB").save(out, optimize=True)


def make_size_grid(primary: Image.Image, out: Path) -> None:
    """Grid showing how the icon reads at real device sizes."""
    sizes = [180, 120, 87, 60, 40]  # iOS @3x real render sizes in px
    pad = 32
    W = sum(sizes) + pad * (len(sizes) + 1)
    H = max(sizes) + pad * 2
    canvas = Image.new("RGB", (W, H), (240, 240, 244))
    x = pad
    for s in sizes:
        tile = primary.resize((s, s), Image.LANCZOS)
        mask = squircle_mask(s, radius_ratio=0.22)
        masked = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        masked.paste(tile, (0, 0), mask)
        shadow = Image.new("RGBA", (s + 20, s + 20), (0, 0, 0, 0))
        sh_m = squircle_mask(s, radius_ratio=0.22)
        shadow.paste((0, 0, 0, 40), (10, 10), sh_m)
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=6))
        c = canvas.convert("RGBA")
        y = (H - s) // 2
        c.alpha_composite(shadow, (x - 10, y - 6))
        c.alpha_composite(masked, (x, y))
        canvas = c.convert("RGB")
        x += s + pad
    canvas.save(out, optimize=True)


if __name__ == "__main__":
    main()
