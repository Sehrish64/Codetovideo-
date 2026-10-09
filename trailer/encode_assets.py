"""Encode intro/outro/bell with SFX."""
import numpy as np, wave, os, subprocess

SR = 44100
TDIR = os.path.expanduser("~/workspace/imagine_media/ai-video-channel/trailer")
SFXD = os.path.expanduser("~/workspace/imagine_media/pixel-fighter/work/sfx")
OUTB = os.path.expanduser("~/workspace/imagine_media/ai-video-channel")

def load_wav(path):
    with wave.open(path, 'rb') as w:
        n = w.getnframes(); ch = w.getnchannels()
        a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    if ch == 2:
        a = a.reshape(-1, 2).mean(axis=1)
    return a, w.getframerate()

def save_wav(path, a):
    a = np.clip(a, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())

def place(track, sample, sr, at_s, gain=1.0):
    start = int(at_s * SR)
    if sr != SR:
        idx = (np.arange(int(len(sample) * SR / sr)) * sr / SR).astype(int)
        idx = np.clip(idx, 0, len(sample) - 1)
        sample = sample[idx]
    end = min(len(track), start + len(sample))
    track[start:end] += sample[:end - start] * gain

def riser(dur):
    n = int(SR * dur); t = np.arange(n) / SR
    return np.random.default_rng(9).standard_normal(n) * (t / dur) ** 2 * 0.3

def impact():
    n = int(SR * 0.6); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 60 * t) * np.exp(-t * 8) +
            np.random.default_rng(4).standard_normal(n) * np.exp(-t * 25) * 0.3) * 0.85

def shimmer():
    n = int(SR * 0.5); t = np.arange(n) / SR
    s = np.zeros(n)
    for f in [880, 1320, 1760]:
        s += np.sin(2 * np.pi * f * t) * np.exp(-t * 9)
    return s * 0.3

whoosh, wsr = load_wav(f"{SFXD}/whoosh.wav")
bell, bsr = load_wav(f"{SFXD}/bell.wav")
coin, csr = load_wav(f"{SFXD}/coin.wav")

def mix_video(frames_dir, sfx_events, out_path, dur):
    n = int(SR * dur)
    sfx = np.zeros(n, dtype=np.float32)
    for kind, at, gain in sfx_events:
        if kind == "riser": place(sfx, riser(1.2), SR, at, gain)
        elif kind == "impact": place(sfx, impact(), SR, at, gain)
        elif kind == "shimmer": place(sfx, shimmer(), SR, at, gain)
        elif kind == "whoosh": place(sfx, whoosh, wsr, at, gain)
        elif kind == "bell": place(sfx, bell, bsr, at, gain)
        elif kind == "coin": place(sfx, coin, csr, at, gain)
    stem = f"{TDIR}/stem_tmp.wav"
    save_wav(stem, sfx)
    fps = 30
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-framerate", str(fps), "-i", f"{frames_dir}/f%05d.png",
           "-i", stem,
           "-filter_complex",
           "[1:a]pan=stereo|c0=c0|c1=c0,apad=whole_dur={}[a]".format(dur),
           "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           "-r", str(fps), "-c:a", "aac", "-b:a", "160k",
           "-shortest", out_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(out_path, "rc:", r.returncode, r.stderr[-300:] if r.stderr else "")

# intro: riser 0.5-1.7, impact at morph 2.0, shimmer 2.1
mix_video(f"{TDIR}/frames_intro",
          [("riser", 0.5, 1.0), ("impact", 2.0, 0.9), ("shimmer", 2.15, 1.0)],
          f"{OUTB}/codetovideo-intro-bumper.mp4", 4.0)
# outro: whoosh 0.1, coin 1.2, bell 2.3, whoosh 2.8
mix_video(f"{TDIR}/frames_outro",
          [("whoosh", 0.1, 0.6), ("coin", 1.2, 0.5), ("bell", 2.3, 0.55),
           ("whoosh", 2.8, 0.5)],
          f"{OUTB}/codetovideo-outro.mp4", 7.0)
# bell: soft coin pop at in, soft bell at ring
n = int(SR * 3.5)
sfx = np.zeros(n, dtype=np.float32)
place(sfx, coin, csr, 0.15, 0.35)
place(sfx, bell, bsr, 0.7, 0.3)
save_wav(f"{TDIR}/stem_bell.wav", sfx)
# bell -> vp9 with alpha
cmd = ["ffmpeg", "-y", "-v", "error",
       "-framerate", "30", "-i", f"{TDIR}/frames_bell/f%05d.png",
       "-i", f"{TDIR}/stem_bell.wav",
       "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "2M",
       "-c:a", "libopus", "-shortest",
       f"{OUTB}/codetovideo-subscribe-bell.webm"]
r = subprocess.run(cmd, capture_output=True, text=True)
print("bell webm rc:", r.returncode, r.stderr[-300:] if r.stderr else "")
