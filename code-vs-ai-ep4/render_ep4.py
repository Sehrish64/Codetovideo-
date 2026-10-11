#!/usr/bin/env python3
"""CodeToVideo EP4: "I Cooked Biryani With Python — Zero Stove".
Novelty/comedy episode: a full cooking show animated ENTIRELY in code.
Renders content frames (70s @30fps = 2100 frames). Bumpers added at assembly.
Scenes (content-local seconds):
  0-6   HOOK        "No stove. No chef. Just Python."
  6-24  INGREDIENTS code -> ingredients pop into pot
  24-42 RECIPE      def fry_onions() / def layer_rice() / def dum()
  42-60 COOKING     compiler = stove, flames, steam, dum progress bar
  60-70 PUNCHLINE   pot opens -> glowing rendered frame. CTA.
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, "/home/hatch/workspace/imagine_media/ai-video-channel/trailer")
from lib import (W, H, FPS, BG, VIOLET, VIOLET_DIM, WHITE, MUTED, CODE_BG,
                 canvas, font, text_size, draw_centered, glow_text, clamp01,
                 ease_out_cubic, ease_in_out, spring, prog,
                 FONT_BOLD, FONT_REG, FONT_MONO, FONT_MONO_B)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
os.makedirs(OUT, exist_ok=True)

GREEN = (80, 255, 140)
AMBER = (255, 190, 80)
RED = (255, 90, 90)
GOLD = (255, 200, 90)
PANEL = (16, 16, 24)
CREAM = (255, 244, 220)

DUR = 74.0
NF = int(DUR * FPS)

# ---------- vignette ----------
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

def bg_particles(d, t, n=60, seed=5):
    rng = np.random.default_rng(seed)
    px = rng.uniform(0, W, n); py = rng.uniform(0, H, n)
    for i in range(n):
        x = (px[i] + t * 10 * (0.3 + 0.7 * ((i % 5) / 5))) % W
        y = (py[i] - t * 7) % H
        a = int(35 + 35 * math.sin(t * 2 + i))
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=VIOLET + (max(0, a),))

def pop_text(img, d, cx, y, s, size, col, t0, t, glow=False):
    """Spring-pop centered text appearing at t0."""
    if t < t0:
        return
    p = spring((t - t0) / 0.45)
    fnt = font(FONT_BOLD, size)
    tw, th = text_size(d, s, fnt)
    sc = 0.5 + 0.5 * p
    tmp = Image.new("RGBA", (tw + 120, th + 120), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    if glow:
        gl = Image.new("RGBA", tmp.size, (0, 0, 0, 0))
        ImageDraw.Draw(gl).text((60, 60), s, font=fnt, fill=VIOLET + (170,))
        gl = gl.filter(ImageFilter.GaussianBlur(14))
        tmp.alpha_composite(gl)
    td.text((60, 60), s, font=fnt, fill=col + (255,))
    nw, nh = int(tmp.width * sc), int(tmp.height * sc)
    tmp = tmp.resize((max(1, nw), max(1, nh)), Image.BILINEAR)
    img.alpha_composite(tmp, (int(cx - tmp.width / 2), int(y - 60 * sc)))

# ================= shared: cooking pot =================
def draw_pot(d, cx, base_y, w, h, lid_open=0.0, fill_level=0.0, t=0.0):
    """Deg/pot. lid_open 0..1 rotates lid up. fill_level 0..1 rice fill."""
    # pot body
    d.rounded_rectangle([cx - w / 2, base_y - h, cx + w / 2, base_y], radius=40,
                        fill=(28, 28, 36), outline=VIOLET, width=5)
    # fill (rice) visible above rim when level high
    if fill_level > 0:
        fh = h * 0.35 * fill_level
        d.ellipse([cx - w / 2 + 18, base_y - h - fh + 26,
                   cx + w / 2 - 18, base_y - h + 26], fill=(245, 235, 200))
    # rim
    d.rounded_rectangle([cx - w / 2 - 16, base_y - h - 14, cx + w / 2 + 16, base_y - h + 14],
                        radius=14, fill=(40, 40, 52), outline=VIOLET_DIM, width=3)
    # handles
    d.arc([cx - w / 2 - 70, base_y - h - 20, cx - w / 2 + 10, base_y - h + 60],
          start=90, end=270, fill=VIOLET_DIM, width=10)
    d.arc([cx + w / 2 - 10, base_y - h - 20, cx + w / 2 + 70, base_y - h + 60],
          start=270, end=90, fill=VIOLET_DIM, width=10)
    # lid
    lw = w / 2 + 16
    if lid_open <= 0:
        d.ellipse([cx - lw, base_y - h - 90, cx + lw, base_y - h + 10],
                  fill=(52, 52, 66), outline=VIOLET, width=4)
        d.ellipse([cx - 22, base_y - h - 118, cx + 22, base_y - h - 74], fill=VIOLET)
    else:
        # lid flies up and tilts
        k = ease_out_cubic(lid_open)
        lx = cx + 380 * k
        ly = base_y - h - 90 - 320 * k
        tmp = Image.new("RGBA", (int(lw * 2) + 60, 220), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        td.ellipse([30, 60, 30 + lw * 2, 160], fill=(52, 52, 66, 255),
                   outline=VIOLET + (255,), width=4)
        tmp = tmp.rotate(-35 * k, expand=True, resample=Image.BICUBIC)
        return (lx, ly, tmp)
    return None

def draw_flames(img, d, cx, base_y, w, t):
    """Animated flame tongues under the pot."""
    rng = np.random.default_rng(42)
    for i in range(9):
        fx = cx - w / 2 + (i + 0.5) * (w / 9)
        fl = 0.75 + 0.25 * math.sin(t * 13 + i * 2.1) + 0.12 * math.sin(t * 29 + i)
        fh = 150 * fl
        fw = 46
        # outer orange
        d.polygon([(fx - fw, base_y), (fx + fw, base_y),
                   (fx + fw * 0.25, base_y - fh), (fx - fw * 0.25, base_y - fh)],
                  fill=(255, 120, 30, 210))
        # inner yellow
        d.polygon([(fx - fw * 0.55, base_y), (fx + fw * 0.55, base_y),
                   (fx + fw * 0.12, base_y - fh * 0.62), (fx - fw * 0.12, base_y - fh * 0.62)],
                  fill=(255, 210, 90, 230))
    # glow under pot
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([cx - w, base_y - 190, cx + w, base_y + 40], fill=(255, 140, 40, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    img.alpha_composite(glow)

def draw_steam(img, d, cx, top_y, t, n=14, seed=3):
    rng = np.random.default_rng(seed)
    sx = rng.uniform(-90, 90, n)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for i in range(n):
        ph = ((t * 0.55 + i / n) % 1.0)
        y = top_y - ph * 420
        x = cx + sx[i] + 40 * math.sin(t * 2 + i * 1.7) * ph
        r = 14 + ph * 42
        a = int(90 * (1 - ph))
        if a <= 0:
            continue
        ld.ellipse([x - r, y - r, x + r, y + r], fill=(220, 220, 235, a))
    lay = lay.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(lay)

# ================= HOOK (0-6) =================
def hook_frame(img, t):
    d = ImageDraw.Draw(img)
    bg_particles(d, t)
    pop_text(img, d, W / 2, 300, "No stove.", 92, WHITE, 0.3, t)
    pop_text(img, d, W / 2, 430, "No chef.", 92, WHITE, 1.3, t)
    pop_text(img, d, W / 2, 590, "Just PYTHON.", 120, VIOLET, 2.4, t, glow=True)
    if t > 4.0:
        p = ease_out_cubic((t - 4.0) / 0.8)
        d2 = ImageDraw.Draw(img)
        fnt = font(FONT_MONO_B, 40)
        s = "tonight: BIRYANI, in code"
        tw, th = text_size(d2, s, fnt)
        bx = (W - tw) / 2 - 40
        d2.rounded_rectangle([bx, 780, bx + tw + 80, 780 + th + 44], radius=24,
                             fill=VIOLET + (int(255 * p),))
        d2.text((bx + 40, 780 + 20), s, font=fnt,
                fill=(255, 255, 255, int(255 * p)))

# ================= INGREDIENTS (6-24) =================
ING_LINES = [
    'rice = ["basmati"] * 4',
    'masalay = {"haldi": "1 tsp",',
    '           "zeera": "2 tsp",',
    '           "garam_masala": "1 tbsp"}',
    'chicken = "leg piece"  # just a variable',
]

def code_panel(d, x, y, w, lines, t, t0, cps=28):
    """Terminal-style code panel with typing effect. Returns chars shown."""
    d.rounded_rectangle([x, y, x + w, y + 40 + len(lines) * 52], radius=18,
                        fill=PANEL, outline=VIOLET_DIM, width=3)
    dots = [RED, AMBER, GREEN]
    for i, c in enumerate(dots):
        d.ellipse([x + 24 + i * 34, y + 18, x + 44 + i * 34, y + 38], fill=c)
    fnt = font(FONT_MONO, 34)
    full = "\n".join(lines)
    nch = int((t - t0) * cps)
    shown = full[:max(0, nch)]
    # syntax tint: strings amber, comments muted, keywords violet
    yy = y + 62
    li = 0
    for ln in shown.split("\n"):
        xx = x + 34
        # crude token coloring
        if ln.strip().startswith("#"):
            d.text((xx, yy), ln, font=fnt, fill=MUTED)
        else:
            # highlight quoted strings
            parts, cur, in_s, q = [], "", False, ""
            for ch in ln:
                if ch in "\"'" and not in_s:
                    if cur:
                        parts.append((cur, False)); cur = ""
                    in_s, q = True, ch; cur = ch
                elif in_s and ch == q:
                    cur += ch; parts.append((cur, True)); cur = ""; in_s = False
                else:
                    cur += ch
            if cur:
                parts.append((cur, in_s))
            for txt, is_str in parts:
                d.text((xx, yy), txt, font=fnt,
                       fill=AMBER if is_str else (235, 235, 245))
                tw, _ = text_size(d, txt, fnt)
                xx += tw
        yy += 52
        li += 1
    # cursor
    if int(t * 2.5) % 2 == 0 and nch < len(full):
        d.rectangle([x + 34 + (text_size(d, shown.split(chr(10))[-1], fnt)[0] if shown else 0),
                     yy - 52, x + 52 + (text_size(d, shown.split(chr(10))[-1], fnt)[0] if shown else 0),
                     yy - 12], fill=GREEN)
    return nch >= len(full)

def ingredients_frame(img, t):
    # t: 6-24 content-local; lt = local
    lt = t - 8
    d = ImageDraw.Draw(img)
    bg_particles(d, t)
    pop_text(img, d, W / 2, 120, "INGREDIENTS = CODE", 64, WHITE, 8.2, t)
    code_panel(d, 110, 230, 830, ING_LINES, t, 9.0, cps=30)
    # pot on the right, fills as lines complete
    cx, base_y = 1450, 880
    fill = clamp01((lt - 4) / 10)
    draw_pot(d, cx, base_y, 380, 300, lid_open=0, fill_level=fill, t=t)
    # ingredient icons pop in with stagger
    items = [("RICE", (245, 235, 200), 11.0), ("MASALAY", AMBER, 14.5), ("CHICKEN", (255, 170, 130), 18.0)]
    for name, col, t0 in items:
        if t >= t0:
            p = spring((t - t0) / 0.4)
            k = ease_out_cubic(min(1.0, (t - t0) / 0.9))
            yy = 300 + (560 - 300) * k
            fnt = font(FONT_BOLD, 44)
            tw, th = text_size(d, name, fnt)
            sc = 0.6 + 0.4 * p
            tmp = Image.new("RGBA", (tw + 60, th + 60), (0, 0, 0, 0))
            ImageDraw.Draw(tmp).text((30, 30), name, font=fnt, fill=col + (255,))
            tmp = tmp.resize((int(tmp.width * sc), int(tmp.height * sc)), Image.BILINEAR)
            img.alpha_composite(tmp, (int(cx - tmp.width / 2), int(yy)))
    # rice grains burst when fill grows
    if 11.0 < t < 20:
        rng = np.random.default_rng(8)
        for i in range(40):
            ph = ((t - 11.0) * 1.4 + i * 0.13) % 1.0
            sx = 400 + rng.uniform(-160, 160)
            x = sx + (cx - sx) * ease_in_out(ph)
            y = 320 + (620 - 320) * ph * ph
            r = 7 * (1 - ph * 0.4)
            d.ellipse([x - r, y - r * 0.5, x + r, y + r * 0.5], fill=(245, 235, 200))

# ================= RECIPE (24-42) =================
FUNCS = [
    ("def fry_onions():", '    return "golden brown"', "ONIONS: golden brown", 24.5),
    ("def layer_rice():", "    for i in range(3):\n        add_layer(rice, masalay)", "LAYERS: 3", 29.5),
    ("def dum():", "    lid.close()\n    wait(minutes=20)", "LID: closed", 34.5),
]

def recipe_frame(img, t):
    lt = t - 24
    d = ImageDraw.Draw(img)
    bg_particles(d, t)
    pop_text(img, d, W / 2, 110, "RECIPE = FUNCTIONS", 64, WHITE, 24.2, t)
    # three function cards
    for i, (sig, body, result, t0) in enumerate(FUNCS):
        x = 140 + i * 590
        y = 240
        if t < t0:
            continue
        p = spring((t - t0) / 0.4)
        yy = y + (1 - p) * 60
        d.rounded_rectangle([x, yy, x + 520, yy + 420], radius=22,
                            fill=PANEL, outline=VIOLET if t > t0 + 5 else VIOLET_DIM, width=4)
        fnt = font(FONT_MONO_B, 32)
        d.text((x + 30, yy + 30), sig, font=fnt, fill=VIOLET)
        fb = font(FONT_MONO, 28)
        byy = yy + 90
        for ln in body.split("\n"):
            d.text((x + 30, byy), ln, font=fb, fill=(235, 235, 245))
            byy += 48
        # >>> execution line
        et = t0 + 3.2
        if t >= et:
            d.text((x + 30, yy + 300), ">>> " + sig[4:].split("(")[0] + "()",
                   font=fb, fill=GREEN)
        if t >= et + 1.2:
            d.text((x + 30, yy + 352), result, font=font(FONT_BOLD, 30),
                   fill=AMBER)
    # running dots footer
    if t > 25:
        fnt = font(FONT_MONO, 34)
        dots = "." * (1 + int(t * 2) % 3)
        draw_centered(d, W / 2, 920, "running recipe" + dots, fnt, MUTED)

# ================= COOKING (42-60) =================
def cooking_frame(img, t):
    lt = t - 40
    d = ImageDraw.Draw(img)
    bg_particles(d, t, n=40)
    pop_text(img, d, W / 2, 100, "THE COMPILER IS MY STOVE", 58, WHITE, 40.2, t)
    cx, base_y = W / 2, 740
    # pot first, then flames licking around its base
    d = ImageDraw.Draw(img)
    d.rectangle([cx - 260, 800, cx + 260, 826], fill=(60, 60, 72),
                outline=VIOLET_DIM, width=2)
    draw_pot(d, cx, base_y, 460, 330, lid_open=0, fill_level=1.0, t=t)
    draw_flames(img, d, cx, 815, 540, t)
    draw_steam(img, d, cx, base_y - 420, t, n=16)
    # fake compile terminal (left)
    d.rounded_rectangle([90, 560, 560, 980], radius=18, fill=PANEL,
                        outline=VIOLET_DIM, width=3)
    fnt = font(FONT_MONO, 30)
    lines = [("$ gcc stove.c -o dinner", GREEN),
             ("compiling masala...", WHITE),
             ("rendering rice layers...", WHITE),
             ("linking dum...", WHITE)]
    yy = 610
    for i, (ln, col) in enumerate(lines):
        if lt > 1 + i * 2.2:
            d.text((120, yy), ln, font=fnt, fill=col)
            yy += 56
    if lt > 10:
        d.text((120, yy), "[OK] dinner ready", font=fnt, fill=GREEN)
    # dum progress bar (right)
    d.rounded_rectangle([1360, 560, 1830, 980], radius=18, fill=PANEL,
                        outline=VIOLET_DIM, width=3)
    draw_centered(d, 1595, 610, "DUM", font(FONT_BOLD, 54), AMBER)
    bp = clamp01((lt - 2) / 14)
    bw, bh = 380, 54
    bx, by = 1595 - bw / 2, 720
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=14, fill=(30, 30, 40))
    fw = bw * bp
    if fw > 30:
        d.rounded_rectangle([bx, by, bx + fw, by + bh], radius=14, fill=VIOLET)
    draw_centered(d, 1595, by + bh + 30, "%d%%" % int(bp * 100),
                  font(FONT_MONO_B, 44), WHITE)
    # countdown 3-2-1 at the end
    if lt > 15.5:
        n = 3 - int((lt - 15.5) / 0.8)
        if n >= 1:
            pop_text(img, d, W / 2, 880, str(n), 130, GOLD, t - 0.01, t, glow=True)

# ================= PUNCHLINE (60-70) =================
def punchline_frame(img, t):
    lt = t - 57
    d = ImageDraw.Draw(img)
    bg_particles(d, t)
    cx, base_y = W / 2, 700
    # lid opens at lt=1
    lid_k = clamp01((lt - 1.0) / 0.8)
    lid_info = draw_pot(d, cx, base_y, 380, 270, lid_open=lid_k, fill_level=1.0, t=t)
    if lid_info:
        lx, ly, ltmp = lid_info
        img.alpha_composite(ltmp, (int(lx - ltmp.width / 2), int(ly)))
    # golden light burst from pot
    if lid_k > 0:
        k = ease_out_cubic(lid_k)
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([cx - 250 * k, base_y - 600 * k, cx + 250 * k, base_y - 60],
                   fill=(255, 200, 90, int(110 * k)))
        glow = glow.filter(ImageFilter.GaussianBlur(50))
        img.alpha_composite(glow)
    # the rendered FRAME rises out (not biryani!)
    if lt > 1.6:
        k = ease_out_cubic((lt - 1.6) / 1.6)
        fw2, fh2 = 480, 280
        fy = 600 - 140 * k
        # glow behind frame
        fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(fl).rectangle([cx - fw2 / 2 - 24, fy - fh2 / 2 - 24,
                                      cx + fw2 / 2 + 24, fy + fh2 / 2 + 24],
                                     fill=(255, 200, 90, int(140 * k)))
        fl = fl.filter(ImageFilter.GaussianBlur(36))
        img.alpha_composite(fl)
        d = ImageDraw.Draw(img)
        d.rectangle([cx - fw2 / 2, fy - fh2 / 2, cx + fw2 / 2, fy + fh2 / 2],
                    fill=(20, 20, 30), outline=GOLD, width=6)
        # mini biryani-ish art inside the frame (code-drawn)
        for gi in range(26):
            gx = cx - fw2 / 2 + 40 + (gi * 197) % (fw2 - 80)
            gy = fy + 40 + (gi * 131) % (fh2 - 120)
            d.ellipse([gx - 9, gy - 4, gx + 9, gy + 4], fill=(245, 235, 200))
        d.text((cx - fw2 / 2 + 24, fy + fh2 / 2 - 66), "frame_0042.png",
               font=font(FONT_MONO, 30), fill=GOLD)
    # punchline text beats
    pop_text(img, d, W / 2, 80, "It's not biryani.", 72, WHITE, 59.2, t)
    pop_text(img, d, W / 2, 180, "It's a RENDERED FRAME.", 72, GOLD, 61.0, t, glow=True)
    if lt > 6.0:
        p = ease_out_cubic((lt - 6.0) / 0.6)
        d2 = ImageDraw.Draw(img)
        fnt = font(FONT_BOLD, 52)
        for i, s in enumerate(["Taste? 10/10.", "Calories? Zero."]):
            tw, _ = text_size(d2, s, fnt)
            a = int(255 * p)
            d2.text((W / 2 - tw / 2, 830 + i * 72 + (1 - p) * 40), s, font=fnt,
                    fill=(255, 255, 255, a))
        draw_centered(d2, W / 2, 1000, "because it's code.",
                      font(FONT_MONO_B, 40), VIOLET + (int(255 * p),))

# ================= main =================
def render_frame(f):
    t = f / FPS
    img = canvas().convert("RGBA")
    if t < 8:
        hook_frame(img, t)
    elif t < 24:
        ingredients_frame(img, t)
    elif t < 40:
        recipe_frame(img, t)
    elif t < 57:
        cooking_frame(img, t)
    else:
        punchline_frame(img, t)
    img = apply_vignette(img.convert("RGB")).convert("RGBA")
    return img

def main(f0=0, f1=None):
    import time
    t0 = time.time()
    f1 = NF if f1 is None else f1
    for f in range(f0, f1):
        img = render_frame(f)
        img.convert("RGB").save(f"{OUT}/f{f:05d}.png")
        if f % 300 == 0:
            print(f"frame {f}/{NF} ({time.time()-t0:.0f}s)", flush=True)
    print("render done", flush=True)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        for ts in [float(x) for x in sys.argv[2:]]:
            img = render_frame(int(ts * FPS))
            img.convert("RGB").save(f"/tmp/ep4_t{ts:.1f}.png")
            print("saved", ts, flush=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "range":
        main(int(sys.argv[2]), int(sys.argv[3]))
    else:
        main()
