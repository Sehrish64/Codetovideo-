"""CodeToVideo — Code vs AI EP2: 80s anime snowy radio station, pure code.
Renders content frames (72s @30fps = 2160 frames). Bumpers added at assembly.
Scenes (content-local seconds):
  0-8   HOOK      kinetic text
  8-20  EXTERIOR  snowy radio tower, 80s anime night
  20-34 CONTROL   control room: teletype, VU meters, scope
  34-46 VS        AI MODEL vs PURE CODE split
  46-56 TERMINAL  $ python render.py proof
  56-66 FLOW      5-step flowchart
  66-72 CTA       GitHub + Friday
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, "/home/hatch/workspace/imagine_media/ai-video-channel/trailer")
from lib import (W, H, FPS, BG, VIOLET, WHITE, MUTED, canvas, font, text_size,
                 draw_centered, glow_text, clamp01, ease_out_cubic, ease_in_out,
                 spring, prog, FONT_BOLD, FONT_REG, FONT_MONO, FONT_MONO_B)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
os.makedirs(OUT, exist_ok=True)

GREEN = (80, 255, 140)
GREEN_DIM = (30, 120, 70)
RED = (255, 90, 90)
AMBER = (255, 190, 80)
PANEL = (16, 16, 22)

def vgrad(h, top, bottom):
    top = np.array(top, dtype=np.float32); bottom = np.array(bottom, dtype=np.float32)
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    return (top[None, None, :] * (1 - t) + bottom[None, None, :] * t).astype(np.uint8)

# ---------- vignette (precomputed) ----------
def make_vignette(strength=0.35):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H / 2
    d = np.sqrt(((xx - cx) / (W / 2)) ** 2 + ((yy - cy) / (H / 2)) ** 2) / math.sqrt(2)
    v = (1 - strength * np.clip(d, 0, 1) ** 1.6)
    return (v * 255).astype(np.uint8)

VIGNETTE = make_vignette()

def apply_vignette(img):
    a = np.asarray(img).astype(np.float32)
    v = (VIGNETTE / 255.0)[..., None]
    return Image.fromarray((a * v).astype(np.uint8))

# ================= HOOK (0-8) =================
def hook_frame(f, t):
    img = canvas().convert("RGBA")
    d = ImageDraw.Draw(img)
    # faint drifting violet particles bg
    rng = np.random.default_rng(11)
    px = rng.uniform(0, W, 70); py = rng.uniform(0, H, 70)
    for i in range(70):
        x = (px[i] + t * 12 * (0.3 + 0.7 * ((i % 5) / 5))) % W
        y = (py[i] - t * 8) % H
        a = int(40 + 40 * math.sin(t * 2 + i))
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=VIOLET + (max(0, a),))
    img = img.convert("RGBA")
    # lines appear staggered with spring pop
    lines = [
        (0.3, 2.2, "Everyone's using AI", 64, WHITE, False),
        (1.2, 3.0, "to make video.", 64, WHITE, False),
        (2.6, 5.2, "Watch what PURE CODE", 88, VIOLET, True),
        (3.8, 6.4, "can do.", 88, WHITE, False),
    ]
    y = 300
    for t0, t1, s, size, col, glow in lines:
        if t >= t0:
            p = spring((t - t0) / 0.5)
            fnt = font(FONT_BOLD, size)
            tw, th = text_size(ImageDraw.Draw(img), s, fnt)
            sc = 0.6 + 0.4 * p
            # draw scaled via temp layer for pop effect
            tmp = Image.new("RGBA", (tw + 80, th + 80), (0, 0, 0, 0))
            td = ImageDraw.Draw(tmp)
            td.text((40, 40), s, font=fnt, fill=col + (255,))
            nw, nh = int(tmp.width * sc), int(tmp.height * sc)
            tmp = tmp.resize((max(1, nw), max(1, nh)), Image.LANCZOS)
            alpha = int(255 * clamp01((t - t0) / 0.25))
            if glow:
                gl = Image.new("RGBA", tmp.size, (0, 0, 0, 0))
                gd = ImageDraw.Draw(gl)
                gd.text((40 * sc, 40 * sc), s, font=fnt, fill=VIOLET + (110,))
                gl = gl.filter(ImageFilter.GaussianBlur(14))
                img.alpha_composite(gl, (int(W / 2 - nw / 2), int(y - 40 * sc)))
            ta = tmp.copy()
            # fade in
            pxa = np.array(ta); pxa[..., 3] = (pxa[..., 3].astype(np.float32) * alpha / 255).astype(np.uint8)
            ta = Image.fromarray(pxa)
            img.alpha_composite(ta, (int(W / 2 - nw / 2), int(y - 40 * sc)))
            y += int((th + 26) * (0.7 + 0.3 * p))
        else:
            y += 90
    return apply_vignette(img.convert("RGB"))

# ================= EXTERIOR (8-20): radio tower =================
def build_exterior_bg():
    img = Image.new("RGB", (W, H))
    px = np.asarray(img).astype(np.float32)
    # sky gradient: deep indigo -> dark teal horizon
    sky = vgrad(H, (8, 8, 26), (16, 30, 52))
    px[:] = sky
    img = Image.fromarray(px.astype(np.uint8))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(42)
    # 80s magenta-cyan aurora band
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    for i in range(6):
        yy = 150 + i * 26
        bd.line([(0, yy), (W, yy + 40)], fill=(190, 60, 160, 26), width=18)
        bd.line([(0, yy + 90), (W, yy + 130)], fill=(60, 200, 220, 18), width=14)
    band = band.filter(ImageFilter.GaussianBlur(30))
    img = Image.alpha_composite(img.convert("RGBA"), band).convert("RGB")
    d = ImageDraw.Draw(img)
    # stars
    sx = rng.uniform(0, W, 260); sy = rng.uniform(0, 560, 260)
    for i in range(260):
        b = int(120 + 120 * rng.uniform())
        d.ellipse([sx[i] - 1.5, sy[i] - 1.5, sx[i] + 1.5, sy[i] + 1.5], fill=(b, b, b + 20))
    # moon with glow
    mx, my, mr = 1560, 210, 90
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([mx - mr - 60, my - mr - 60, mx + mr + 60, my + mr + 60], fill=(220, 230, 255, 40))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    d = ImageDraw.Draw(img)
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(235, 240, 250))
    d.ellipse([mx - mr + 30, my - mr + 18, mx - mr + 70, my - mr + 58], fill=(215, 222, 238))
    # far mountains
    mpts = [(0, 700)]
    for i, x in enumerate(range(0, W + 100, 100)):
        mpts.append((x, 620 - abs(math.sin(i * 1.7)) * 150 - rng.uniform(0, 40)))
    mpts.append((W, 700))
    d.polygon(mpts, fill=(14, 20, 40))
    # snow ground
    g = vgrad(H - 700, (36, 52, 84), (70, 92, 128))
    ground = Image.fromarray(np.repeat(g, W, axis=1) if g.shape[1] == 1 else g)
    img.paste(ground, (0, 700))
    d = ImageDraw.Draw(img)
    # ground sparkles
    for i in range(120):
        x = rng.uniform(60, W - 60); y = rng.uniform(720, H - 20)
        b = int(150 + 90 * rng.uniform())
        d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(b, b + 10, b + 30))
    # radio tower silhouette (center-left)
    tx = 640
    d.polygon([(tx - 90, 760), (tx + 90, 760), (tx + 26, 300), (tx - 26, 300)], fill=(10, 12, 20))
    # lattice braces
    for yy in range(320, 740, 44):
        wfrac = (yy - 300) / 460
        hw = 26 + wfrac * 64
        d.line([(tx - hw, yy), (tx + hw, yy)], fill=(24, 28, 44), width=5)
        d.line([(tx - hw, yy), (tx + hw, yy + 44)], fill=(20, 24, 38), width=4)
        d.line([(tx + hw, yy), (tx - hw, yy + 44)], fill=(20, 24, 38), width=4)
    # antenna mast + dish
    d.line([(tx, 300), (tx, 190)], fill=(10, 12, 20), width=10)
    d.ellipse([tx - 46, 330, tx + 46, 400], outline=(30, 36, 56), width=7)  # dish
    # small hut
    d.rectangle([tx + 150, 660, tx + 330, 760], fill=(12, 14, 24))
    d.polygon([(tx + 140, 660), (tx + 240, 610), (tx + 340, 660)], fill=(18, 22, 36))
    d.rectangle([tx + 220, 690, tx + 260, 730], fill=(255, 190, 80, 200))  # lit window
    return img

EXT_BG = build_exterior_bg()
# tower beacon position
BX, BY = 640, 186

class Snow:
    def __init__(self, n=520, seed=5):
        rng = np.random.default_rng(seed)
        self.x = rng.uniform(0, W, n)
        self.y = rng.uniform(0, H, n)
        self.vy = rng.uniform(50, 170, n)
        self.vx = rng.uniform(-24, 10, n)
        self.r = rng.uniform(1.5, 4.5, n)
        self.n = n
    def step(self, dt, t):
        self.y += self.vy * dt
        self.x += (self.vx + 18 * math.sin(t * 0.9)) * dt
        over = self.y > H + 10
        self.y[over] = -10
        self.x[self.x < -10] = W + 10
        self.x[self.x > W + 10] = -10
    def draw(self, d):
        for i in range(self.n):
            r = self.r[i]
            d.ellipse([self.x[i] - r, self.y[i] - r, self.x[i] + r, self.y[i] + r],
                      fill=(235, 240, 252))

SNOW = Snow()

def exterior_frame(f, t_global):
    t = t_global  # seconds within scene
    img = EXT_BG.copy().convert("RGBA")
    d = ImageDraw.Draw(img)
    # signal rings expanding from beacon
    for k in range(3):
        ph = ((t * 0.7 + k / 3) % 1.0)
        r = 30 + ph * 260
        a = int(150 * (1 - ph))
        d.ellipse([BX - r, BY - r * 0.55, BX + r, BY + r * 0.55],
                  outline=VIOLET + (a,), width=4)
    # searchlight beam sweeping from hut
    ang = math.sin(t * 0.55) * 0.9 - 0.35
    beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    sx, sy = 870, 640
    length = 1100
    # beam from (sx,sy) upward at angle
    bx = sx + math.sin(ang) * length
    by = sy - math.cos(ang) * length
    bd.polygon([(sx - 26, sy), (sx + 26, sy), (bx + 130, by), (bx - 130, by)],
               fill=(255, 240, 200, 34))
    beam = beam.filter(ImageFilter.GaussianBlur(24))
    img.alpha_composite(beam)
    d = ImageDraw.Draw(img)
    # beacon blink
    blink = 0.5 + 0.5 * math.sin(t * 4.2)
    br = 10 + 6 * blink
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gl)
    gd.ellipse([BX - br - 26, BY - br - 26, BX + br + 26, BY + br + 26],
               fill=(255, 70, 70, int(30 + 90 * blink)))
    gl = gl.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(gl)
    d = ImageDraw.Draw(img)
    d.ellipse([BX - br, BY - br, BX + br, BY + br], fill=(255, 80, 80))
    # snow
    SNOW.step(1 / FPS, t_global)
    SNOW.draw(d)
    # 80s caption chip
    if t > 1.0:
        p = ease_out_cubic((t - 1.0) / 0.6)
        chip = Image.new("RGBA", (560, 64), (0, 0, 0, 0))
        cd = ImageDraw.Draw(chip)
        cd.rounded_rectangle([0, 0, 560, 64], radius=32, fill=(10, 10, 16, 200),
                             outline=VIOLET + (255,), width=3)
        fnt = font(FONT_BOLD, 30)
        cd.text((36, 14), "100% CODE - ZERO AI", font=fnt, fill=WHITE + (255,))
        chip = chip.resize((int(560 * p), int(64 * p)), Image.LANCZOS) if p < 1 else chip
        img.alpha_composite(chip, (120, 120))
    return apply_vignette(img.convert("RGB"))

# ================= CONTROL ROOM (20-34) =================
TELETYPE_LINES = [
    ">> TUNE 88.5 FM",
    ">> SIGNAL LOCKED",
    ">> DECODING INCOMING ...",
    "HELLO FROM THE STATIC",
    "THIS SCENE IS 100% CODE",
]

def build_control_bg():
    img = Image.new("RGB", (W, H), (8, 8, 12))
    d = ImageDraw.Draw(img)
    # wall panels
    for x in range(0, W, 240):
        d.rectangle([x + 6, 40, x + 234, H - 40], outline=(24, 26, 34), width=2)
    return img

CTRL_BG = build_control_bg()

def control_frame(f, t):
    img = CTRL_BG.copy().convert("RGBA")
    d = ImageDraw.Draw(img)
    # main CRT screen
    sx0, sy0, sx1, sy1 = 150, 120, 1230, 780
    d.rounded_rectangle([sx0 - 14, sy0 - 14, sx1 + 14, sy1 + 14], radius=26, fill=(20, 22, 30))
    d.rounded_rectangle([sx0, sy0, sx1, sy1], radius=18, fill=(4, 14, 8))
    # scanlines
    for yy in range(sy0, sy1, 6):
        d.line([(sx0, yy), (sx1, yy)], fill=(0, 0, 0, 90), width=2)
    # teletype text (chars appear over time)
    fnt = font(FONT_MONO_B, 44)
    chars = int(max(0, (t - 1.0)) * 22)
    y = sy0 + 60
    rem = chars
    shown_any = False
    for line in TELETYPE_LINES:
        if rem >= len(line):
            d.text((sx0 + 50, y), line, font=fnt, fill=GREEN + (255,))
            rem -= len(line) + 4
            shown_any = True
        elif rem > 0:
            d.text((sx0 + 50, y), line[:rem], font=fnt, fill=GREEN + (255,))
            tw, _ = text_size(d, line[:rem], fnt)
            if int(t * 3) % 2 == 0:
                d.rectangle([sx0 + 50 + tw + 8, y + 6, sx0 + 50 + tw + 26, y + 44], fill=GREEN + (255,))
            rem = 0
            shown_any = True
            break
        y += 74
    if shown_any and rem <= 0 and int(t * 3) % 2 == 0:
        pass
    # screen glow flicker
    fl = 0.04 + 0.02 * math.sin(t * 31)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rounded_rectangle([sx0, sy0, sx1, sy1], radius=18, fill=(80, 255, 140, int(255 * fl)))
    ov = ov.filter(ImageFilter.GaussianBlur(30))
    img.alpha_composite(ov)
    d = ImageDraw.Draw(img)
    # VU meters (right side)
    mx0 = 1300
    d.text((mx0, 120), "SIGNAL", font=font(FONT_BOLD, 30), fill=MUTED + (255,))
    d.text((mx0, 330), "AUDIO", font=font(FONT_BOLD, 30), fill=MUTED + (255,))
    for k, yy in enumerate([170, 380]):
        v = 0.55 + 0.4 * math.sin(t * 5.1 + k * 2.2) * math.sin(t * 1.7 + k)
        v = clamp01(v)
        d.rounded_rectangle([mx0, yy, mx0 + 470, yy + 90], radius=14, fill=(14, 16, 22))
        bw = int(470 * v)
        col = GREEN if v < 0.8 else AMBER
        if bw > 8:
            d.rounded_rectangle([mx0 + 6, yy + 6, mx0 + 6 + bw, yy + 84], radius=10, fill=col + (255,))
        for i in range(10):
            d.line([(mx0 + i * 47, yy + 96), (mx0 + i * 47, yy + 108)],
                   fill=(60, 64, 80, 255), width=3)
    # LED row
    for i in range(12):
        on = int(t * (2 + (i % 3)) + i * 1.3) % 2 == 0
        col = [RED, GREEN, AMBER][i % 3] if on else (40, 42, 52)
        x = mx0 + i * 40
        d.ellipse([x, 560, x + 24, 584], fill=col + (255,))
    d.text((mx0, 620), "TX ARRAY", font=font(FONT_BOLD, 26), fill=MUTED + (255,))
    # oscilloscope
    ox0, oy0, ox1, oy1 = mx0, 680, mx0 + 470, 940
    d.rounded_rectangle([ox0 - 10, oy0 - 10, ox1 + 10, oy1 + 10], radius=16, fill=(20, 22, 30))
    d.rounded_rectangle([ox0, oy0, ox1, oy1], radius=12, fill=(4, 10, 8))
    pts = []
    for i in range(120):
        xx = ox0 + 10 + i * (450 / 120)
        yy = (oy0 + oy1) / 2 + math.sin(i * 0.22 + t * 9) * 60 * math.sin(t * 0.8 + 0.4)
        pts.append((xx, yy))
    d.line(pts, fill=GREEN + (255,), width=4)
    # caption
    if t > 0.6:
        fnt2 = font(FONT_BOLD, 30)
        s = "every letter printed by code"
        tw, _ = text_size(d, s, fnt2)
        d.rounded_rectangle([W - tw - 120, H - 120, W - 60, H - 56], radius=32,
                            fill=(10, 10, 16, 210), outline=GREEN + (255,), width=3)
        d.text((W - tw - 90, H - 108), s, font=fnt2, fill=WHITE + (255,))
    return apply_vignette(img.convert("RGB"))

# ================= VS (34-46) =================
VS_ROWS = [
    ("guesses every time", "exact every time"),
    ("pay per try", "100% free, unlimited"),
    ("characters change", "same every frame"),
    ("can't fix one frame", "edit any single frame"),
]

def vs_frame(f, t):
    img = canvas().convert("RGBA")
    d = ImageDraw.Draw(img)
    # divider
    d.line([(W / 2, 130), (W / 2, H - 60)], fill=(50, 52, 66, 255), width=4)
    # headers
    p = ease_out_cubic(t / 0.6)
    for side, label, col, x in [("AI MODEL", "AI MODEL", (150, 150, 165), W * 0.25),
                               ("PURE CODE", "PURE CODE", VIOLET, W * 0.75)]:
        fnt = font(FONT_BOLD, 72)
        tw, th = text_size(d, label, fnt)
        sc = 0.5 + 0.5 * p
        tmp = Image.new("RGBA", (tw + 40, th + 40), (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text((20, 20), label, font=fnt, fill=col + (255,))
        tmp = tmp.resize((int(tmp.width * sc), int(tmp.height * sc)), Image.LANCZOS)
        img.alpha_composite(tmp, (int(x - tmp.width / 2), int(170 - 20 * sc)))
    # rows
    for i, (left, right) in enumerate(VS_ROWS):
        rt = t - (1.2 + i * 1.6)
        if rt < 0:
            continue
        rp = spring(rt / 0.45)
        y = 330 + i * 150
        # left: X mark + text (muted)
        fnt = font(FONT_REG, 40)
        a = int(255 * clamp01(rt / 0.3))
        # X
        xs, ys, r = W * 0.25 - 330, y + 8, 22
        d.line([(xs - r, ys - r), (xs + r, ys + r)], fill=RED + (a,), width=7)
        d.line([(xs - r, ys + r), (xs + r, ys - r)], fill=RED + (a,), width=7)
        d.text((W * 0.25 - 280, y - 12 * (1 - rp)), left, font=fnt, fill=(170, 170, 185, a))
        # right: check + text (bright)
        xs2 = W * 0.75 - 330
        d.line([(xs2 - r, ys), (xs2 - 2, ys + r)], fill=GREEN + (a,), width=8)
        d.line([(xs2 - 2, ys + r), (xs2 + r + 10, ys - r - 6)], fill=GREEN + (a,), width=8)
        fntb = font(FONT_BOLD, 42)
        if i == 1:
            img = glow_text(img, W * 0.75 - 40, y - 12 * (1 - rp), right, fntb, WHITE).convert("RGBA")
            d = ImageDraw.Draw(img)
        else:
            d.text((W * 0.75 - 280, y - 12 * (1 - rp)), right, font=fntb, fill=WHITE + (a,))
    return apply_vignette(img.convert("RGB"))

# ================= TERMINAL (46-56) =================
TERM_SCRIPT = [
    (0.5, "$ python render.py", "cmd"),
    (1.6, "rendering 1800 frames ...", "out"),
    (2.6, "PROGRESS", "bar"),
    (5.6, "done - 1800 frames in 41.2s", "out"),
    (6.6, "0 credits  |  no watermark  |  no queue", "punch"),
]

def terminal_frame(f, t):
    img = Image.new("RGB", (W, H), (6, 6, 9)).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([120, 90, W - 120, H - 90], radius=22, fill=(10, 10, 14, 255),
                        outline=(44, 46, 60, 255), width=3)
    # traffic dots
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([170 + i * 44, 130, 196 + i * 44, 156], fill=c + (255,))
    d.text((170, 190), "mulaa@studio: ~/codetovideo", font=font(FONT_MONO, 28),
           fill=MUTED + (255,))
    fnt = font(FONT_MONO_B, 46)
    y = 300
    for t0, s, kind in TERM_SCRIPT:
        if t < t0:
            break
        if kind == "bar":
            # animated progress bar
            bp = clamp01((t - t0) / 2.6)
            bw_total = 1100
            d.rounded_rectangle([200, y, 200 + bw_total, y + 54], radius=12, fill=(24, 26, 34, 255))
            bw = int(bw_total * bp)
            if bw > 8:
                d.rounded_rectangle([200, y, 200 + bw, y + 54], radius=12, fill=VIOLET + (255,))
            pct = f"{int(bp * 100)}%"
            d.text((200 + bw_total + 30, y - 2), pct, font=fnt, fill=WHITE + (255,))
            y += 110
        else:
            col = VIOLET if kind == "cmd" else (GREEN if kind == "punch" else (225, 225, 235))
            ff = font(FONT_BOLD, 52) if kind == "punch" else fnt
            if kind == "cmd":
                # type-on
                nch = int((t - t0) * 30)
                s2 = s[:nch]
                d.text((200, y), s2, font=ff, fill=col + (255,))
                if nch < len(s) and int(t * 3) % 2 == 0:
                    tw, _ = text_size(d, s2, ff)
                    d.rectangle([200 + tw + 8, y + 6, 200 + tw + 26, y + 50], fill=VIOLET + (255,))
            elif kind == "punch":
                pp = spring((t - t0) / 0.5)
                sc = 0.7 + 0.3 * pp
                tw, th = text_size(d, s, ff)
                tmp = Image.new("RGBA", (tw + 60, th + 60), (0, 0, 0, 0))
                ImageDraw.Draw(tmp).text((30, 30), s, font=ff, fill=WHITE + (255,))
                gl = Image.new("RGBA", tmp.size, (0, 0, 0, 0))
                ImageDraw.Draw(gl).text((30, 30), s, font=ff, fill=VIOLET + (130,))
                gl = gl.filter(ImageFilter.GaussianBlur(16))
                gl = gl.resize((int(gl.width * sc), int(gl.height * sc)), Image.LANCZOS)
                tmp = tmp.resize((int(tmp.width * sc), int(tmp.height * sc)), Image.LANCZOS)
                img.alpha_composite(gl, (int(200 - 30 * sc), int(y - 30 * sc)))
                img.alpha_composite(tmp, (int(200 - 30 * sc), int(y - 30 * sc)))
                d = ImageDraw.Draw(img)
            else:
                d.text((200, y), s, font=ff, fill=col + (255,))
            y += 96
    # cursor at end
    if t > 7.2 and int(t * 2.5) % 2 == 0:
        d.rectangle([200, y + 10, 232, y + 58], fill=VIOLET + (255,))
    return apply_vignette(img.convert("RGB"))

# ================= FLOWCHART (56-66) =================
FLOW_STEPS = [
    "Pick a scene",
    "Draw it in code",
    "Animate the camera",
    "Render on your laptop",
    "Edit + post",
]

def flow_frame(f, t):
    img = canvas().convert("RGBA")
    d = ImageDraw.Draw(img)
    draw_centered(d, W / 2, 130, "THE 5-STEP FORMULA", font(FONT_BOLD, 58), WHITE)
    n = len(FLOW_STEPS)
    gap = 40
    bw, bh = 300, 170
    total_w = n * bw + (n - 1) * gap
    x0 = (W - total_w) / 2
    y0 = 400
    fnt_num = font(FONT_BOLD, 64)
    fnt_s = font(FONT_BOLD, 33)
    for i, s in enumerate(FLOW_STEPS):
        st = t - (0.5 + i * 1.1)
        if st < 0:
            continue
        p = spring(st / 0.5)
        x = x0 + i * (bw + gap)
        cx, cy = x + bw / 2, y0 + bh / 2
        w2, h2 = bw * p, bh * p
        # card
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([cx - w2 / 2, cy - h2 / 2, cx + w2 / 2, cy + h2 / 2],
                             radius=26, fill=(20, 20, 30, 255),
                             outline=VIOLET + (255,), width=4)
        card = card.filter(ImageFilter.GaussianBlur(0))
        img.alpha_composite(card)
        d = ImageDraw.Draw(img)
        # number badge
        d.ellipse([cx - 34 * p, cy - h2 / 2 - 34 * p, cx + 34 * p, cy - h2 / 2 + 34 * p],
                  fill=VIOLET + (255,))
        num = str(i + 1)
        tw, th = text_size(d, num, fnt_num)
        d.text((cx - tw / 2, cy - h2 / 2 - th / 2 - 8), num, font=fnt_num, fill=WHITE + (255,))
        # label (wrap)
        words = s.split()
        lines = []
        cur = ""
        for w_ in words:
            test = (cur + " " + w_).strip()
            tw2, _ = text_size(d, test, fnt_s)
            if tw2 > bw - 50 and cur:
                lines.append(cur); cur = w_
            else:
                cur = test
        lines.append(cur)
        ly = cy - (len(lines) * 44) / 2 + 30
        for ln in lines:
            draw_centered(d, cx, ly, ln, fnt_s, WHITE)
            ly += 44
        # arrow to next
        if i < n - 1 and st > 0.5:
            ax = x + bw + gap / 2
            d.polygon([(ax - 14, cy - 18), (ax - 14, cy + 18), (ax + 18, cy)],
                      fill=VIOLET + (255,))
    return apply_vignette(img.convert("RGB"))

# ================= CTA (66-72) =================
def cta_frame(f, t):
    img = canvas().convert("RGBA")
    d = ImageDraw.Draw(img)
    p1 = spring(t / 0.5)
    img = glow_text(img, W / 2, 250, "FULL SOURCE CODE", font(FONT_BOLD, 84), WHITE).convert("RGBA")
    d = ImageDraw.Draw(img)
    draw_centered(d, W / 2, 380, "ON GITHUB", font(FONT_BOLD, 84), VIOLET)
    if t > 0.8:
        p2 = ease_out_cubic((t - 0.8) / 0.5)
        s = "github.com/Sehrish64/Codetovideo-"
        fnt = font(FONT_MONO_B, 52)
        tw, th = text_size(d, s, fnt)
        pad = 44
        d.rounded_rectangle([W / 2 - tw / 2 - pad, 540, W / 2 + tw / 2 + pad, 540 + th + pad * 1.4],
                            radius=24, fill=(20, 20, 30, int(255 * p2)),
                            outline=VIOLET + (int(255 * p2),), width=4)
        d.text((W / 2 - tw / 2, 540 + pad * 0.55), s, font=fnt,
               fill=(255, 255, 255, int(255 * p2)))
    if t > 1.8:
        p3 = ease_out_cubic((t - 1.8) / 0.5)
        draw_centered(d, W / 2, 780, "New builds every Friday",
                      font(FONT_BOLD, 54), (255, 255, 255, int(255 * p3)))
    # subscribe bell hint
    if t > 2.6:
        a = int(255 * clamp01((t - 2.6) / 0.5))
        pulse = 1 + 0.06 * math.sin(t * 6)
        fntb = font(FONT_BOLD, 40)
        s = "Subscribe for the next build"
        tw, _ = text_size(d, s, fntb)
        d.rounded_rectangle([W / 2 - tw / 2 - 40, 890, W / 2 + tw / 2 + 40, 890 + 76],
                            radius=38, fill=VIOLET + (a,))
        d.text((W / 2 - tw / 2, 906), s, font=fntb, fill=(255, 255, 255, a))
    return apply_vignette(img.convert("RGB"))

# ================= MAIN =================
SCENES = [
    (0, 8, hook_frame),
    (8, 20, exterior_frame),
    (20, 34, control_frame),
    (34, 46, vs_frame),
    (46, 56, terminal_frame),
    (56, 66, flow_frame),
    (66, 72, cta_frame),
]

def main():
    total = 72 * FPS
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else total
    for f in range(start, min(end, total)):
        ct = f / FPS
        fn = None
        for s0, s1, func in SCENES:
            if s0 <= ct < s1:
                fn = (func, s0)
                break
        if fn is None:
            func, s0 = SCENES[-1][2], SCENES[-1][0]
        else:
            func, s0 = fn
        img = func(f, ct - s0)
        img.save(os.path.join(OUT, f"f{f:05d}.png"))
        if f % 120 == 0:
            print(f"frame {f}/{total}", flush=True)

if __name__ == "__main__":
    main()
