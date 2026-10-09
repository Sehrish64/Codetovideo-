"""Synthesize + place SFX stems for the trailer, then mix with music."""
import numpy as np
import wave, os, subprocess

SR = 44100
DUR = 36.0
N = int(SR * DUR)
TDIR = os.path.expanduser("~/workspace/imagine_media/ai-video-channel/trailer")
SFXD = os.path.expanduser("~/workspace/imagine_media/pixel-fighter/work/sfx")
DCD = os.path.expanduser("~/workspace/imagine_media/dead-city-karachi/ep1/sfx")

def load_wav(path):
    with wave.open(path, 'rb') as w:
        n = w.getnframes(); ch = w.getnchannels(); sw = w.getsampwidth()
        raw = w.readframes(n)
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if ch == 2:
        a = a.reshape(-1, 2).mean(axis=1)
    return a, w.getframerate()

def save_wav(path, a, sr=SR):
    a = np.clip(a, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((a * 32767).astype(np.int16).tobytes())

def place(track, sample, sr, at_s, gain=1.0):
    start = int(at_s * SR)
    if sr != SR:
        # naive resample
        idx = (np.arange(int(len(sample) * SR / sr)) * sr / SR).astype(int)
        idx = np.clip(idx, 0, len(sample) - 1)
        sample = sample[idx]
    end = min(N, start + len(sample))
    track[start:end] += sample[:end - start] * gain

# --- synthesize tick ---
def tick():
    n = int(SR * 0.03)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 180) * 0.5

# --- synthesize impact boom ---
def impact():
    n = int(SR * 0.7)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 55 * t) * np.exp(-t * 7)
    noise = np.random.default_rng(3).standard_normal(n) * np.exp(-t * 22) * 0.35
    return (body + noise) * 0.9

# --- synthesize riser (noise sweep up) ---
def riser(dur=0.9):
    n = int(SR * dur)
    t = np.arange(n) / SR
    noise = np.random.default_rng(5).standard_normal(n)
    # amplitude ramp up
    env = (t / dur) ** 2
    return noise * env * 0.25

sfx = np.zeros(N, dtype=np.float32)

# typing ticks 0.8 -> 5.0
tk = tick()
tt = 0.8
while tt < 5.0:
    place(sfx, tk, SR, tt, gain=0.5)
    tt += 0.13

# riser into flash
place(sfx, riser(0.9), SR, 4.95, gain=1.0)
# impact at flash
place(sfx, impact(), SR, 5.8, gain=1.0)

# whooshes
whoosh, wsr = load_wav(f"{SFXD}/whoosh.wav")
for at in [9.0, 12.5, 15.5, 18.5, 29.0]:
    place(sfx, whoosh, wsr, at, gain=0.7)

# pops for montage + cards
coin, csr = load_wav(f"{SFXD}/coin.wav")
for at in [12.5, 15.5, 18.5, 21.5, 22.35, 23.2, 24.05]:
    place(sfx, coin, csr, at, gain=0.45)

# charge riser for logo
place(sfx, riser(1.8), SR, 25.1, gain=0.9)
place(sfx, impact(), SR, 27.0, gain=0.8)

# subscribe pop + bell
bell, bsr = load_wav(f"{SFXD}/bell.wav")
place(sfx, coin, csr, 31.9, gain=0.5)
place(sfx, bell, bsr, 32.1, gain=0.5)
place(sfx, impact(), SR, 35.2, gain=0.4)

save_wav(f"{TDIR}/sfx_stem.wav", sfx)
print("sfx stem done", sfx.max())

# --- mix: music + sfx with deterministic amerge recipe ---
# music: cipher 0-36s at 0.22, sfx at 1.0
cmd = [
    "ffmpeg", "-y", "-v", "error",
    "-i", f"{TDIR}/trailer_silent.mp4",
    "-i", f"{TDIR}/cipher.mp3",
    "-i", f"{TDIR}/sfx_stem.wav",
    "-filter_complex",
    "[1:a]atrim=0:36,asetpts=PTS-STARTPTS,pan=stereo|c0=c0|c1=c0,volume=0.35,apad=whole_dur=36[m];"
    "[2:a]pan=stereo|c0=c0|c1=c0,volume=1.0,apad=whole_dur=36[s];"
    "[m][s]amerge=inputs=2,"
    "pan=stereo|c0=c0+c2|c1=c1+c3,"
    "alimiter=limit=0.95[aout]",
    "-map", "0:v", "-map", "[aout]",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
    "-shortest",
    os.path.expanduser("~/workspace/imagine_media/ai-video-channel/codetovideo-trailer.mp4"),
]
r = subprocess.run(cmd, capture_output=True, text=True)
print("ffmpeg rc:", r.returncode)
if r.stderr:
    print(r.stderr[-800:])
