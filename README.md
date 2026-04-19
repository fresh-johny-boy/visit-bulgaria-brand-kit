# Visit Bulgaria — Brand Kit

Production iOS + Android + web icons, plus a 31-sound UI kit. Everything a developer needs to ship a Visit Bulgaria surface.

**Live site:** <https://YOUR-ORG.github.io/brand-kit/>

---

## Quick download

- **Everything** — [visit-bulgaria-brand-kit.zip](downloads/visit-bulgaria-brand-kit.zip) (≈2.8 MB · 78 files)
- **Icons only** — [visit-bulgaria-icons.zip](downloads/visit-bulgaria-icons.zip) (≈2.1 MB · 43 files)
- **iOS** — [visit-bulgaria-icons-ios.zip](downloads/visit-bulgaria-icons-ios.zip) (≈461 KB)
- **Android** — [visit-bulgaria-icons-android.zip](downloads/visit-bulgaria-icons-android.zip) (≈255 KB)
- **Web / PWA / social** — [visit-bulgaria-icons-web.zip](downloads/visit-bulgaria-icons-web.zip) (≈396 KB)
- **Sounds** — [visit-bulgaria-sounds.zip](downloads/visit-bulgaria-sounds.zip) (≈653 KB · 31 WAVs)

---

## What’s in the repo

```
brand-kit/
├── index.html                 # unified landing page (GitHub Pages root)
├── icons/                     # icon documentation + assets
│   ├── index.html             # icon system docs
│   ├── README.md              # design rationale
│   ├── brand-bar_icon.svg     # source lockup
│   ├── master/                # 1024 masters
│   ├── ios/                   # Xcode AppIcon.appiconset
│   ├── android/               # Android res/mipmap-*
│   ├── web/                   # favicons, PWA, OG card
│   ├── preview/               # mock renders
│   └── _work/                 # build scripts
├── sounds/                    # UI sound kit
│   ├── index.html             # interactive player
│   ├── README.md              # sound kit docs
│   ├── LICENSE.md             # usage terms
│   ├── *.wav                  # 31 synthesised sounds
│   └── generate.py            # regenerate from scratch
├── downloads/                 # zipped bundles (built by _build/build_zips.py)
└── _build/
    └── build_zips.py          # zip bundler
```

---

## Integration quick-start

### iOS (Xcode)

```bash
unzip visit-bulgaria-icons-ios.zip
cp -R ios/AppIcon.appiconset/ <App>/Assets.xcassets/AppIcon.appiconset/
```

In **Build Settings ▸ App Icon & Launch Screen**, set *App Icon Source* to `AppIcon`.

### Android (Studio)

```bash
unzip visit-bulgaria-icons-android.zip
cp -R android/mipmap-* app/src/main/res/
```

In `AndroidManifest.xml`:

```xml
<application
    android:icon="@mipmap/ic_launcher"
    android:roundIcon="@mipmap/ic_launcher_round">
```

### Web

```bash
unzip visit-bulgaria-icons-web.zip
cp -R web/* <site-root>/
```

Paste the `<head>` snippet in `web/usage.html` into every page.

### Sounds

```bash
unzip visit-bulgaria-sounds.zip
```

```js
const sfx = new Audio('sounds/click-soft.wav');
sfx.play();
```

See [`sounds/README.md`](sounds/README.md) for the recommended event mapping.

---

## Regenerate from source

All assets are deterministic. Requires Python 3 + Pillow + Inkscape.

```bash
# Rebuild every icon from brand-bar_icon.svg
python3 icons/_work/build_icons.py
python3 icons/_work/build_web_icons.py

# Rebuild every sound from generate.py
python3 sounds/generate.py

# Rebuild the download archives
python3 _build/build_zips.py
```

---

## Hosting

This folder is a drop-in GitHub Pages root. Every asset path is relative; just enable Pages on the `main` branch, root directory.

```bash
git init
git add -A
git commit -m "Initial brand kit"
gh repo create visit-bulgaria-brand-kit --public --source=. --push
gh api repos/:owner/visit-bulgaria-brand-kit/pages -X POST \
  -f source[branch]=main -f source[path]=/
```

After a minute the kit is live at `https://<owner>.github.io/visit-bulgaria-brand-kit/`.

---

## Licence

Icons are derivatives of the Visit Bulgaria brand-bar lockup — use for Visit Bulgaria properties only.
Sounds are licensed exclusively for use within the Visit Bulgaria mobile app, website, and brand properties. Third-party use requires written permission — see [`sounds/LICENSE.md`](sounds/LICENSE.md).
