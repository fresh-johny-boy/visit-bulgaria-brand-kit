#!/usr/bin/env python3
"""
Visit Bulgaria — web / browser / PWA / social icon set.

Generates every asset a modern website needs, from the primary master:
  favicon.ico (multi-size), favicon-{16,32,48,64}.png,
  apple-touch-icon.png (180), icon-{192,512}.png (PWA),
  icon-maskable-{192,512}.png (PWA adaptive),
  mstile-150.png (Windows),
  og-image.png (1200×630 social share),
  site.webmanifest (PWA manifest example),
  usage.html (drop-in <head> snippet).

Run after build_icons.py — consumes master/primary-1024.png.
"""

from __future__ import annotations
import json
import math
from pathlib import Path

from PIL import Image

WORK = Path(__file__).resolve().parent
ICONS = WORK.parent                    # …/icons/
MASTER = ICONS / "master" / "primary-1024.png"
ROSE_FG = ICONS / "master" / "rose-foreground-1024.png"
LOCKUP = WORK / "source-4096.png"      # full brand-bar lockup (rendered by build_icons.py)
OUT = ICONS / "web"

TEAL = (0x00, 0x4F, 0x46)
TEAL_DARK = (0x00, 0x38, 0x32)


def sq(src: Image.Image, size: int, out: Path) -> None:
    src.resize((size, size), Image.LANCZOS).save(out, optimize=True)
    print(f"  · {out.name}  ({out.stat().st_size // 1024 or 1} KB)")


def build_ico(src: Image.Image, out: Path, sizes=(16, 32, 48)) -> None:
    """Multi-size ICO — includes 16/32/48 so OSes pick the crispest bucket."""
    src.save(out, sizes=[(s, s) for s in sizes])
    print(f"  · {out.name}  ({out.stat().st_size // 1024 or 1} KB) — {sizes}")


def radial_bg(size, centre_rgb, edge_rgb, cx_ratio=0.38, cy_ratio=0.35) -> Image.Image:
    w, h = size if isinstance(size, tuple) else (size, size)
    img = Image.new("RGB", (w, h), edge_rgb)
    px = img.load()
    cx, cy = w * cx_ratio, h * cy_ratio
    max_d = math.hypot(w, h) * 0.85
    cr, cg, cb = centre_rgb
    er, eg, eb = edge_rgb
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy) / max_d
            t = min(1.0, max(0.0, d))
            t = t * t * (3 - 2 * t)
            px[x, y] = (
                int(cr * (1 - t) + er * t),
                int(cg * (1 - t) + eg * t),
                int(cb * (1 - t) + eb * t),
            )
    return img


def build_og(out: Path) -> None:
    """1200×630 Open Graph / Twitter / iMessage social card.

    Teal gradient background with the full brand-bar lockup (rose + БЪЛГАРИЯ
    wordmark) recoloured white and centred. Uses the full SVG render at
    4096×3230 already produced by build_icons.py.
    """
    W, H = 1200, 630
    canvas = radial_bg((W, H), centre_rgb=TEAL, edge_rgb=TEAL_DARK,
                       cx_ratio=0.50, cy_ratio=0.42).convert("RGBA")

    # Full lockup (rose + wordmark + brushstroke underline).
    assert LOCKUP.exists(), f"missing {LOCKUP} — run build_icons.py first"
    lockup = Image.open(LOCKUP).convert("RGBA")

    # Tight-crop transparent margins so scaling is content-based, not canvas-based.
    bbox = lockup.getbbox()
    if bbox:
        lockup = lockup.crop(bbox)

    # Recolour every inked pixel to white, preserving alpha.
    _r, _g, _b, a = lockup.split()
    lockup = Image.merge("RGBA", (
        Image.new("L", lockup.size, 255),
        Image.new("L", lockup.size, 255),
        Image.new("L", lockup.size, 255),
        a,
    ))

    # Fit lockup inside a 72%-of-height safe box, preserving aspect ratio.
    max_h = int(H * 0.72)
    max_w = int(W * 0.72)
    lw, lh = lockup.size
    scale = min(max_w / lw, max_h / lh)
    new_size = (max(1, int(lw * scale)), max(1, int(lh * scale)))
    lockup = lockup.resize(new_size, Image.LANCZOS)

    # Centre.
    x = (W - lockup.size[0]) // 2
    y = (H - lockup.size[1]) // 2
    canvas.alpha_composite(lockup, (x, y))

    canvas.convert("RGB").save(out, optimize=True)
    print(f"  · {out.name}  ({out.stat().st_size // 1024} KB) — 1200×630 · full lockup")


def build_manifest(out: Path) -> None:
    payload = {
        "name": "Visit Bulgaria",
        "short_name": "Visit BG",
        "description": "Discover Bulgaria — places, routes, and events.",
        "start_url": "/",
        "display": "standalone",
        "theme_color": "#004F46",
        "background_color": "#004F46",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "/icon-maskable-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
            {"src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"  · {out.name}")


def build_usage(out: Path) -> None:
    snippet = """<!-- Visit Bulgaria — favicons, PWA, social. Paste into <head>. -->
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#004F46">
<meta name="msapplication-TileColor" content="#004F46">
<meta name="msapplication-TileImage" content="/mstile-150.png">

<!-- Open Graph / social -->
<meta property="og:image" content="/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Visit Bulgaria">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="/og-image.png">
"""
    out.write_text(snippet)
    print(f"  · {out.name}")


def main() -> None:
    assert MASTER.exists(), f"missing {MASTER} — run build_icons.py first"
    OUT.mkdir(parents=True, exist_ok=True)

    master = Image.open(MASTER).convert("RGBA")
    print(f"source: {MASTER.name}  ({master.size[0]}×{master.size[1]})\nwriting to {OUT}/")

    # Classic favicons
    sq(master, 16, OUT / "favicon-16.png")
    sq(master, 32, OUT / "favicon-32.png")
    sq(master, 48, OUT / "favicon-48.png")
    sq(master, 64, OUT / "favicon-64.png")
    build_ico(master, OUT / "favicon.ico", sizes=(16, 32, 48))

    # Apple touch
    sq(master, 180, OUT / "apple-touch-icon.png")

    # PWA standard
    sq(master, 192, OUT / "icon-192.png")
    sq(master, 512, OUT / "icon-512.png")

    # PWA maskable — rose at 68% of canvas sits inside the 80% safe zone,
    # so the primary is already maskable-compliant. Duplicate with the
    # `maskable` suffix so the manifest can declare purpose explicitly.
    sq(master, 192, OUT / "icon-maskable-192.png")
    sq(master, 512, OUT / "icon-maskable-512.png")

    # Windows tile
    sq(master, 150, OUT / "mstile-150.png")

    # Social / OG card
    build_og(OUT / "og-image.png")

    # PWA manifest + usage snippet
    build_manifest(OUT / "site.webmanifest")
    build_usage(OUT / "usage.html")

    print(f"\ndone. {len(list(OUT.iterdir()))} files in {OUT}")


if __name__ == "__main__":
    main()
