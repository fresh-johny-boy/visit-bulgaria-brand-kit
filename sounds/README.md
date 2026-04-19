# Visit Bulgaria — UI Sound Kit

31 original UI sounds, synthesised from scratch.

**Created by Kristian Kostadinov.** Licensed exclusively for use within the Visit Bulgaria mobile app, website, and Visit Bulgaria brand properties. Third-party use requires written permission. See [`LICENSE.md`](LICENSE.md) for full terms and contact details.

---

## Quick start

### Audition in a browser
Open `index.html` — clickable cards, grouped by category, with a "Play all in group" shortcut per section.

### Use a single sound
```html
<audio src="sounds/passport-stamp.wav" preload="auto"></audio>
```

```js
new Audio('sounds/passport-stamp.wav').play();
```

### Regenerate / tweak
All sounds are produced by `generate.py`. Edit the synthesis functions (they are ~3–8 lines each), then:
```
python3 generate.py
```
No dependencies — pure stdlib (`wave`, `math`, `struct`).

---

## The kit

| Category | Files | Best for |
|---|---|---|
| **Clicks** | `click-soft`, `click-sharp`, `click-deep`, `click-tick` | Every button tap. Start with `click-soft`. |
| **Confirms** | `confirm-pop`, `confirm-chime`, `confirm-bell`, `confirm-soft-tap` | Small positive actions. `confirm-soft-tap` is the recommended mark-visited sound. |
| **Success** | `success-short`, `success-arpeggio`, `success-big`, `login-success` | Save, complete, unlock. `login-success` after auth. |
| **Errors** | `error-minor`, `error-buzz`, `delete-thud`, `delete-sharp`, `warning` | Destructive actions, form errors. Use sparingly. |
| **Toggles** | `toggle-on`, `toggle-off`, `select`, `deselect` | Switches, multi-select, filter chips. |
| **Navigation** | `swoosh`, `swipe-soft`, `back`, `refresh` | Page transitions, pull-to-refresh, back gestures. |
| **Notifications** | `notify-gentle`, `notify-message`, `alert` | Incoming alerts. `notify-gentle` for non-urgent. |
| **Brand · travel** | `passport-stamp`, `day-complete`, `route-complete` | Unique to Visit Bulgaria. `passport-stamp` is the signature mark-visited sound. |

---

## Recommended mapping (Visit Bulgaria mobile app)

| Event | Sound | Why |
|---|---|---|
| Button tap (any) | `click-soft.wav` | Neutral, doesn't fatigue |
| Mark destination as visited | `passport-stamp.wav` | On-brand — it IS a travel stamp |
| Add to route | `confirm-soft-tap.wav` | Subtler — this is a small commit |
| Toast confirmation | `confirm-pop.wav` | Matches the "pop up" visual |
| Login success | `login-success.wav` | Sparkly, rewarding |
| Save changes | `success-short.wav` | Quick positive |
| Complete a day | `day-complete.wav` | Small fanfare |
| Complete full route | `route-complete.wav` | Bigger moment |
| Delete destination | `delete-thud.wav` | Decisive, low |
| Form error | `error-minor.wav` | Minor 2nd — noticeable, not harsh |
| Toggle switch on | `toggle-on.wav` | Upward |
| Toggle switch off | `toggle-off.wav` | Downward |
| Swipe between days | `swipe-soft.wav` | Very subtle |
| Pull-to-refresh completes | `refresh.wav` | Upward sweep |

---

## Technical specs

- **Format:** 16-bit PCM WAV
- **Sample rate:** 44.1kHz
- **Channels:** mono
- **Duration:** 40ms – 900ms depending on sound
- **Peak normalisation:** -0.4 dBFS (gentle headroom)
- **Combined size:** ~900KB for the full kit

All files are small enough to bundle directly in an app or preload for zero-latency playback.

---

## Pairing with haptics (iOS)

Sound alone is weaker than sound + haptic. Recommended pairings:

| Sound | Haptic |
|---|---|
| `click-soft` | `UIImpactFeedbackGenerator(style: .light)` |
| `confirm-soft-tap` | `UIImpactFeedbackGenerator(style: .medium)` |
| `passport-stamp` | `UIImpactFeedbackGenerator(style: .heavy)` + `.success` |
| `success-*` | `UINotificationFeedbackGenerator.notificationOccurred(.success)` |
| `error-*` / `delete-*` | `UINotificationFeedbackGenerator.notificationOccurred(.error)` |
| `warning` | `UINotificationFeedbackGenerator.notificationOccurred(.warning)` |

Android equivalents: `HapticFeedbackConstants.CONFIRM`, `REJECT`, `LONG_PRESS`.

---

## Licence

© 2026 **Kristian Kostadinov**. Licensed exclusively for Visit Bulgaria. Third-party use requires written permission — contact kristian@fasttrack-europe.com. Full terms: [`LICENSE.md`](LICENSE.md).
