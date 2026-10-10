"""SFX synthesis for Code vs AI EP1 v2. Total main = 60s @30fps."""
import numpy as np, os
from scipy.io import wavfile

OUT = os.path.expanduser("~/workspace/imagine_media/ai-video-channel/code-vs-ai")
SR = 44100
TOTAL = 60.0
N = int(SR * TOTAL)
sfx = np.zeros(N, dtype=np.float64)
rng = np.random.default_rng(42)

def add(seg, start_s, gain=1.0):
    i0 = int(start_s * SR)
    i1 = min(N, i0 + len(seg))
    if i0 < N:
        sfx[i0:i1] += seg[:i1-i0] * gain

def whoosh(dur=0.7, f_lo=200, f_hi=2400):
    n = int(SR*dur); t = np.arange(n)/SR
    noise = rng.standard_normal(n)
    sweep = np.linspace(f_lo, f_hi, n) / (SR/2)
    phase = np.cumsum(sweep) * 2*np.pi / 8
    env = np.sin(np.pi * t/dur)**2
    return (noise*0.4 + np.sin(phase)*0.6) * env

def impact(dur=0.9):
    n = int(SR*dur); t = np.arange(n)/SR
    boom = np.sin(2*np.pi*55*t) * np.exp(-t*5)
    crack = rng.standard_normal(n) * np.exp(-t*22) * 0.5
    return (boom + crack) * np.minimum(1, t*40)

def riser(dur=1.6):
    n = int(SR*dur); t = np.arange(n)/SR
    f = 150 * (2400/150)**(t/dur)
    phase = np.cumsum(f/SR*2*np.pi)
    env = (t/dur)**2
    return np.sin(phase)*env*0.5 + rng.standard_normal(n)*env*0.12

def pop(freq=880, dur=0.18):
    n = int(SR*dur); t = np.arange(n)/SR
    return np.sin(2*np.pi*freq*t)*np.exp(-t*18)

def tick(dur=0.05, freq=2200):
    n = int(SR*dur); t = np.arange(n)/SR
    return np.sin(2*np.pi*freq*t)*np.exp(-t*60)*0.6

def ding():
    n = int(SR*1.2); t = np.arange(n)/SR
    return (np.sin(2*np.pi*1318*t)*0.5 + np.sin(2*np.pi*1975*t)*0.25)*np.exp(-t*3)

# beat 1 hook: punch at ~3s
add(whoosh(0.8), 2.9, 0.5)
# beat 2 reveal (8-24): riser in, impact, caption whoosh at 18.5
add(riser(1.8), 7.6, 0.55)
add(impact(1.0), 9.2, 0.7)
add(whoosh(0.6), 18.5, 0.35)
# beat 3 split (24-38): VS impact + row pops
add(impact(0.8), 24.2, 0.5)
for i, ts in enumerate([26.0, 27.2, 28.4, 26.6, 27.8, 29.0, 30.2]):
    add(pop(760+i*60, 0.2), ts, 0.5)
# beat 4 terminal (38-52): typing ticks, done pop+ding
for k in range(28):
    add(tick(0.05, 2000+rng.uniform(-300,300)), 38.5+k*0.07, 0.35)
add(pop(990, 0.25), 47.5, 0.55)
add(ding(), 50.0, 0.4)
# beat 5 CTA (52-60): whoosh + ding
add(whoosh(0.7), 52.5, 0.4)
add(ding(), 56.5, 0.45)

peak = np.max(np.abs(sfx))
sfx = sfx / max(peak, 1e-6) * 0.89
wavfile.write(OUT+"/sfx_stem.wav", SR, (sfx*32767).astype(np.int16))
print("sfx v2 written")
