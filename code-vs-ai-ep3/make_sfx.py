"""Synthesize SFX stem for EP3 (48kHz stereo, 62s content timeline)."""
import numpy as np
from scipy.io import wavfile

SR = 48000
DUR = 62.0
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
    t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t) ** 1.5
    sweep = np.sin(2 * np.pi * (200 + 1800 * t) * t * dur)
    x = noise * 0.4 * env + sweep * 0.25 * env
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
    t = np.arange(n) / SR
    x = (np.sin(2*np.pi*1320*t) + 0.6*np.sin(2*np.pi*1980*t)) * np.exp(-t*4) * 0.4
    return mono(x, gain=gain)

def wind(dur, gain=0.10):
    n = int(SR * dur)
    noise = rng.standard_normal(n)
    # lowpass via moving average
    k = 400
    kernel = np.ones(k) / k
    x = np.convolve(noise, kernel, mode='same')
    # slow gusts
    t = np.arange(n) / SR
    gust = 0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * t + 1.0)
    x = x * gust * gain * 8
    # fade in/out
    fade = min(int(2*SR), n//4)
    x[:fade] *= np.linspace(0, 1, fade)
    x[-fade:] *= np.linspace(1, 0, fade)
    return mono(x, pan=0.0)

def footstep(gain=0.35):
    n = int(SR * 0.16)
    t = np.arange(n) / SR
    x = np.sin(2*np.pi*95*t) * np.exp(-t*28)
    x += 0.5 * rng.standard_normal(n) * np.exp(-t*60) * 0.4
    return mono(x, gain=gain, pan=rng.uniform(-0.2, 0.2))

def hum(dur, gain=0.12, freq=58.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = np.sin(2*np.pi*freq*t) * 0.6 + np.sin(2*np.pi*freq*2*t) * 0.25
    x *= gain
    fade = int(0.5*SR)
    x[:fade] *= np.linspace(0, 1, fade)
    x[-fade:] *= np.linspace(1, 0, fade)
    return mono(x)

# ---------- timeline ----------
# HOOK pops
for tt in [0.3, 1.1, 2.8, 4.0]:
    place(pop(660 + tt*40, 0.4), tt)
place(whoosh(1.2, 0.35), 2.6)
place(shimmer(0.25), 4.2)

# SCENE: wind bed 8-30
place(wind(22.0, 0.10), 8.0)
# footsteps during walk 8.3-19.5 (every 0.7s)
ft = 8.3
while ft < 19.5:
    place(footstep(0.30), ft)
    ft += 0.7
# searchlight sweep 20-25
place(riser(2.5, 0.30), 19.8)
place(hum(6.0, 0.12), 20.0)
place(whoosh(1.0, 0.4), 24.5)   # lock-on
place(hit(0.5), 25.2)
# signal rings 26-30
for i, tt in enumerate([26.0, 26.55, 27.1, 27.65]):
    place(beep(880, 0.18), tt)
    place(whoosh(0.8, 0.30), tt)

# VS rows
for i, tt in enumerate([31.0, 31.9, 32.8, 40.0, 40.9, 41.8]):
    place(pop(740 if i < 3 else 880, 0.4), tt)
place(hit(0.6), 30.4)  # VS badge

# TERM typing
tt = 42.7
while tt < 44.5:
    place(tick(0.25), tt)
    tt += 0.09
place(shimmer(0.25), 49.5)   # progress done
place(pop(990, 0.4), 50.6)   # "0 credits" reveal

# CTA
place(pop(780, 0.45), 56.2)  # github pill
place(whoosh(1.0, 0.3), 60.5)
place(hit(0.45), 61.2)

# normalize to avoid clipping, keep headroom
peak = max(np.abs(L).max(), np.abs(R).max())
if peak > 0.89:
    g = 0.89 / peak
    L *= g; R *= g
stereo = np.stack([L, R], axis=1)
wavfile.write("sfx_stem.wav", SR, (np.clip(stereo, -1, 1) * 32767).astype(np.int16))
print("sfx stem written, peak %.3f" % max(np.abs(L).max(), np.abs(R).max()))
