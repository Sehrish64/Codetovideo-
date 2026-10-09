"""CodeToVideo brand overlays: like (3s) + comment (3s), ProRes 4444 alpha.
Matches the subscribe-bell overlay family: lower-right pill, slide in/hold/out,
violet icon + white text, soft coin pop SFX."""
import math, os, sys, subprocess
import numpy as np, wave
sys.path.insert(0, os.path.dirname(__file__))
from lib import *
from PIL import Image, ImageDraw

BASE = os.path.expanduser("~/workspace/imagine_media/ai-video-channel")
TDIR = os.path.join(BASE, "trailer")
SFXD = os.path.expanduser("~/workspace/imagine_media/pixel-fighter/work/sfx")

PW, PH = 560, 130
DUR = 3.0

def load_wav(path):
    with wave.open(path, 'rb') as w:
        n = w.getnframes(); ch = w.getnchannels()
        a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    if ch == 2:
        a = a.reshape(-1, 2).mean(axis=1)
    return a, w.getframerate()

def save_wav(path, a, sr=44100):
    a = np.clip(a, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((a * 32767).astype(np.int16).tobytes())

def place(track, sample, sr, at_s, gain=1.0, SR=44100):
    start = int(at_s * SR)
    if sr != SR:
        idx = (np.arange(int(len(sample) * SR / sr)) * sr / SR).astype(int)
        idx = np.clip(idx, 0, len(sample) - 1)
        sample = sample[idx]
    end = min(len(track), start + len(sample))
    track[start:end] += sample[:end - start] * gain

# ---------- pill chrome (shared) ----------
def pill_geometry(t):
    if t < 0.5:
        xp = ease_out_cubic(t / 0.5)
    elif t < 2.1:
        xp = 1.0
    else:
        xp = 1 - ease_in_cubic((t - 2.1) / 0.9)
    tx = W - PW - 120
    x0 = tx + (1 - xp) * (PW + 300)
    y0 = H - PH - 140
    a = int(235 * min(1, xp * 1.5))
    return x0, y0, a

def draw_pill(d, x0, y0, a):
    d.rounded_rectangle([x0, y0, x0 + PW, y0 + PH], radius=PH // 2,
                        fill=(16, 16, 22, a))
    d.rounded_rectangle([x0, y0, x0 + PW, y0 + PH], radius=PH // 2,
                        outline=VIOLET + (a,), width=3)

def draw_label(d, x0, y0, a, text):
    d.text((x0 + 130, y0 + PH / 2 - 26), text, font=font(FONT_BOLD, 52),
           fill=WHITE + (a,))

# ---------- icons ----------
def draw_thumb(d, bx, by, s, a):
    """Thumbs-up, violet, scaled by s around (bx,by)."""
    def X(v): return bx + v * s
    def Y(v): return by + v * s
    # fist
    d.rounded_rectangle([X(-8), Y(-8), X(46), Y(36)], radius=int(12 * s),
                        fill=VIOLET + (a,))
    # thumb (vertical bar, rounded)
    d.rounded_rectangle([X(-14), Y(-50), X(6), Y(10)], radius=int(9 * s),
                        fill=VIOLET + (a,))
    # finger separator lines (pill-bg color)
    for yy in (2, 12, 22):
        d.line([(X(8), Y(yy)), (X(40), Y(yy))],
               fill=(16, 16, 22, a), width=max(2, int(3 * s)))

def draw_bubble(d, bx, by, s, a):
    """Speech bubble, violet outline + tail, scaled by s around (bx,by)."""
    def X(v): return bx + v * s
    def Y(v): return by + v * s
    w = max(2, int(6 * s))
    d.rounded_rectangle([X(-32), Y(-30), X(32), Y(12)], radius=int(16 * s),
                        outline=VIOLET + (a,), width=w)
    # tail
    d.polygon([(X(-20), Y(8)), (X(-24), Y(32)), (X(2), Y(8))],
              fill=VIOLET + (a,))

def icon_scale(i, t):
    """Base 1.0; smooth bump 0.6->1.1s, then gentle pulse 1.3->1.9s."""
    s = 1.0
    if 0.6 <= t <= 1.1:
        s += 0.25 * math.sin(math.pi * (t - 0.6) / 0.5)
    if 1.3 < t < 1.9:
        s *= 1 + 0.06 * math.sin((t - 1.3) * 12) * (1 - (t - 1.3) / 0.6)
    return s

# ---------- overlays ----------
def render_overlay(kind):
    frames = []
    N = int(DUR * FPS)
    for i in range(N):
        t = i / FPS
        img = canvas(alpha=True); d = ImageDraw.Draw(img, "RGBA")
        x0, y0, a = pill_geometry(t)
        draw_pill(d, x0, y0, a)
        bx, by = x0 + 75, y0 + PH / 2
        s = icon_scale(i, t)
        if kind == "like":
            draw_thumb(d, bx, by, s, a)
            draw_label(d, x0, y0, a, "Like")
        else:
            draw_bubble(d, bx, by, s, a)
            draw_label(d, x0, y0, a, "Comment")
        frames.append(img)
    return frames

def save_frames(frames, subdir):
    out = os.path.join(TDIR, subdir)
    os.makedirs(out, exist_ok=True)
    for i, img in enumerate(frames):
        img.save(f"{out}/f{i:05d}.png")
    print(subdir, len(frames), "frames")

def encode(frames_dir, label):
    coin, csr = load_wav(f"{SFXD}/coin.wav")
    SR = 44100
    n = int(SR * DUR)
    sfx = np.zeros(n, dtype=np.float32)
    place(sfx, coin, csr, 0.15, 0.35)   # soft pop on slide-in (same as bell)
    stem = f"{TDIR}/stem_{label}.wav"
    save_wav(stem, sfx, SR)
    out = f"{BASE}/codetovideo-{label}-overlay.mov"
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-framerate", "30", "-i", f"{frames_dir}/f%05d.png",
           "-i", stem,
           "-filter_complex",
           "[1:a]pan=stereo|c0=c0|c1=c0,apad=whole_dur={}[a]".format(DUR),
           "-map", "0:v", "-map", "[a]",
           "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p12le",
           "-c:a", "pcm_s16le", "-r", "30", "-shortest", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(out, "rc:", r.returncode, r.stderr[-400:] if r.stderr else "")
    return out

if __name__ == "__main__":
    for kind, label in (("like", "like"), ("comment", "comment")):
        subdir = f"frames_{label}"
        save_frames(render_overlay(kind), subdir)
        encode(os.path.join(TDIR, subdir), label)
    print("OVERLAYS DONE")
