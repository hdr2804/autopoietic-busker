#!/usr/bin/env python3
"""
"The Corner at Dawn" — an autopoietic street performance.

A self-playing system busks an original piece:
  - a fingerpicked guitar (Karplus-Strong plucked strings),
  - a generative melody that improvises over the chords (seeded random walk
    on the chord tones + pentatonic colour),
  - a soft root-note bass and foot-tap percussion (envelope-shaped noise /
    sine thumps — synthesis, not filters).

Rendered in ONE pass, dry: no EQ, no compression, no reverb, no audio
filters — only a noise gate at the render stage, as the bounty allows.
The seed fixes the composition; every run of this file performs it identically,
like a street musician who has settled on tonight's arrangement.
"""

import numpy as np
import wave, struct, sys

SR = 44100
SEED = 1455
rng = np.random.default_rng(SEED)

BPM = 92
BEAT = 60.0 / BPM
BAR = BEAT * 4

# ---------------------------------------------------------------- instruments
def ks_pluck(freq, dur, damp=0.996, bright=0.5, vel=1.0):
    """Karplus-Strong plucked string."""
    n = int(SR * dur)
    N = max(2, int(round(SR / freq)))
    buf = rng.uniform(-1, 1, N) * (0.4 + 0.6 * bright)
    out = np.zeros(n)
    idx = 0
    cur = buf.copy()
    for i in range(n):
        out[i] = cur[idx]
        nxt = cur[(idx + 1) % N]
        cur[idx] = damp * 0.5 * (cur[idx] + nxt)
        idx = (idx + 1) % N
    env = np.exp(-3.0 * np.arange(n) / n) * 0.3 + 0.7 * np.exp(-0.6 * np.arange(n) / n)
    return out * env * vel

def bass_note(freq, dur, vel=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2 * t)
    env = np.minimum(1.0, t * 30) * np.exp(-1.8 * t / dur)
    return tone * env * 0.5 * vel

def stomp(t_pos, vel=1.0):
    n = int(SR * 0.16)
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 22) + 45
    ph = np.cumsum(2 * np.pi * f / SR)
    return np.sin(ph) * np.exp(-t * 26) * 0.9 * vel

def shaker(t_pos, vel=1.0, dur=0.09):
    n = int(SR * dur)
    noise = rng.uniform(-1, 1, n)
    # one-pole downward sweep = hand-shaken beads (envelope shaping only)
    env = np.exp(-np.arange(n) / (n * 0.35)) * np.minimum(1.0, np.arange(n) / (n * 0.08))
    return noise * env * 0.16 * vel

# ---------------------------------------------------------------- composition
# Am(add9) – Fmaj7 – Cmaj7 – G6  (vi – IV – I – V), warm dawn progression
CHORDS = [
    dict(name="Am(add9)", root=110.00, tones=[220.00, 261.63, 329.63, 493.88], bass=55.00),
    dict(name="Fmaj7",    root=174.61, tones=[174.61, 220.00, 261.63, 329.63], bass=43.65),
    dict(name="Cmaj7",    root=130.81, tones=[196.00, 246.94, 329.63, 523.25], bass=32.70),
    dict(name="G6",       root=196.00, tones=[196.00, 246.94, 293.66, 329.63], bass=49.00),
]
PENTA = [220.00, 261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25]

track = []  # (start_sec, samples, pan, gain)

def add(start, samples, pan=0.0, gain=1.0):
    track.append((start, samples, pan, gain))

def arpeggio(bar_start, chord, pattern=(0, 1, 2, 3, 2, 1, 2, 3), vel=0.5):
    step = BEAT / 2
    for i, p in enumerate(pattern):
        f = chord["tones"][p % len(chord["tones"])]
        add(bar_start + i * step, ks_pluck(f, step * 2.2, vel=vel), pan=-0.08)

def strum(bar_start, chord, vel=0.55):
    for j, f in enumerate(chord["tones"]):
        add(bar_start + j * 0.012, ks_pluck(f, BAR * 0.95, damp=0.997, vel=vel), pan=0.06)

mel_state = {"deg": 4}

def improvise(bar_start, chord, density=0.8, register=1.0, vel=0.62):
    """Random-walk melody on chord tones + pentatonic colour, with rests."""
    steps = 8
    step = BEAT / 2
    pool = sorted(set([round(f, 2) for f in chord["tones"]] +
                      [round(f, 2) for f in PENTA if abs(f - chord["root"]) < 400]))
    for s in range(steps):
        if rng.random() > density:
            continue
        move = rng.choice([-2, -1, -1, 0, 1, 1, 2], p=[.08, .22, .22, .12, .22, .08, .06])
        mel_state["deg"] = int(np.clip(mel_state["deg"] + move, 0, len(pool) - 1))
        f = pool[mel_state["deg"]] * register
        dur = step * rng.choice([1, 1, 2], p=[.6, .25, .15])
        add(bar_start + s * step, ks_pluck(f, dur * 1.8, damp=0.9975, bright=0.65, vel=vel),
            pan=0.12)

def bassline(bar_start, chord, vel=0.8):
    add(bar_start, bass_note(chord["bass"] * 2, BEAT * 1.8, vel), pan=0.0)
    add(bar_start + BEAT * 2, bass_note(chord["bass"] * 2, BEAT * 1.6, vel * 0.85), pan=0.0)

def groove(bar_start, level=1.0):
    for b in range(4):
        if b % 2 == 0:
            add(bar_start + b * BEAT, stomp(0, 0.5 * level), pan=-0.05)
        for s in range(2):
            add(bar_start + b * BEAT + s * BEAT / 2, shaker(0, (0.7 if s else 1.0) * level), pan=0.15)

# ---------------------------------------------------------------- arrangement
# 4 sections x 4 bars (one chord per bar), BPM 92 -> ~42s per section cycle is
# too long; use 2 bars per chord pass: total 32 bars ~ 83s + outro.
t = 0.5  # lead-in silence like a musician settling on the corner

def section(bars, mode):
    global t
    for i in range(bars):
        ch = CHORDS[i % 4]
        if mode == "intro":
            arpeggio(t, ch, vel=0.5)
        elif mode == "theme":
            arpeggio(t, ch, vel=0.42)
            improvise(t, ch, density=0.75, vel=0.6)
            bassline(t, ch)
            groove(t, 0.8)
        elif mode == "variation":
            strum(t, ch, vel=0.4)
            arpeggio(t, ch, pattern=(3, 2, 1, 0, 1, 2, 3, 2), vel=0.35)
            improvise(t, ch, density=0.9, register=1.0, vel=0.66)
            bassline(t, ch)
            groove(t, 1.0)
        elif mode == "breakdown":
            arpeggio(t, ch, vel=0.46)
            improvise(t, ch, density=0.45, vel=0.55)
        t += BAR

section(4, "intro")       # alone on the corner
section(8, "theme")       # the tune arrives
section(8, "variation")   # showing off a little
section(4, "breakdown")   # hush — a passer-by stops
section(4, "theme")       # reprise for the small crowd

# outro: final Am(add9), let it ring
ch = CHORDS[0]
for j, f in enumerate(ch["tones"]):
    add(t + j * 0.02, ks_pluck(f, 4.5, damp=0.9985, vel=0.55), pan=0.0)
add(t, bass_note(ch["bass"] * 2, 4.0, 0.7), pan=0.0)
total = t + 5.0

# ---------------------------------------------------------------- render (dry)
n_total = int(SR * total)
mix_l = np.zeros(n_total)
mix_r = np.zeros(n_total)
for start, samples, pan, gain in track:
    i0 = int(start * SR)
    i1 = min(n_total, i0 + len(samples))
    if i1 <= i0:
        continue
    seg = samples[: i1 - i0] * gain
    mix_l[i0:i1] += seg * (1.0 - max(0.0, pan))
    mix_r[i0:i1] += seg * (1.0 + min(0.0, pan))

# noise gate only (allowed): silence anything under -52 dB, gentle knee
mono = np.maximum(np.abs(mix_l), np.abs(mix_r))
gate = np.clip((mono - 0.0025) / 0.01, 0.0, 1.0)
mix_l *= gate
mix_r *= gate

peak = max(np.max(np.abs(mix_l)), np.max(np.abs(mix_r)), 1e-9)
target = 0.89
mix_l *= target / peak
mix_r *= target / peak

stereo = np.stack([mix_l, mix_r], axis=1)
pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)

out = sys.argv[1] if len(sys.argv) > 1 else "corner-at-dawn.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"performed: {out}  duration={total:.1f}s  peak={peak:.3f} -> normalized {target}")
