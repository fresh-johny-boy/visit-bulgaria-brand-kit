#!/usr/bin/env python3
"""
Visit Bulgaria — brand kit zip bundler.

Creates the downloadable archives served by the Pages site:

  downloads/
    visit-bulgaria-brand-kit.zip           # everything (icons + sounds + docs)
    visit-bulgaria-icons.zip               # all icon platforms
    visit-bulgaria-icons-ios.zip           # iOS only
    visit-bulgaria-icons-android.zip       # Android only
    visit-bulgaria-icons-web.zip           # web / PWA / social only
    visit-bulgaria-sounds.zip              # UI sound kit

Run from anywhere:  python3 brand-kit/_build/build_zips.py
"""

from __future__ import annotations
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent       # …/brand-kit/
ICONS = REPO / "icons"
SOUNDS = REPO / "sounds"
OUT = REPO / "downloads"


def make_zip(dest: Path, roots: list[tuple[Path, str]], extra: list[tuple[Path, str]] = None) -> None:
    """Write a zip.

    roots: list of (absolute_path_to_dir, prefix_inside_zip)
    extra: list of (absolute_path_to_file, path_inside_zip)
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()

    skip_names = {".DS_Store", "__pycache__"}
    skip_dirs = {"_work", "_build", "downloads"}

    count = 0
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for src_dir, prefix in roots:
            if not src_dir.exists():
                continue
            for path in sorted(src_dir.rglob("*")):
                if path.is_dir():
                    continue
                if path.name in skip_names:
                    continue
                parts = set(path.relative_to(src_dir).parts)
                if parts & skip_dirs:
                    continue
                arcname = f"{prefix}/{path.relative_to(src_dir).as_posix()}" if prefix else path.relative_to(src_dir).as_posix()
                zf.write(path, arcname)
                count += 1
        for src_file, arcname in (extra or []):
            if src_file.exists():
                zf.write(src_file, arcname)
                count += 1

    size_kb = dest.stat().st_size // 1024
    print(f"  · {dest.name:<48} {count:>4} files  {size_kb:>6} KB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"writing archives to {OUT}/\n")

    readme_repo = REPO / "README.md"

    # Per-platform icon bundles
    make_zip(
        OUT / "visit-bulgaria-icons-ios.zip",
        roots=[(ICONS / "ios", "ios")],
        extra=[(ICONS / "README.md", "README.md")] if (ICONS / "README.md").exists() else [],
    )
    make_zip(
        OUT / "visit-bulgaria-icons-android.zip",
        roots=[(ICONS / "android", "android")],
        extra=[(ICONS / "README.md", "README.md")] if (ICONS / "README.md").exists() else [],
    )
    make_zip(
        OUT / "visit-bulgaria-icons-web.zip",
        roots=[(ICONS / "web", "web")],
        extra=[(ICONS / "README.md", "README.md")] if (ICONS / "README.md").exists() else [],
    )

    # All icons (master + every platform + preview + source SVG)
    make_zip(
        OUT / "visit-bulgaria-icons.zip",
        roots=[
            (ICONS / "master", "icons/master"),
            (ICONS / "ios", "icons/ios"),
            (ICONS / "android", "icons/android"),
            (ICONS / "web", "icons/web"),
            (ICONS / "preview", "icons/preview"),
        ],
        extra=[
            (ICONS / "README.md", "icons/README.md"),
            (ICONS / "brand-bar_icon.svg", "icons/brand-bar_icon.svg"),
        ],
    )

    # Sounds only
    make_zip(
        OUT / "visit-bulgaria-sounds.zip",
        roots=[(SOUNDS, "sounds")],
    )

    # Everything
    make_zip(
        OUT / "visit-bulgaria-brand-kit.zip",
        roots=[
            (ICONS / "master", "icons/master"),
            (ICONS / "ios", "icons/ios"),
            (ICONS / "android", "icons/android"),
            (ICONS / "web", "icons/web"),
            (ICONS / "preview", "icons/preview"),
            (SOUNDS, "sounds"),
        ],
        extra=[
            (ICONS / "README.md", "icons/README.md"),
            (ICONS / "brand-bar_icon.svg", "icons/brand-bar_icon.svg"),
            (readme_repo, "README.md") if readme_repo.exists() else (ICONS / "README.md", "README.md"),
        ],
    )

    print(f"\ndone — {len(list(OUT.glob('*.zip')))} archives in {OUT}")


if __name__ == "__main__":
    main()
