"""Synthesize SFX stem for EP2 (48kHz stereo, 72s content timeline)."""
import numpy as np
from scipy.io import wavfile

SR = 48000
DUR = 72.0
N = int(SR * DUR)
rng = np.random.default_rng(99)

L = np.zeros(N, dtype=np.float64)
R = np.zeros(N, dtype=np.float64)

def place(stereo, t0):
    n = len(stereo[0])
    i0 = int(t0 * SR)
    i1 = min(N, i0 + n)
    if i1 <= i0:
        return
    L[i0:i1] += stereo[0][:i1 - i0]
    R[i0:i1] += stereo[1][:i1 - i0]

def mono(x, pan=0.0, gain=1.0):
    x = x * gain
    gl = np.cos((pan + 1) * np.pi / 4)
    gr = np.sin((pan + 1) * np.pi / 4)
    return np.stack([x * gl, x * gr])

def whoosh(dur=0.7, gain=0.5, up=True):
    n = int(SR * dur)
    noise = rng.standard_normal(n)
    # sweep filter via cumulative envelope on FFT-ish: simple lowpass sweep using moving average with varying window
    t = np.linspace(0, 1, n)
    # amplitude envelope: swell
    env = np.sin(np.pi * t) ** 1.5
    # crude sweep: modulate noise with rising sine for motion feel
    sweep = np.sin(2 * np.pi * (200 + 1800 * t) * t * dur)
    x = noise * 0.4 * env + sweep * 0.25 * env
    # fade edges
    x *= np.minimum(1, np.minimum(np.arange(n), np.arange(n)[::-1]) / (0.05 * SR)).clip(0, 1)
    return mono(x, gain=gain)

def hit(gain=0.7):
    n = int(SR * 0.5)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 70 * t) * np.exp(-t * 9)
    x += 0.4 * np.sin(2 * np.pi * 140 * t) * np.exp(-t * 14)
    return mono(x, gain=gain)

def pop(freq=740, gain=0.45, dur=0.14):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = freq * (1 + 0.35 * np.exp(-t * 30))
    ph = np.cumsum(2 * np.pi * f / SR)
    x = np.sin(ph) * np.exp(-t * 26)
    return mono(x, gain=gain)

def tick(gain=0.30):
    n = int(SR * 0.03)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 220)
    x += 0.5 * rng.standard_normal(n) * np.exp(-t * 300)
    return mono(x, gain=gain)

def beep(freq=880, gain=0.20, dur=0.18):
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t) * np.exp(-t * 12)
    return mono(x, gain=gain)

def riser(dur=2.0, gain=0.35):
    n = int(SR * dur)
    t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n) * 0.3
    tone = np.sin(2 * np.pi * (150 + 900 * t) * t * dur) * 0.2
    x = (noise + tone) * (t ** 2)
    return mono(x, gain=gain)

def shimmer(gain=0.3):
    n = int(SR * 0.9)
    out = np.zeros(n)
    for k, fq in enumerate([1046, 1318, 1568, 2093]):
        st = int(k * 0.09 * SR)
        m = int(0.35 * SR)
        t = np.arange(m) / SR
        out[st:st + m] += np.sin(2 * np.pi * fq * t) * np.exp(-t * 8) * 0.5
    return mono(out, gain=gain)

def wind(dur=12.0, gain=0.10):
    n = int(SR * dur)
    noise = rng.standard_normal(n)
    # lowpass via FFT
    F = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(n, 1 / SR)
    F *= 1 / (1 + (freqs / 300) ** 2)
    x = np.fft.irfft(F, n)
    x /= max(1e-6, np.abs(x).max())
    # slow swells
    t = np.arange(n) / SR
    x *= (0.6 + 0.4 * np.sin(2 * np.pi * 0.15 * t))
    # fades
    fd = int(1.5 * SR)
    x[:fd] *= np.linspace(0, 1, fd)
    x[-fd:] *= np.linspace(1, 0, fd)
    return mono(x, gain=gain)

# ---- timeline (content-local seconds) ----
place(whoosh(), 0.0)
place(riser(), 6.0)
place(whoosh(gain=0.6), 8.0)
place(hit(), 8.05)
place(wind(), 8.0)                       # exterior ambience
for k in range(6):                        # beacon beeps
    place(beep(), 9.0 + k * 2.0)
place(whoosh(), 20.0)                     # -> control room
place(hit(0.5), 20.05)
for k in range(40):                       # teletype ticks ct 21-31
    place(tick(), 21.0 + k * 0.26)
place(whoosh(), 34.0)                     # -> VS
place(hit(), 34.05)
for k in range(4):                        # VS row pops
    place(pop(740 + k * 90), 35.2 + k * 1.6)
place(whoosh(), 46.0)                     # -> terminal
for k in range(26):                       # terminal typing ticks
    place(tick(0.26), 47.0 + k * 0.22)
place(pop(880, 0.5), 52.6)                # "0 credits" punch
place(hit(0.55), 52.6)
place(whoosh(), 56.0)                     # -> flowchart
for k in range(5):                        # step pops
    place(pop(660 + k * 110, 0.5), 56.5 + k * 1.1)
place(whoosh(gain=0.6), 66.0)             # -> CTA
place(shimmer(), 66.1)
place(pop(990, 0.5), 68.6)                # subscribe pill

# soft limiter
mx = max(np.abs(L).max(), np.abs(R).max(), 1e-6)
if mx > 0.95:
    L *= 0.95 / mx
    R *= 0.95 / mx
stereo = np.stack([L, R], axis=1)
wavfile.write("sfx_stem.wav", SR, (np.clip(stereo, -1, 1) * 32767).astype(np.int16))
print("sfx_stem.wav written", DUR, "s")
