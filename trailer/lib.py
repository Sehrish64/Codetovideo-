"""Shared graphics utilities for CodeToVideo trailer + brand assets."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
FPS = 30

BG = (10, 10, 11)
VIOLET = (139, 92, 246)
VIOLET_DIM = (99, 60, 180)
WHITE = (255, 255, 255)
MUTED = (140, 140, 155)
CODE_BG = (14, 14, 18)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

_font_cache = {}
def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]

# ---------- easing ----------
def clamp01(x):
    return max(0.0, min(1.0, x))

def ease_out_cubic(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3

def ease_in_cubic(t):
    t = clamp01(t)
    return t ** 3

def ease_in_out(t):
    t = clamp01(t)
    return 3 * t * t - 2 * t * t * t

def spring(t, damping=6.0, freq=10.0):
    """Overshooting spring 0->1."""
    t = clamp01(t)
    return 1 - math.exp(-damping * t) * math.cos(freq * t)

def prog(frame, start_s, end_s):
    """Progress 0..1 of frame within [start_s, end_s)."""
    return clamp01((frame / FPS - start_s) / max(1e-6, (end_s - start_s)))

# ---------- canvas ----------
def canvas(alpha=False):
    if alpha:
        return Image.new("RGBA", (W, H), (0, 0, 0, 0))
    return Image.new("RGB", (W, H), BG)

def text_size(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1]

def draw_centered(draw, cx, y, s, f, fill, alpha=255):
    tw, th = text_size(draw, s, f)
    if len(fill) == 3:
        fill = fill + (alpha,)
    draw.text((cx - tw / 2, y), s, font=f, fill=fill)

def glow_text(base, cx, y, s, f, fill, glow_color=VIOLET, radius=18, alpha=160):
    """Draw glowing text: blurred copy underneath."""
    tw, th = text_size(ImageDraw.Draw(base), s, f)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((cx - tw / 2, y), s, font=f, fill=glow_color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(radius))
    out = Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")
    d2 = ImageDraw.Draw(out)
    d2.text((cx - tw / 2, y), s, font=f, fill=fill)
    return out

# ---------- particles ----------
class Particles:
    def __init__(self, n, seed=7):
        rng = np.random.default_rng(seed)
        self.n = n
        self.pos = np.zeros((n, 2))
        self.vel = np.zeros((n, 2))
        self.life = np.zeros(n)      # remaining
        self.maxlife = np.ones(n)
        self.size = np.zeros(n)
        self.hue = np.zeros(n)       # 0=violet, 1=white
        self.rng = rng

    def burst(self, cx, cy, count, speed_lo=120, speed_hi=700, life_lo=0.4,
              life_hi=1.4, size_lo=2, size_hi=7, violet_ratio=0.7):
        idx = np.where(self.life <= 0)[0][:count]
        if len(idx) == 0:
            return
        ang = self.rng.uniform(0, 2 * math.pi, len(idx))
        spd = self.rng.uniform(speed_lo, speed_hi, len(idx))
        self.pos[idx, 0] = cx
        self.pos[idx, 1] = cy
        self.vel[idx, 0] = np.cos(ang) * spd
        self.vel[idx, 1] = np.sin(ang) * spd
        self.maxlife[idx] = self.rng.uniform(life_lo, life_hi, len(idx))
        self.life[idx] = self.maxlife[idx]
        self.size[idx] = self.rng.uniform(size_lo, size_hi, len(idx))
        self.hue[idx] = (self.rng.uniform(0, 1, len(idx)) < violet_ratio).astype(float)

    def update(self, dt, gravity=0.0, drag=0.98):
        alive = self.life > 0
        self.vel[alive, 1] += gravity * dt
        self.vel[alive] *= drag
        self.pos[alive] += self.vel[alive] * dt
        self.life[alive] -= dt

    def draw(self, draw):
        alive = np.where(self.life > 0)[0]
        for i in alive:
            t = self.life[i] / max(1e-6, self.maxlife[i])
            a = int(255 * min(1.0, t * 1.6))
            col = VIOLET if self.hue[i] > 0.5 else WHITE
            x, y = self.pos[i]
            r = self.size[i] * (0.5 + 0.5 * t)
            if -20 < x < W + 20 and -20 < y < H + 20:
                draw.ellipse([x - r, y - r, x + r, y + r],
                             fill=col + (a,))

# ---------- code typing ----------
CODE_LINES = [
    ("// watch this become video", "comment"),
    ("export const Intro = () => {", "kw"),
    ("  const frame = useCurrentFrame();", "plain"),
    ("  const scale = spring({", "plain"),
    ("    frame, fps: 30, config: {", "plain"),
    ("      damping: 12, stiffness: 90,", "num"),
    ("    },", "plain"),
    ("  });", "plain"),
    ("  return (", "kw"),
    ('    <Title text="Hello, world"', "tag"),
    ("      scale={scale}", "attr"),
    ("      color=\"#8B5CF6\" />", "tag"),
    ("  );", "plain"),
    ("};", "kw"),
]

TOKEN_COLORS = {
    "comment": (110, 110, 125),
    "kw": (139, 92, 246),
    "plain": (235, 235, 245),
    "num": (255, 180, 90),
    "tag": (120, 200, 255),
    "attr": (150, 230, 170),
}

def render_code_frame(draw, chars_shown, x0=140, y0=300, line_h=52, font_size=34):
    f = font(FONT_MONO, font_size)
    fb = font(FONT_MONO_B, font_size)
    remaining = chars_shown
    y = y0
    for text, tok in CODE_LINES:
        col = TOKEN_COLORS[tok]
        ff = fb if tok in ("kw", "tag") else f
        if remaining >= len(text):
            draw.text((x0, y), text, font=ff, fill=col)
            remaining -= len(text)
        elif remaining > 0:
            draw.text((x0, y), text[:remaining], font=ff, fill=col)
            # cursor
            tw, _ = text_size(draw, text[:remaining], ff)
            draw.rectangle([x0 + tw + 4, y + 4, x0 + tw + 16, y + font_size + 2],
                           fill=VIOLET)
            remaining = 0
        y += line_h
        if remaining <= 0 and y > y0:
            # still draw cursor at end position if exactly consumed
            pass
    total = sum(len(t) for t, _ in CODE_LINES)
    if chars_shown >= total:
        # blinking cursor at end
        pass
    return total

def code_total_chars():
    return sum(len(t) for t, _ in CODE_LINES)
