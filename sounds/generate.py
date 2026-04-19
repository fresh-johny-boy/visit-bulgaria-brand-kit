#!/usr/bin/env python3
"""
Visit Bulgaria — UI Sound Kit generator.

Synthesises a full set of UI sounds using only Python stdlib (wave, math, struct).

© 2026 Kristian Kostadinov. All rights reserved.
Licensed exclusively for use within the Visit Bulgaria mobile app, website, and
official Visit Bulgaria brand properties. Third-party use requires written
permission — contact kristian@fasttrack-europe.com. Full terms: LICENSE.md.

Run:
    python3 generate.py

Output: 31 .wav files in the current directory.
"""
import wave, math, struct, os

SR = 44100  # sample rate
AMPLITUDE = 0.55  # headroom to avoid clipping when layered

# ─────────────────────────── helpers ───────────────────────────

def envelope(t, attack_rate=300, decay_rate=20):
    """Attack + exponential decay envelope (0..1)."""
    return (1.0 - math.exp(-attack_rate * t)) * math.exp(-decay_rate * t)

def tone(freq, t, attack=300, decay=20, harmonics=None):
    """Single tone with optional harmonic content."""
    env = envelope(t, attack, decay)
    s = math.sin(2 * math.pi * freq * t)
    if harmonics:
        for h, amp in harmonics:
            s += amp * math.sin(2 * math.pi * freq * h * t)
    return env * s

def noise_pulse(t, cutoff=100, decay=40):
    """Short noisy impulse (pseudo-click)."""
    import random
    random.seed(int(t * 1000000))
    env = envelope(t, 600, decay)
    # pseudo random from sine ratios (deterministic without numpy)
    n = math.sin(t * 99991.7) * math.sin(t * 77773.3) * math.sin(t * 55553.1)
    return env * n * 0.8

def glide(f_start, f_end, t, dur, attack=200, decay=10):
    """Pitch-glide tone over duration `dur`."""
    # linear glide in log-frequency space
    if t >= dur: return 0
    ratio = t / dur
    f = f_start * ((f_end / f_start) ** ratio)
    env = envelope(t, attack, decay)
    return env * math.sin(2 * math.pi * f * t)

def write_wav(name, samples, sr=SR):
    """Write float samples [-1, 1] to 16-bit PCM WAV."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    # Normalise and clip
    peak = max(abs(s) for s in samples) or 1
    scale = min(1.0, 0.95 / peak)
    with wave.open(path, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        frames = b''.join(
            struct.pack('<h', int(max(-1, min(1, s * scale)) * 32767))
            for s in samples
        )
        w.writeframes(frames)
    return path

def render(duration, fn):
    """Render a function fn(t) -> sample over `duration` seconds."""
    n = int(SR * duration)
    return [AMPLITUDE * fn(i / SR) for i in range(n)]

def layer(*arrays):
    """Mix equal-length sample arrays."""
    longest = max(len(a) for a in arrays)
    out = [0.0] * longest
    for a in arrays:
        for i, s in enumerate(a):
            out[i] += s
    return out

def pad(samples, duration):
    """Pad/truncate to fixed duration."""
    n = int(SR * duration)
    if len(samples) >= n: return samples[:n]
    return samples + [0.0] * (n - len(samples))

def offset(samples, delay_s):
    """Offset samples by delay_s seconds with silence before."""
    lead = [0.0] * int(SR * delay_s)
    return lead + samples

# ─────────────────────────── note frequencies ───────────────────────────
# Equal temperament, A4 = 440Hz
def note(semitones_from_a4):
    return 440.0 * (2 ** (semitones_from_a4 / 12))

C4 = note(-9);  D4 = note(-7);  E4 = note(-5);  F4 = note(-4)
G4 = note(-2);  A4 = note(0);   B4 = note(2)
C5 = note(3);   D5 = note(5);   E5 = note(7);   F5 = note(8)
G5 = note(10);  A5 = note(12);  B5 = note(14)
C6 = note(15);  E6 = note(19);  G6 = note(22)

# ────────────────────────────────────────────────────────────────────────
# 1. CLICKS — neutral, used for every button tap
# ────────────────────────────────────────────────────────────────────────

def s_click_soft():
    # Short mid-frequency click, clean
    return render(0.06, lambda t: tone(900, t, attack=500, decay=70,
                                       harmonics=[(2, 0.2)]))

def s_click_sharp():
    # Crisper, higher
    return render(0.05, lambda t: tone(1400, t, attack=600, decay=90,
                                       harmonics=[(2, 0.25), (3, 0.1)]))

def s_click_deep():
    # Lower, fuller — feels more physical
    return render(0.08, lambda t: tone(340, t, attack=400, decay=45,
                                       harmonics=[(2, 0.35), (3, 0.15)]))

def s_click_tick():
    # Very short, typing-key feel
    return render(0.04, lambda t: tone(2200, t, attack=800, decay=120))

# ────────────────────────────────────────────────────────────────────────
# 2. CONFIRMS — positive feedback on meaningful actions
# ────────────────────────────────────────────────────────────────────────

def s_confirm_pop():
    # Soft pop, medium length
    return render(0.15, lambda t: tone(880, t, attack=300, decay=22,
                                       harmonics=[(2, 0.3)]))

def s_confirm_chime():
    # Two-note ascending (C5 → G5)
    a = render(0.35, lambda t: tone(C5, t, attack=250, decay=7))
    b = offset(render(0.32, lambda t: tone(G5, t, attack=300, decay=10)), 0.06)
    return layer(a, pad(b, 0.4))

def s_confirm_soft_tap():
    # Subtle double-pluck for checkmarks
    a = render(0.12, lambda t: tone(G5, t, attack=500, decay=35))
    b = offset(render(0.12, lambda t: tone(C6, t, attack=500, decay=30)), 0.05)
    return layer(pad(a, 0.2), pad(b, 0.2))

# ────────────────────────────────────────────────────────────────────────
# 3. SUCCESS — bigger accomplishment (login, complete route, save)
# ────────────────────────────────────────────────────────────────────────

def s_success_arpeggio():
    # C major ascending: C5 E5 G5
    notes = [(C5, 0.0), (E5, 0.08), (G5, 0.16)]
    layers = []
    for f, dly in notes:
        layers.append(pad(offset(
            render(0.45, lambda t, f=f: tone(f, t, attack=300, decay=12)), dly), 0.6))
    return layer(*layers)

def s_success_short():
    # Two-note major 3rd — quick positive
    a = render(0.22, lambda t: tone(E5, t, attack=400, decay=18))
    b = offset(render(0.3, lambda t: tone(G5, t, attack=400, decay=14,
                                          harmonics=[(2, 0.2)])), 0.08)
    return layer(pad(a, 0.4), pad(b, 0.4))

def s_success_big():
    # 4-note triumphant: C E G C' — for big moments
    notes = [(C5, 0.0), (E5, 0.07), (G5, 0.14), (C6, 0.22)]
    layers = []
    for f, dly in notes:
        layers.append(pad(offset(
            render(0.5, lambda t, f=f: tone(f, t, attack=350, decay=10,
                                            harmonics=[(2, 0.25)])), dly), 0.75))
    return layer(*layers)

def s_login_success():
    # Sparkly unlock — higher register with slight bell
    notes = [(G5, 0.0), (C6, 0.05), (E6, 0.11)]
    layers = []
    for f, dly in notes:
        layers.append(pad(offset(render(0.4, lambda t, f=f:
            tone(f, t, attack=400, decay=15,
                 harmonics=[(2, 0.3), (3, 0.15)])), dly), 0.55))
    return layer(*layers)

# ────────────────────────────────────────────────────────────────────────
# 4. ERROR / DESTRUCTIVE — negative feedback
# ────────────────────────────────────────────────────────────────────────

def s_error_minor():
    # Minor 2nd dissonance (E5 + F5)
    a = render(0.3, lambda t: tone(E5, t, attack=400, decay=15))
    b = render(0.3, lambda t: tone(F5, t, attack=400, decay=15))
    return layer(a, b)

def s_error_buzz():
    # Short buzz — low detuned tone pair
    a = render(0.18, lambda t: tone(196, t, attack=500, decay=18))
    b = render(0.18, lambda t: tone(205, t, attack=500, decay=18))
    return layer(a, b)

def s_delete_thud():
    # Low decisive thud — feels like dropping
    return render(0.2, lambda t: tone(90, t, attack=800, decay=20,
                                      harmonics=[(2, 0.5), (3, 0.2)]))

def s_delete_sharp():
    # Downward pluck — quick negative
    return render(0.18, lambda t: glide(800, 200, t, 0.15,
                                        attack=500, decay=18))

def s_warning():
    # Attention tone — moderate pitch, sustain
    return render(0.35, lambda t: tone(660, t, attack=300, decay=8,
                                       harmonics=[(1.5, 0.3)]))

# ────────────────────────────────────────────────────────────────────────
# 5. TOGGLES / SELECTIONS
# ────────────────────────────────────────────────────────────────────────

def s_toggle_on():
    # Upward pluck
    return render(0.15, lambda t: glide(E5, A5, t, 0.1, attack=500, decay=25))

def s_toggle_off():
    # Downward pluck
    return render(0.15, lambda t: glide(A5, E5, t, 0.1, attack=500, decay=25))

def s_select():
    # Subtle upward pick
    return render(0.08, lambda t: tone(1200, t, attack=600, decay=50))

def s_deselect():
    # Subtle downward pick
    return render(0.08, lambda t: tone(600, t, attack=600, decay=50))

# ────────────────────────────────────────────────────────────────────────
# 6. NAVIGATION / TRANSITIONS
# ────────────────────────────────────────────────────────────────────────

def s_swoosh():
    # Glide sweep, feels like page transition
    return render(0.22, lambda t: glide(300, 1200, t, 0.2,
                                        attack=300, decay=8) * 0.6)

def s_swipe_soft():
    # Very subtle whoosh
    return render(0.15, lambda t: glide(200, 800, t, 0.13,
                                        attack=400, decay=12) * 0.4)

def s_back():
    # Descending — feels like retreat
    return render(0.18, lambda t: glide(800, 300, t, 0.15, attack=400, decay=12))

def s_refresh():
    # Quick upward sweep
    return render(0.2, lambda t: glide(400, 1000, t, 0.17, attack=400, decay=10))

# ────────────────────────────────────────────────────────────────────────
# 7. NOTIFICATIONS
# ────────────────────────────────────────────────────────────────────────

def s_notify_gentle():
    # Single soft tone
    return render(0.4, lambda t: tone(G5, t, attack=400, decay=6,
                                      harmonics=[(2, 0.2)]))

def s_notify_message():
    # Two-tone alert (D5 → F#5)
    a = render(0.3, lambda t: tone(D5, t, attack=350, decay=12))
    b = offset(render(0.35, lambda t: tone(note(6), t, attack=350, decay=10)), 0.1)
    return layer(pad(a, 0.45), pad(b, 0.45))

def s_alert():
    # Triple-tick for urgent but not alarming
    ticks = []
    for i in range(3):
        ticks.append(pad(offset(
            render(0.15, lambda t: tone(1000, t, attack=600, decay=40)),
            i * 0.08), 0.4))
    return layer(*ticks)

# ────────────────────────────────────────────────────────────────────────
# 8. BRAND — travel-themed for Visit Bulgaria
# ────────────────────────────────────────────────────────────────────────

def s_passport_stamp():
    # Low thud + paper-rustle noise + tiny chime tail
    # Main thud
    thud = render(0.18, lambda t: tone(110, t, attack=800, decay=22,
                                       harmonics=[(2, 0.5), (3, 0.2), (4, 0.1)]))
    # Higher component for "paper crunch"
    crunch = render(0.08, lambda t: noise_pulse(t, decay=50) * 0.6)
    # Tiny chime after ~150ms — "it's marked"
    chime = offset(render(0.2, lambda t: tone(E6, t, attack=400, decay=25,
                                              harmonics=[(2, 0.3)])), 0.14)
    return layer(pad(thud, 0.4), pad(crunch, 0.4), pad(chime, 0.4))

def s_day_complete():
    # Short fanfare: ascending 4th then resolve — a small reward
    notes = [(C5, 0.0), (F5, 0.08), (G5, 0.16), (C6, 0.22)]
    layers = []
    for f, dly in notes:
        layers.append(pad(offset(render(0.4, lambda t, f=f:
            tone(f, t, attack=300, decay=13,
                 harmonics=[(2, 0.2)])), dly), 0.65))
    return layer(*layers)

def s_route_complete():
    # Bigger moment — full ascending major scale fragment
    notes = [(C5, 0.0), (E5, 0.06), (G5, 0.12), (C6, 0.18), (E6, 0.26)]
    layers = []
    for f, dly in notes:
        layers.append(pad(offset(render(0.5, lambda t, f=f:
            tone(f, t, attack=400, decay=10,
                 harmonics=[(2, 0.3), (3, 0.1)])), dly), 0.85))
    return layer(*layers)

# ────────────────────────────────────────────────────────────────────────
# Registry & generate
# ────────────────────────────────────────────────────────────────────────

KIT = [
    # clicks
    ('clicks',     'click-soft.wav',       s_click_soft,        'Neutral button tap'),
    ('clicks',     'click-sharp.wav',      s_click_sharp,       'Crisp button tap'),
    ('clicks',     'click-deep.wav',       s_click_deep,        'Deep, physical tap'),
    ('clicks',     'click-tick.wav',       s_click_tick,        'Typing / key tick'),
    # confirms
    ('confirm',    'confirm-pop.wav',      s_confirm_pop,       'Soft pop confirmation'),
    ('confirm',    'confirm-chime.wav',    s_confirm_chime,     'Two-tone ascending chime'),
    ('confirm',    'confirm-soft-tap.wav', s_confirm_soft_tap,  'Double-pluck (good for mark-visited)'),
    # success
    ('success',    'success-short.wav',    s_success_short,     'Quick 2-note positive'),
    ('success',    'success-arpeggio.wav', s_success_arpeggio,  'C-E-G rising arpeggio'),
    ('success',    'success-big.wav',      s_success_big,       'Triumphant 4-note'),
    ('success',    'login-success.wav',    s_login_success,     'Sparkly unlock / login'),
    # errors / destructive
    ('error',      'error-minor.wav',      s_error_minor,       'Minor 2nd dissonance'),
    ('error',      'error-buzz.wav',       s_error_buzz,        'Short detuned buzz'),
    ('error',      'delete-thud.wav',      s_delete_thud,       'Low decisive delete'),
    ('error',      'delete-sharp.wav',     s_delete_sharp,      'Downward pluck delete'),
    ('error',      'warning.wav',          s_warning,           'Attention / warning tone'),
    # toggles / selection
    ('toggle',     'toggle-on.wav',        s_toggle_on,         'Upward pluck — toggle on'),
    ('toggle',     'toggle-off.wav',       s_toggle_off,        'Downward pluck — toggle off'),
    ('toggle',     'select.wav',           s_select,            'Subtle upward select'),
    ('toggle',     'deselect.wav',         s_deselect,          'Subtle downward deselect'),
    # navigation
    ('nav',        'swoosh.wav',           s_swoosh,            'Page transition whoosh'),
    ('nav',        'swipe-soft.wav',       s_swipe_soft,        'Subtle swipe'),
    ('nav',        'back.wav',             s_back,              'Descending back / close'),
    ('nav',        'refresh.wav',          s_refresh,           'Upward refresh sweep'),
    # notifications
    ('notify',     'notify-gentle.wav',    s_notify_gentle,     'Gentle single-tone notification'),
    ('notify',     'notify-message.wav',   s_notify_message,    'Two-tone message alert'),
    ('notify',     'alert.wav',            s_alert,             'Triple-tick alert'),
    # brand / travel
    ('brand',      'passport-stamp.wav',   s_passport_stamp,    'Travel-themed mark-visited'),
    ('brand',      'day-complete.wav',     s_day_complete,      'Day complete fanfare'),
    ('brand',      'route-complete.wav',   s_route_complete,    'Full route complete'),
]

def main():
    print(f'Generating {len(KIT)} sounds…')
    for group, name, fn, desc in KIT:
        samples = fn()
        path = write_wav(name, samples)
        size = os.path.getsize(path)
        print(f'  ✓ [{group:>8}] {name:<26} {size:>6} bytes   {desc}')
    print(f'\nDone. {len(KIT)} files written to {os.path.dirname(os.path.abspath(__file__))}')

if __name__ == '__main__':
    main()
