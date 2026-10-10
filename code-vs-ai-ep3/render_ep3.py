"""CodeToVideo — Code vs AI EP3: a cartoon FILM SCENE in pure code.
Content 96s @30fps = 2880 frames. Bumpers added at assembly.
Scenes (content-local seconds):
  0-10   HOOK   kinetic text
  10-32  WALK   silhouette walker crosses snow toward radio tower (parallax, zoom)
  32-48  LIGHT  searchlight sweeps, locks onto walker; walker looks up
  48-62  PULSE  tower signal rings + teletype "SOMEONE IS OUT THERE"
  62-76  REVEAL "No artist drew a single frame..." over scene
  76-90  TERM   $ python3 render_scene.py proof
  90-96  CTA    GitHub + Friday
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, "/home/hatch/workspace/imagine_media/ai-video-channel/trailer")
from lib import (W, H, FPS, BG, VIOLET, WHITE, MUTED, canvas, font, text_size,
                 draw_centered, glow_text, clamp01, ease_out_cubic, ease_in_out,
                 ease_in_cubic, spring, prog, FONT_BOLD, FONT_REG, FONT_MONO, FONT_MONO_B,
                 render_code_frame)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
os.makedirs(OUT, exist_ok=True)

TEAL_DK = (10, 26, 34)
TEAL = (24, 70, 84)
WARM = (255, 196, 130)
GREEN = (80, 255, 140)
RED = (255, 90, 90)
SNOW_C = (228, 236, 250)

# ---------- precomputed: sky gradient ----------
def vgrad(h, w, top, bottom):
    top = np.array(top, dtype=np.float32); bottom = np.array(bottom, dtype=np.float32)
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    col = (top[None, None, :] * (1 - t) + bottom[None, None, :] * t).astype(np.uint8)
    return np.repeat(col, w, axis=1)

SKY = vgrad(H, W, (6, 12, 26), (16, 30, 52))  # deep night blue

# stars (fixed)
srng = np.random.default_rng(21)
NST = 220
ST_X = srng.uniform(0, W, NST); ST_Y = srng.uniform(0, 520, NST)
ST_R = srng.uniform(0.8, 2.4, NST); ST_P = srng.uniform(0, 6.28, NST)

# vignette
def make_vignette(strength=0.38):
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

# ---------- precomputed: mountains layer ----------
def build_mountains():
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(5)
    # far range
    pts = [(0, 700)]
    x = 0
    while x < W:
        pts.append((x, 700 - rng.uniform(120, 300)))
        x += rng.uniform(140, 260)
    pts.append((W, 700))
    d.polygon(pts, fill=(20, 34, 58, 255))
    # snow caps on far range (small white triangles at peaks)
    # near range
    pts2 = [(0, 800)]
    x = 0
    while x < W:
        pts2.append((x, 800 - rng.uniform(60, 170)))
        x += rng.uniform(180, 320)
    pts2.append((W, 800))
    d.polygon(pts2, fill=(13, 22, 40, 255))
    return lay
MOUNTAINS = build_mountains()

# ---------- precomputed: radio tower layer (no beacon) ----------
def build_tower():
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    tx, base_y, top_y = 1450, 760, 300
    d.polygon([(tx - 80, base_y), (tx + 80, base_y), (tx + 22, top_y), (tx - 22, top_y)],
              fill=(10, 12, 22, 255))
    for yy in range(top_y + 20, base_y, 44):
        wf = (yy - top_y) / (base_y - top_y)
        hw = 22 + wf * 58
        d.line([(tx - hw, yy), (tx + hw, yy)], fill=(28, 32, 52, 255), width=5)
        d.line([(tx - hw, yy), (tx + hw, yy + 44)], fill=(22, 26, 44, 255), width=2)
        d.line([(tx + hw, yy), (tx - hw, yy + 44)], fill=(22, 26, 44, 255), width=2)
    d.line([(tx, top_y), (tx, top_y - 70)], fill=(10, 12, 22, 255), width=9)
    # dish
    d.ellipse([tx + 40, top_y + 60, tx + 110, top_y + 130], outline=(40, 46, 70, 255), width=6)
    return lay, (tx, top_y - 70)
TOWER, BEACON = build_tower()

# ---------- snowfall params ----------
frng = np.random.default_rng(77)
NFL = 420
FL_X = frng.uniform(0, W, NFL); FL_Y = frng.uniform(0, H, NFL)
FL_V = frng.uniform(40, 130, NFL); FL_S = frng.uniform(1.0, 3.6, NFL)
FL_P = frng.uniform(0, 6.28, NFL)

def draw_snow(d, t, wind=18.0, alpha=235):
    for i in range(NFL):
        x = (FL_X[i] + t * wind + 24 * math.sin(t * 0.9 + FL_P[i])) % W
        y = (FL_Y[i] + t * FL_V[i]) % H
        r = FL_S[i]
        d.ellipse([x - r, y - r, x + r, y + r], fill=SNOW_C + (alpha,))

def draw_stars(d, t):
    for i in range(NST):
        tw = 0.45 + 0.55 * abs(math.sin(t * 1.4 + ST_P[i]))
        b = int(200 * tw)
        r = ST_R[i]
        d.ellipse([ST_X[i] - r, ST_Y[i] - r, ST_X[i] + r, ST_Y[i] + r],
                  fill=(b, b, min(255, b + 20), int(220 * tw)))

def draw_moon(img):
    d = ImageDraw.Draw(img)
    d.ellipse([1560, 90, 1700, 230], fill=(232, 238, 248, 255))
    d.ellipse([1590, 110, 1670, 190], fill=(210, 220, 236, 255))  # shading
    # moon glow
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([1530, 60, 1730, 260], fill=(180, 200, 240, 40))
    gl = gl.filter(ImageFilter.GaussianBlur(40))
    img.alpha_composite(gl)

# ================= CHARACTER: silhouette walker =================
def draw_walker(d, x, y_ground, s, phase, look=0.0, t=0.0, walking=True):
    """Side-view silhouette figure facing right. phase = walk radians.
    look 0..1 = head tilts up. Returns head position (for beam targeting)."""
    col = (16, 18, 28)
    rim = VIOLET
    bob = abs(math.cos(phase)) * 5 * s if walking else math.sin(t * 2) * 1.5 * s
    hip_y = y_ground - 150 * s - bob
    sh_y = hip_y - 92 * s
    # legs (two-segment, alternating)
    for k, off in enumerate([0.0, math.pi]):
        sw = math.sin(phase + off)
        if walking:
            fx = x + sw * 44 * s
            fy = y_ground - max(0.0, math.sin(phase + off + math.pi / 2)) * 18 * s
        else:
            fx = x + (14 if k == 0 else -12) * s
            fy = y_ground
        knee_x = x + sw * 18 * s + 16 * s
        knee_y = (hip_y + fy) / 2 + 7 * s
        d.line([x, hip_y, knee_x, knee_y, fx, fy], fill=col,
               width=int(17 * s), joint="curve")
    # torso
    d.line([x, hip_y, x + 7 * s, sh_y], fill=col, width=int(32 * s))
    # coat flutter behind
    fl = math.sin(t * 6.5) * 12 * s + math.sin(t * 11) * 5 * s
    d.polygon([(x - 15 * s, sh_y + 10 * s), (x - 15 * s, hip_y + 34 * s),
               (x - 52 * s - fl, hip_y + 52 * s + fl * 0.4),
               (x - 34 * s - fl * 0.5, sh_y + 26 * s)], fill=(12, 14, 24))
    # arm (far side hint) + near arm swing
    asw = math.sin(phase + math.pi) * 26 * s if walking else 4 * s
    d.line([x + 7 * s, sh_y + 12 * s, x + 20 * s + asw, sh_y + 66 * s],
           fill=col, width=int(13 * s))
    # head (tilts up with look)
    hx = x + 16 * s + look * 4 * s
    hy = sh_y - 28 * s - look * 10 * s
    d.ellipse([hx - 21 * s, hy - 21 * s, hx + 21 * s, hy + 21 * s], fill=col)
    # hood point
    d.polygon([(hx - 20 * s, hy - 6 * s), (hx - 34 * s, hy - 26 * s),
               (hx - 8 * s, hy - 20 * s)], fill=col)
    # violet rim light on right edges
    d.line([x + 24 * s, hip_y + 4 * s, x + 30 * s, sh_y + 4 * s],
           fill=rim, width=max(2, int(3.5 * s)))
    d.arc([hx - 21 * s, hy - 21 * s, hx + 21 * s, hy + 21 * s],
          start=-70, end=55, fill=rim, width=max(2, int(3 * s)))
    return (hx, hy)

def draw_ground(img):
    d = ImageDraw.Draw(img)
    # snow field with subtle blue shading + sparkle
    d.polygon([(0, 760), (W, 730), (W, H), (0, H)], fill=(38, 52, 82))
    d.polygon([(0, 800), (W, 775), (W, H), (0, H)], fill=(30, 42, 68))
    # drifts
    rng = np.random.default_rng(3)
    for _ in range(26):
        x = rng.uniform(0, W); y = rng.uniform(790, 1000)
        rx, ry = rng.uniform(60, 200), rng.uniform(12, 30)
        d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=(44, 60, 94))

def draw_beacon(d, t, on=True):
    bx, by = BEACON
    if on and (t % 1.6) < 0.9:
        pulse = 1 - (t % 1.6) / 0.9
        r = 14 + pulse * 60
        d.ellipse([bx - r, by - r, bx + r, by + r],
                  outline=(255, 90, 90, int(160 * (1 - pulse)) + 30), width=4)
        d.ellipse([bx - 11, by - 11, bx + 11, by + 11], fill=(255, 110, 110))
    else:
        d.ellipse([bx - 9, by - 9, bx + 9, by + 9], fill=(120, 50, 50))

def draw_searchlight(img, d, src, angle_deg, length, intensity=1.0, color=(190, 170, 255)):
    """Volumetric-ish beam wedge from src at angle (degrees, 0=right, -90=up)."""
    ang = math.radians(angle_deg)
    dx, dy = math.cos(ang), math.sin(ang)
    # perpendicular
    px, py = -dy, dx
    w0, w1 = 26, 150
    sx, sy = src
    pts = [(sx + px * w0, sy + py * w0), (sx - px * w0, sy - py * w0),
           (sx + dx * length - px * w1, sy + dy * length - py * w1),
           (sx + dx * length + px * w1, sy + dy * length + py * w1)]
    beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    bd.polygon(pts, fill=color + (int(70 * intensity),))
    beam = beam.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(beam)
    # hot core
    core = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(core)
    w0c, w1c = 10, 60
    cpts = [(sx + px * w0c, sy + py * w0c), (sx - px * w0c, sy - py * w0c),
            (sx + dx * length - px * w1c, sy + dy * length - py * w1c),
            (sx + dx * length + px * w1c, sy + dy * length + py * w1c)]
    cd.polygon(cpts, fill=(235, 230, 255, int(110 * intensity)))
    core = core.filter(ImageFilter.GaussianBlur(8))
    img.alpha_composite(core)
    # source glow
    d.ellipse([sx - 16, sy - 16, sx + 16, sy + 16], fill=(240, 235, 255))

def draw_signal_rings(d, cx, cy, t, t0, count=4, color=VIOLET):
    for k in range(count):
        lt = (t - t0) - k * 0.55
        if lt < 0:
            continue
        r = 30 + lt * 260
        a = max(0, int(200 * (1 - lt / 2.2)))
        if a <= 0 or r > 700:
            continue
        d.ellipse([cx - r, cy - r * 0.42, cx + r, cy + r * 0.42],
                  outline=color + (a,), width=6)

# ================= SCENE BUILDERS =================
def base_night():
    """Static night backdrop: sky + stars handled per-frame, mountains + tower composited."""
    img = Image.fromarray(SKY).convert("RGBA")
    return img

# ================= HOOK (0-8) =================
def hook_frame(f, t):
    img = canvas().convert("RGBA")
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(11)
    px = rng.uniform(0, W, 70); py = rng.uniform(0, H, 70)
    for i in range(70):
        x = (px[i] + t * 12 * (0.3 + 0.7 * ((i % 5) / 5))) % W
        y = (py[i] - t * 8) % H
        a = int(40 + 40 * math.sin(t * 2 + i))
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=VIOLET + (max(0, a),))
    lines = [
        (0.3, 2.4, "Every film you've seen", 72, WHITE, False),
        (1.1, 3.2, "was drawn by someone.", 72, WHITE, False),
        (2.8, 5.4, "But what if CODE", 96, VIOLET, True),
        (4.0, 6.6, "drew this one?", 96, WHITE, False),
    ]
    y = 320
    for t0, t1, s, size, col, glow in lines:
        if t >= t0:
            p = spring((t - t0) / 0.5)
            fnt = font(FONT_BOLD, size)
            tw, th = text_size(ImageDraw.Draw(img), s, fnt)
            sc = 0.6 + 0.4 * p
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
            pxa = np.array(ta); pxa[..., 3] = (pxa[..., 3].astype(np.float32) * alpha / 255).astype(np.uint8)
            ta = Image.fromarray(pxa)
            img.alpha_composite(ta, (int(W / 2 - nw / 2), int(y - 40 * sc)))
            y += int((th + 30) * (0.7 + 0.3 * p))
        else:
            y += 100
    return apply_vignette(img.convert("RGB"))

# ================= SCENE (8-30): one compact film moment =================
def scene_frame(f, t):
    # t: content-local seconds within 8..30
    img = base_night()
    d = ImageDraw.Draw(img)
    draw_stars(d, t)
    draw_moon(img)
    d = ImageDraw.Draw(img)
    img.alpha_composite(MOUNTAINS)
    img.alpha_composite(TOWER)
    d = ImageDraw.Draw(img)
    draw_beacon(d, t)
    draw_ground(img)
    d = ImageDraw.Draw(img)
    draw_snow(d, t, wind=22.0)

    # walker: walks 8->20 (x 350->950), then idle + look up
    wt = t  # 0..22 local
    walking = wt < 12
    if walking:
        wx = 350 + (950 - 350) * ease_in_out(wt / 12)
        phase = wt * 9.0
        look = 0.0
    else:
        wx = 950
        phase = 12 * 9.0  # frozen mid-stride -> settle to neutral
        look = clamp01((wt - 12.5) / 2.0)
    hx, hy = draw_walker(d, wx, 880, 1.0, phase, look=look, t=t, walking=walking)

    # searchlight: sweeps 12->17, locks 17+
    if wt >= 12:
        lt = wt - 12
        if lt < 5:
            ang = 100 + (139 - 100) * ease_in_out(lt / 5)
            inten = 0.7
        else:
            ang = 139 + math.sin((lt - 5) * 1.2) * 1.5
            inten = 1.0
        draw_searchlight(img, ImageDraw.Draw(img), (1450, 430), ang, 780, intensity=inten)
        d = ImageDraw.Draw(img)
        # light pool on walker when locked
        if lt >= 5:
            pool = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            pd = ImageDraw.Draw(pool)
            pa = int(60 + 20 * math.sin(t * 3))
            pd.ellipse([hx - 90, 820, hx + 90, 940], fill=(200, 185, 255, pa))
            pool = pool.filter(ImageFilter.GaussianBlur(24))
            img.alpha_composite(pool)
            d = ImageDraw.Draw(img)

    # signal rings pulse 18->22
    if wt >= 18:
        draw_signal_rings(d, 1450, 300, t, 8 + 18, count=4)

    # foreground drifting snow blobs (parallax)
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fg)
    frng = np.random.default_rng(31)
    for i in range(14):
        bx = (frng.uniform(0, W) + t * 60 * (0.5 + (i % 3) * 0.3)) % (W + 200) - 100
        by = frng.uniform(700, 1050)
        r = 26 + (i % 4) * 14
        fd.ellipse([bx - r, by - r, bx + r, by + r], fill=(150, 170, 210, 36))
    fg = fg.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(fg)

    # camera slow zoom 1.00 -> 1.06
    z = 1.0 + 0.06 * ease_in_out(wt / 22)
    zw, zh = int(W * z), int(H * z)
    img = img.resize((zw, zh), Image.LANCZOS)
    x0, y0 = (zw - W) // 2, (zh - H) // 2 + int(20 * ease_in_out(wt / 22))
    img = img.crop((x0, y0, x0 + W, y0 + H))
    return apply_vignette(img.convert("RGB"))

# ================= VS (30-42): AI MODEL vs PURE CODE =================
def vs_frame(f, t):
    img = canvas().convert("RGBA")
    d = ImageDraw.Draw(img)
    draw_centered(d, W / 2, 120, "AI MODEL  vs  PURE CODE", font(FONT_BOLD, 64), WHITE)
    # panels
    pw, ph = 760, 640
    lx, rx, py = 110, 1050, 260
    for (x0, col, title, rows) in [
        (lx, (200, 70, 70), "AI MODEL",
         [("guesses every time", False), ("credits per try", False), ("characters change", False)]),
        (rx, VIOLET, "PURE CODE",
         [("exact every time", True), ("free forever", True), ("same every frame", True)]),
    ]:
        d.rounded_rectangle([x0, py, x0 + pw, py + ph], radius=28,
                            fill=(18, 18, 26), outline=col, width=4)
        draw_centered(d, x0 + pw / 2, py + 44, title, font(FONT_BOLD, 54), col)
        yy = py + 160
        for i, (txt, good) in enumerate(rows):
            rt = t - (1.0 + i * 0.9)
            if rt > 0:
                p = spring(rt / 0.45)
                mark = "✓" if good else "✗"
                mc = (110, 230, 140) if good else (230, 110, 110)
                a = int(255 * clamp01(rt / 0.3))
                fnt = font(FONT_BOLD, 44)
                tw = text_size(d, mark + "  " + txt, fnt)[0]
                sc = 0.7 + 0.3 * p
                d.text((x0 + pw / 2 - tw * sc / 2, yy), mark, font=fnt,
                       fill=mc + (a,))
                d.text((x0 + pw / 2 - tw * sc / 2 + text_size(d, mark + "  ", fnt)[0] * sc, yy),
                       txt, font=fnt, fill=WHITE + (a,))
            yy += 120
    # VS badge
    bt = spring(clamp01((t - 0.4) / 0.5))
    bs = int(150 * (0.5 + 0.5 * bt))
    d.ellipse([W / 2 - bs / 2, 480 - bs / 2, W / 2 + bs / 2, 480 + bs / 2],
              fill=VIOLET)
    draw_centered(d, W / 2, 480 - 34, "VS", font(FONT_BOLD, 56), WHITE)
    return apply_vignette(img.convert("RGB"))

# ================= TERM (42-54): terminal proof =================
CODE_LINES = [
    "$ python3 render_scene.py",
    "rendering frames ...",
]
def term_frame(f, t):
    img = canvas().convert("RGBA")
    d = ImageDraw.Draw(img)
    draw_centered(d, W / 2, 120, "PROOF: IT RENDERED ON MY LAPTOP",
                  font(FONT_BOLD, 54), WHITE)
    # terminal window
    tw_, th_ = 1420, 620
    x0, y0 = (W - tw_) // 2, 230
    d.rounded_rectangle([x0, y0, x0 + tw_, y0 + th_], radius=22, fill=(12, 13, 20),
                        outline=(60, 64, 90), width=3)
    d.rounded_rectangle([x0, y0, x0 + tw_, y0 + 64], radius=22, fill=(24, 26, 38))
    d.text((x0 + 30, y0 + 74), "", font=font(FONT_MONO, 34))
    fnt = font(FONT_MONO, 36)
    yy = y0 + 100
    # typed command
    cmd = CODE_LINES[0]
    nch = int(clamp01((t - 0.5) / 1.8) * len(cmd))
    d.text((x0 + 40, yy), cmd[:nch], font=fnt, fill=(140, 255, 170))
    if nch < len(cmd) and int(t * 3) % 2 == 0:
        d.rectangle([x0 + 40 + text_size(d, cmd[:nch], fnt)[0], yy,
                     x0 + 52 + text_size(d, cmd[:nch], fnt)[0], yy + 40],
                    fill=(140, 255, 170))
    yy += 70
    if t > 2.6:
        d.text((x0 + 40, yy), CODE_LINES[1], font=fnt, fill=MUTED)
        yy += 60
        # progress bar
        p = clamp01((t - 2.8) / 4.5)
        bw = 900
        d.rectangle([x0 + 40, yy, x0 + 40 + bw, yy + 34], outline=(80, 84, 110), width=2)
        d.rectangle([x0 + 40, yy, x0 + 40 + bw * p, yy + 34], fill=VIOLET)
        pct = f"{int(p * 1860)}/1860 frames"
        d.text((x0 + 40 + bw + 24, yy - 4), pct, font=fnt, fill=WHITE)
        yy += 70
    if t > 7.6:
        d.text((x0 + 40, yy), "done. 1860 frames, local machine.",
               font=fnt, fill=(140, 255, 170))
        yy += 64
    if t > 8.8:
        glow_text(img, W / 2, yy + 10, "0 credits  |  no watermark  |  no queue",
                  font(FONT_BOLD, 44), WHITE)
    return apply_vignette(img.convert("RGB"))

# ================= CTA (54-62) =================
def cta_frame(f, t):
    img = canvas().convert("RGBA")
    d = ImageDraw.Draw(img)
    lines = [
        (0.2, "The full code is", 72, WHITE, False),
        (0.9, "in the description.", 72, VIOLET, True),
    ]
    y = 300
    for t0, s, size, col, glow in lines:
        if t >= t0:
            p = spring((t - t0) / 0.5)
            fnt = font(FONT_BOLD, size)
            tw, th = text_size(ImageDraw.Draw(img), s, fnt)
            sc = 0.6 + 0.4 * p
            tmp = Image.new("RGBA", (tw + 80, th + 80), (0, 0, 0, 0))
            ImageDraw.Draw(tmp).text((40, 40), s, font=fnt, fill=col + (255,))
            nw, nh = int(tmp.width * sc), int(tmp.height * sc)
            tmp = tmp.resize((max(1, nw), max(1, nh)), Image.LANCZOS)
            if glow:
                gl = Image.new("RGBA", tmp.size, (0, 0, 0, 0))
                ImageDraw.Draw(gl).text((40 * sc, 40 * sc), s, font=fnt, fill=VIOLET + (110,))
                gl = gl.filter(ImageFilter.GaussianBlur(14))
                img.alpha_composite(gl, (int(W / 2 - nw / 2), int(y - 40 * sc)))
            img.alpha_composite(tmp, (int(W / 2 - nw / 2), int(y - 40 * sc)))
            y += int((th + 40) * (0.7 + 0.3 * p))
        else:
            y += 110
    if t > 2.2:
        p = spring((t - 2.2) / 0.5)
        s = "github.com/Sehrish64/Codetovideo-"
        fnt = font(FONT_MONO_B, 34)
        tw, th = text_size(d, s, fnt)
        bw, bh = int(tw + 90), 96
        bx, by = W / 2 - bw / 2, 620
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=48, fill=VIOLET)
        d.text((W / 2 - tw / 2, by + bh / 2 - th / 2), s, font=fnt, fill=WHITE)
    if t > 3.4:
        a = int(255 * clamp01((t - 3.4) / 0.5))
        draw_centered(d, W / 2, 800, "New builds every Friday.",
                      font(FONT_BOLD, 48), WHITE + (a,))
    return apply_vignette(img.convert("RGB"))

# ================= MAIN =================
# content-local scene boundaries (seconds)
SCENES = [
    (0, 8, hook_frame),
    (8, 30, lambda f, t: scene_frame(f, t - 8)),
    (30, 42, lambda f, t: vs_frame(f, t - 30)),
    (42, 54, lambda f, t: term_frame(f, t - 42)),
    (54, 62, lambda f, t: cta_frame(f, t - 54)),
]
CONTENT_DUR = 62
TOTAL = CONTENT_DUR * FPS

def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else TOTAL
    for f in range(start, end):
        t = f / FPS
        fn = None
        for s0, s1, func in SCENES:
            if s0 <= t < s1:
                fn = func
                break
        if fn is None:
            fn = SCENES[-1][2]
            t = 61.9
        img = fn(f, t)
        img.save(os.path.join(OUT, "f%05d.png" % f))
        if f % 150 == 0:
            print("frame %d/%d (%.1fs)" % (f, TOTAL, t), flush=True)

if __name__ == "__main__":
    main()
