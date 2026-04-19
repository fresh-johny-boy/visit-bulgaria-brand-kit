# Visit Bulgaria — Mobile App Icon

Production iOS + Android app-icon set generated from `../brand-bar_icon.svg` (the Bulgaria rose + `БЪЛГАРИЯ` wordmark, single colour `#004F46`).

Rebuild any time with:

```bash
./venv/bin/python3 app-icon/_work/build_icons.py
```

The script is deterministic — no manual compositing in Figma/Illustrator required.

---

## Design decisions

### 1. Drop the wordmark, keep the rose

The source SVG is the full *brand-bar lockup*: rose symbol + `БЪЛГАРИЯ` Cyrillic wordmark + brushstroke underline. Wordmarks become illegible below ~60 pt — that's sub-optimal for iOS (minimum rendered 40 × 40 px in Settings) and broken on Android (`mdpi` 48 × 48 px). The rose is the distinctive element and carries the brand alone.

Rose isolation is done programmatically: the SVG is rasterised at 4096 px, the row where ink density collapses between the rose and the wordmark is detected, and the rose is cropped. A flood-fill step drops the small brushstroke descender + any stray specks so the silhouette is clean at every scale.

### 2. Colour inversion: teal background, white rose

The brand bar renders as a *teal rose on cream*. The **primary** app icon inverts this with a white fill: **white rose on deep teal** (`#FFFFFF` on a `#004F46`→`#003832` radial gradient).

Why: iOS home screens are a cluttered colour field. Light-on-dark icons read more strongly at thumb scale — see Apple Music, Threads, Apple Podcasts, Pinterest. And the product UI is cool neutrals (`#ffffff` cards, `#f4f6f7` pages) — so white gives a continuous vibe from icon into app. Cream would reintroduce a warm colour that appears nowhere else in the product.

Contrast: white on `#004F46` is **14.38 : 1**, exceeds WCAG AAA (7:1).

The **alt** (`master/alt-brand-faithful-1024.png`) is the brand-bar-faithful version: teal rose on cream background. Use if brand lockup fidelity takes priority (e.g. marketing surfaces co-branded with the logo).

### 3. Safe area sized for both platforms

Rose occupies **68%** of the master canvas edge. That clears:

- Apple's visual bounds guidance (≤ 80% to leave shadow ring + squircle-mask bite)
- Android's adaptive-icon safe circle (66dp of the 108dp canvas — 61%)

Android-specific foreground sits inside **60%** of the adaptive layer (tighter, because launcher masks can crop aggressively — teardrop, squircle, circle are all in the wild).

### 4. Subtle radial gradient on the background

Centre lighter (`#004F46`), edges darker (`#003832`). Adds depth without busy-ness, matches the glass/material treatment that iOS 18+ icons lean on. Flat on Android adaptive bg because adaptive masks clip unpredictably.

---

## File map

```
app-icon/
├── master/                                    Source-of-truth @1024 px
│   ├── primary-1024.png                       ← main icon (white rose on teal)
│   ├── alt-brand-faithful-1024.png            ← alt (teal rose on cream)
│   ├── rose-foreground-1024.png               transparent rose silhouette
│   └── rose-monochrome-1024.png               transparent rose (black, for tint layers)
│
├── ios/AppIcon.appiconset/                    Drop-in Xcode asset catalog
│   ├── icon-1024.png                          light (universal)
│   ├── icon-1024-dark.png                     dark appearance
│   ├── icon-1024-tinted.png                   tinted appearance (iOS 18+)
│   └── Contents.json                          asset-catalog manifest
│
├── android/                                   Drop-in `res/` folder
│   ├── mipmap-anydpi-v26/
│   │   ├── ic_launcher.xml                    adaptive icon (O+)
│   │   └── ic_launcher_round.xml
│   ├── mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/
│   │   ├── ic_launcher.png                    legacy pre-O fallback
│   │   └── ic_launcher_round.png              legacy round fallback
│   ├── mipmap-xxxhdpi/
│   │   ├── ic_launcher_foreground.png         adaptive foreground (white rose, α)
│   │   ├── ic_launcher_background.png         adaptive background (solid teal)
│   │   └── ic_launcher_monochrome.png         themed icon (Material You, Android 13+)
│   └── playstore-512.png                      Google Play Store listing asset
│
├── web/                                       Drop-in site-root assets
│   ├── favicon.ico                            multi-size (16+32+48) ICO
│   ├── favicon-{16,32,48,64}.png              individual favicons
│   ├── apple-touch-icon.png                   180px — iOS Add to Home Screen
│   ├── icon-{192,512}.png                     PWA standard icons
│   ├── icon-maskable-{192,512}.png            PWA maskable icons (Android adaptive)
│   ├── mstile-150.png                         Windows Start-menu tile
│   ├── og-image.png                           1200×630 Open Graph / Twitter / iMessage card
│   ├── site.webmanifest                       PWA manifest (JSON)
│   └── usage.html                             drop-in <head> snippet
│
└── preview/
    ├── home-screen-ios.png                    squircle mock with drop shadow
    ├── home-screen-android.png                squircle + circle mask mock
    └── size-grid.png                          icon at 180/120/87/60/40 px
```

---

## How to use

### iOS (Xcode)

1. Replace the empty `AppIcon` asset catalog in your project with `ios/AppIcon.appiconset/`.
2. Xcode generates all per-device renders from the single 1024 px source (this is the modern single-size approach introduced with Xcode 14).
3. In **App Icon & Launch Screen** build settings, confirm `Include all app icon assets` is off and `App Icon source` is `AppIcon`.

**iOS 26 / Liquid Glass**: Apple's new `Icon Composer` tool produces a layered `.icon` bundle for depth/specular treatment on the Liquid Glass home screen. For that, open `master/rose-foreground-1024.png` and `primary-1024.png` in Icon Composer, assign the rose to the foreground layer, the teal gradient to the background, and let the tool handle specular highlights. The PNGs in this set are the single-layer fallback Apple still accepts.

### Android (Android Studio)

1. Copy `android/mipmap-*` directories into `app/src/main/res/`.
2. Reference in `AndroidManifest.xml`:

   ```xml
   <application
       android:icon="@mipmap/ic_launcher"
       android:roundIcon="@mipmap/ic_launcher_round">
   ```

3. Themed icon (Material You, Android 13+) is wired in automatically via the `<monochrome>` element in `mipmap-anydpi-v26/ic_launcher.xml`. No additional app config needed.
4. Upload `playstore-512.png` as the **Hi-res icon** on the Play Console listing (512 × 512, 32-bit PNG, full-bleed — no transparency).

### React Native / Expo / Flutter

Use `master/primary-1024.png` as the single input:

- **Expo**: set `expo.icon` in `app.json`. Expo generates all targets from the 1024.
- **React Native CLI**: replace `ios/<App>/Images.xcassets/AppIcon.appiconset/` with the `ios/AppIcon.appiconset/` folder here, and drop `android/mipmap-*` into `android/app/src/main/res/`.
- **Flutter**: `flutter_launcher_icons` config — point `image_path` at `master/primary-1024.png` and `adaptive_icon_foreground` at `master/rose-foreground-1024.png`, `adaptive_icon_background` at `#004F46`.

---

## Compliance notes

- **Apple HIG**: 1024 × 1024 sRGB, opaque, no transparency, no Apple UI replicas, no text, safe area ≤ 80%. ✅
- **Android adaptive icon spec**: 108dp × 108dp foreground + 108dp × 108dp background, safe zone 66dp. ✅
- **Themed icon (Material You)**: monochrome layer at 108dp, single-colour with alpha. ✅
- **Play Store**: 512 × 512, 32-bit, opaque. ✅
- **Colour contrast**: white `#FFFFFF` on teal `#004F46` = **14.38 : 1**, exceeds WCAG AAA (7:1). Not a regulated surface for icons but reassuring for visibility on low-end panels.

---

## What this does *not* ship

- **`.icon` bundle** for Xcode 26 Icon Composer (Liquid Glass depth layering). The flat 1024 PNG set is the fallback Apple accepts, but the layered format renders richer on iOS 26. Follow-up task if targeting iOS 26 as minimum.
- **Notification and spotlight sized PNGs**. Modern Xcode generates these from the 1024 source; if targeting Xcode 13 or earlier, add the legacy size variants from the `master/primary-1024.png` (20/29/40/60/76/83.5 at @1/@2/@3).
- **Adaptive icon at non-xxxhdpi densities**. Not required — Android samples the `mipmap-xxxhdpi` adaptive layers for every density via the `anydpi-v26` alias. The legacy `ic_launcher.png` in each density bucket is the pre-O fallback.

---

## Colour reference

| Role | Hex | RGB | Usage |
|---|---|---|---|
| Logo teal (source) | `#004F46` | 0, 79, 70 | Adaptive bg, primary icon bg centre |
| Teal shadow | `#003832` | 0, 56, 50 | Radial gradient outer stop |
| Rose white | `#FFFFFF` | 255, 255, 255 | **Rose fill (primary icon)** · aligns with product UI `#ffffff` |
| Cream | `#F7EFE1` | 247, 239, 225 | Alt (brand-faithful) background only |
| Cream highlight | `#FDF7EB` | 253, 247, 235 | Alt bg radial centre |

The source logo uses `#004F46` — a darker forest-teal than the UI brand teal (`#00BBA7`, see `../../CLAUDE.md`). The logo colour is kept here for lockup fidelity; the UI teal is *not* used for the app icon. Cream appears only on the brand-faithful alt — it is not a product colour and does not appear anywhere in the app or website surfaces.

---

## Web / browser / PWA / social

`app-icon/web/` ships the full site-root asset set. Regenerate with:

```bash
./venv/bin/python3 app-icon/_work/build_web_icons.py
```

Deploy every file in `web/` to the site root, paste the snippet in `web/usage.html` into every page `<head>`, and you're covered for: browser tabs, bookmarks, iOS Safari home-screen pins, Android PWA installs (including maskable launcher icons), Windows Start-menu tiles, and Open Graph / Twitter / iMessage social previews.
