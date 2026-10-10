"""CodeToVideo 'Code vs AI' EP1 — 5-beat structure.
Beat 1: Hook (kinetic text) | Beat 2: The reveal (anime night scene)
Beat 3: Split-screen AI vs CODE | Beat 4: Terminal proof | Beat 5: CTA
Reuses trailer/lib.py helpers.
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.expanduser("~/workspace/imagine_media/ai-video-channel/trailer"))
from lib import (W, H, FPS, BG, VIOLET, VIOLET_DIM, WHITE, MUTED, CODE_BG,
                 font, FONT_BOLD, FONT_REG, FONT_MONO, FONT_MONO_B,
                 clamp01, ease_out_cubic, ease_in_cubic, ease_in_out, prog,
                 canvas, text_size, draw_centered, glow_text, Particles)

OUT = os.path.expanduser("~/workspace/imagine_media/ai-video-channel/code-vs-ai")
os.makedirs(OUT + "/frames", exist_ok=True)

RED = (235, 90, 90)
RED_DIM = (120, 45, 45)
GREEN = (110, 230, 140)
VIOLET_SOFT = (170, 130, 255)

# ---------- beat durations (main content only) ----------
B1 = 8.0    # hook
B2 = 16.0   # reveal
B3 = 14.0   # split screen
B4 = 14.0   # terminal
B5 = 8.0    # CTA
TOTAL = B1 + B2 + B3 + B4 + B5  # 60s

def t_of(beat_start, beat_dur, frame):
    return prog(frame, beat_start, beat_start + beat_dur)

# ================= BEAT 1: HOOK =================
def beat1(frame):
    img = canvas()
    d = ImageDraw.Draw(img)
    t = t_of(0, B1, frame)
    # line 1
    p1 = ease_out_cubic(prog(frame, 0.5, 2.0))
    if p1 > 0:
        f = font(FONT_BOLD, 64)
        a = int(255 * p1)
        y = 400 + int(40 * (1 - p1))
        draw_centered(d, W//2, y, "Everyone's using AI", f, WHITE, a)
        draw_centered(d, W//2, y + 84, "to generate video.", f, WHITE, a)
    # line 2 (punch)
    p2 = ease_out_cubic(prog(frame, 3.0, 4.2))
    if p2 > 0:
        f = font(FONT_BOLD, 76)
        a = int(255 * p2)
        sc = 0.85 + 0.15 * p2
        y = 640 + int(50 * (1 - p2))
        # draw scaled-ish via bigger font is complex; just fade+rise
        img2 = glow_text(img, W//2, y, "But watch what", f, WHITE)
        d = ImageDraw.Draw(img2); img = img2
        draw_centered(d, W//2, y, "But watch what", f, WHITE, a)
        img = glow_text(img, W//2, y + 96, "PURE CODE can do.", f, VIOLET_SOFT)
        d = ImageDraw.Draw(img)
        draw_centered(d, W//2, y + 96, "PURE CODE can do.", f, VIOLET_SOFT, a)
    # particles drift
    return img

# ================= BEAT 2: REVEAL (anime night scene) =================
_stars = None
def get_stars():
    global _stars
    if _stars is None:
        rng = np.random.default_rng(11)
        _stars = [(rng.uniform(0, W), rng.uniform(0, 620), rng.uniform(1, 3),
                   rng.uniform(0, 2*math.pi)) for _ in range(140)]
    return _stars

def beat2(frame, particles):
    t_abs = frame / FPS - B1
    img = canvas()
    d = ImageDraw.Draw(img)
    # sky gradient: deep blue-black
    for y in range(0, 700, 4):
        k = y / 700
        r = int(8 + 6*k); g = int(8 + 8*k); b = int(16 + 26*k)
        d.rectangle([0, y, W, y+4], fill=(r, g, b))
    # stars twinkle
    for x, y, r, ph in get_stars():
        tw = 0.35 + 0.65 * abs(math.sin(t_abs*1.4 + ph))
        a = int(220 * tw)
        d.ellipse([x-r, y-r, x+r, y+r], fill=(255,255,255,a))
    # moon + glow
    mx, my, mr = 1560, 170, 70
    glow = Image.new("RGBA", (W,H), (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([mx-160, my-160, mx+160, my+160], fill=(200,200,230,28))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    d = ImageDraw.Draw(img)
    d.ellipse([mx-mr, my-mr, mx+mr, my+mr], fill=(235,235,245))
    # mountain layers (silhouettes)
    rng = np.random.default_rng(5)
    for layer, (col, base, amp) in enumerate([((16,18,30), 640, 90), ((10,11,20), 720, 70)]):
        pts = [(0, H)]
        for x in range(0, W+40, 40):
            y = base + math.sin(x*0.004 + layer*2.1)*amp + math.sin(x*0.013+layer)*amp*0.3
            pts.append((x, y))
        pts.append((W, H))
        d.polygon(pts, fill=col)
    # ground
    d.rectangle([0, 800, W, H], fill=(8, 8, 14))
    # searchlight tower (right side)
    tx, ty = 1620, 800
    d.rectangle([tx-14, ty-180, tx+14, ty], fill=(30,30,40))
    d.polygon([(tx-40,ty-180),(tx+40,ty-180),(tx+24,ty-150),(tx-24,ty-150)], fill=(45,45,60))
    # sweeping beam (volumetric)
    ang = math.sin(t_abs*0.55) * 0.9 - 0.35  # sweep
    beam_len = 1500
    bx = tx + math.cos(ang - math.pi/2) * 0  # origin at tower top
    oy = ty - 195
    # beam as translucent polygon
    spread = 0.16
    dirx, diry = math.cos(ang), math.sin(ang)
    # beam points up-left sweeping
    ex = tx + dirx*0 + math.cos(ang+math.pi)*0  # compute endpoint
    # simpler: beam from tower top toward angle
    px, py = math.sin(ang), -math.cos(ang)
    tipx, tipy = tx + px*beam_len, oy + py*beam_len
    perp_x, perp_y = -py, px
    w0, w1 = 26, 200
    beam = Image.new("RGBA", (W,H), (0,0,0,0))
    bd = ImageDraw.Draw(beam)
    bd.polygon([(tx+perp_x*w0, oy+perp_y*w0),(tx-perp_x*w0, oy-perp_y*w0),
                (tipx-perp_x*w1, tipy-perp_y*w1),(tipx+perp_x*w1, tipy+perp_y*w1)],
               fill=(139,92,246,85))
    beam = beam.filter(ImageFilter.GaussianBlur(16))
    img = Image.alpha_composite(img.convert("RGBA"), beam).convert("RGB")
    d = ImageDraw.Draw(img)
    # bright core line
    d.line([tx, oy, tipx, tipy], fill=(190,160,255), width=7)
    # lamp glow at tower
    d.ellipse([tx-20, oy-20, tx+20, oy+20], fill=(200,170,255))
    # barbed wire posts (foreground silhouettes)
    for i, px_ in enumerate([180, 560, 980, 1400]):
        ph_ = 150 + (i%2)*30
        d.rectangle([px_-8, 800-ph_, px_+8, 800], fill=(5,5,8))
        # wire sags between posts
    for i in range(3):
        x0, x1 = [180,560,980,1400][i], [180,560,980,1400][i+1]
        for wline in range(2):
            yb = 800 - 150 + wline*40
            pts = []
            for s_ in range(21):
                x = x0 + (x1-x0)*s_/20
                y = yb + math.sin(s_/20*math.pi)*26
                pts.append((x,y))
            d.line(pts, fill=(5,5,8), width=3)
    # falling snow (violet-white)
    if frame % 2 == 0:
        particles.burst(W//2, -20, 6, speed_lo=60, speed_hi=160, life_lo=4, life_hi=8,
                        size_lo=2, size_hi=5, violet_ratio=0.35)
        # drift handled via vel x in update
    particles.update(1/FPS, gravity=26, drag=0.999)
    # add slight wind
    alive = particles.life > 0
    particles.pos[alive, 0] += 22 * (1/FPS)
    layer = img.convert("RGBA")
    pd = ImageDraw.Draw(layer)
    particles.draw(pd)
    img = layer.convert("RGB")
    d = ImageDraw.Draw(img)
    # caption (appears mid-beat)
    p = ease_out_cubic(prog(frame, B1+11, B1+13))
    if p > 0:
        f = font(FONT_BOLD, 44)
        # backdrop strip
        a = int(200*p)
        d.rectangle([0, 880, W, 1010], fill=(0,0,0,a//2))
        draw_centered(d, W//2, 905, "Every frame. Every snowflake. Every beam.", f, WHITE, int(255*p))
        draw_centered(d, W//2, 955, "Written by hand. In code.", f, VIOLET_SOFT, int(255*p))
    return img

# ================= BEAT 3: SPLIT SCREEN =================
def x_mark(d, cx, cy, r, col, lw=10):
    d.line([cx-r, cy-r, cx+r, cy+r], fill=col, width=lw)
    d.line([cx-r, cy+r, cx+r, cy-r], fill=col, width=lw)

def check_mark(d, cx, cy, r, col, lw=10):
    d.line([cx-r, cy, cx-r//3, cy+r//2], fill=col, width=lw)
    d.line([cx-r//3, cy+r//2, cx+r, cy-r], fill=col, width=lw)

def beat3(frame):
    t = frame / FPS - (B1 + B2)
    img = canvas()
    d = ImageDraw.Draw(img)
    mid = W // 2
    # bg halves slide in
    pl = ease_out_cubic(prog(frame, B1+B2, B1+B2+1.0))
    pr = ease_out_cubic(prog(frame, B1+B2+0.25, B1+B2+1.25))
    d.rectangle([0, 0, int(mid*pl), H], fill=(26, 12, 14))
    d.rectangle([W-int(mid*pr), 0, W, H], fill=(14, 12, 26))
    d.line([mid, 0, mid, H], fill=(60,60,70), width=4)
    # VS badge
    pv = ease_out_cubic(prog(frame, B1+B2+1.0, B1+B2+1.6))
    if pv > 0:
        r = int(64*pv)
        d.ellipse([mid-r, 400-r, mid+r, 400+r], fill=VIOLET)
        f = font(FONT_BOLD, int(56*pv))
        draw_centered(d, mid, 400-int(28*pv), "VS", f, WHITE)
    # headers
    fh = font(FONT_BOLD, 72)
    if pl > 0.9:
        draw_centered(d, mid//2, 120, "AI MODEL", fh, RED)
    if pr > 0.9:
        draw_centered(d, mid + mid//2, 120, "PURE CODE", fh, VIOLET_SOFT)
    # rows
    ai_rows = ["Guesses what you want", "Costs credits per try", "Characters change every time"]
    code_rows = ["Exact - does what you tell it", "Free", "Unlimited", "Editable frame by frame"]
    fr = font(FONT_REG, 40)
    for i, row in enumerate(ai_rows):
        prw = ease_out_cubic(prog(frame, B1+B2+2.0+i*1.2, B1+B2+2.8+i*1.2))
        if prw > 0:
            y = 300 + i*130
            x = int(-400*(1-prw)) + 90
            x_mark(d, x, y+18, 22, RED)
            d.text((x+48, y), row, font=fr, fill=(255,255,255,int(255*prw)))
    for i, row in enumerate(code_rows):
        prw = ease_out_cubic(prog(frame, B1+B2+2.6+i*1.2, B1+B2+3.4+i*1.2))
        if prw > 0:
            y = 300 + i*130
            x = int(1080 + 500*(1-prw))
            check_mark(d, x, y+18, 22, GREEN)
            d.text((x+48, y), row, font=fr, fill=(255,255,255,int(255*prw)))
    return img

# ================= BEAT 4: TERMINAL PROOF =================
def beat4(frame):
    t = frame / FPS - (B1 + B2 + B3)
    img = canvas()
    d = ImageDraw.Draw(img)
    # terminal window
    tx0, ty0, tx1, ty1 = 260, 180, 1660, 900
    d.rounded_rectangle([tx0, ty0, tx1, ty1], radius=24, fill=(16,16,22))
    d.rounded_rectangle([tx0, ty0, tx1, ty1], radius=24, outline=(70,70,85), width=3)
    # title bar dots
    for i, c in enumerate([(235,90,90),(240,200,90),(110,230,140)]):
        d.ellipse([tx0+36+i*44, ty0+30, tx0+60+i*44, ty0+54], fill=c)
    fm = font(FONT_MONO, 38)
    # typed command
    cmd = "$ python3 render_scene.py --frames 2400"
    nch = int(ease_out_cubic(prog(frame, B1+B2+B3+0.5, B1+B2+B3+2.5)) * len(cmd))
    d.text((tx0+60, ty0+110), cmd[:nch], font=fm, fill=WHITE)
    if nch >= len(cmd) and (int(t*2) % 2 == 0):
        tw,_ = text_size(d, cmd, fm)
        d.rectangle([tx0+60+tw+8, ty0+114, tx0+60+tw+24, ty0+114+40], fill=VIOLET)
    # render log lines
    p2 = prog(frame, B1+B2+B3+3.0, B1+B2+B3+4.0)
    if p2 > 0:
        lines = [
            ("rendering frame", WHITE, "  640 / 2400", MUTED),
            ("rendering frame", WHITE, " 1280 / 2400", MUTED),
            ("rendering frame", WHITE, " 1920 / 2400", MUTED),
            ("rendering frame", WHITE, " 2400 / 2400", GREEN),
        ]
        # animate progress
        prog_n = int(ease_in_out(prog(frame, B1+B2+B3+3.0, B1+B2+B3+9.0)) * 4)
        for i in range(min(prog_n, 4)):
            txt, c1, num, c2 = lines[i]
            y = ty0 + 210 + i*72
            d.text((tx0+60, y), txt, font=fm, fill=c1)
            d.text((tx0+560, y), num, font=fm, fill=c2)
        # progress bar
        if prog_n >= 1:
            bw = tx1 - tx0 - 120
            frac = min(1.0, prog_n/4)
            d.rounded_rectangle([tx0+60, ty0+540, tx0+60+bw, ty0+580], radius=20, fill=(40,40,52))
            d.rounded_rectangle([tx0+60, ty0+540, tx0+60+int(bw*frac), ty0+580], radius=20, fill=VIOLET)
        if prog_n >= 4:
            p3 = ease_out_cubic(prog(frame, B1+B2+B3+9.5, B1+B2+B3+10.5))
            if p3 > 0:
                f = font(FONT_BOLD, 46)
                draw_centered(d, W//2, ty0+660, "done. 2400 frames, local machine.", f, GREEN, int(255*p3))
    # bottom strip
    p4 = ease_out_cubic(prog(frame, B1+B2+B3+10.5, B1+B2+B3+12.0))
    if p4 > 0:
        f = font(FONT_BOLD, 52)
        draw_centered(d, W//2, 950, "No credits. No watermark. No queue.", f, WHITE, int(255*p4))
    return img

# ================= BEAT 5: CTA =================
def beat5(frame):
    img = canvas()
    d = ImageDraw.Draw(img)
    p1 = ease_out_cubic(prog(frame, B1+B2+B3+B4+0.3, B1+B2+B3+B4+1.5))
    if p1 > 0:
        f = font(FONT_BOLD, 68)
        a = int(255*p1)
        draw_centered(d, W//2, 300, "The full code is in", f, WHITE, a)
        draw_centered(d, W//2, 390, "the description.", f, WHITE, a)
    p2 = ease_out_cubic(prog(frame, B1+B2+B3+B4+1.8, B1+B2+B3+B4+3.0))
    if p2 > 0:
        fm = font(FONT_MONO_B, 44)
        a = int(255*p2)
        # github pill
        txt = "github.com/Sehrish64/Codetovideo-"
        tw, th = text_size(d, txt, fm)
        px0 = W//2 - tw//2 - 40; px1 = W//2 + tw//2 + 40
        py0, py1 = 540, 540 + th + 44
        d.rounded_rectangle([px0, py0, px1, py1], radius=28, fill=(24,24,34))
        d.rounded_rectangle([px0, py0, px1, py1], radius=28, outline=VIOLET, width=4)
        d.text((W//2 - tw//2, py0+22), txt, font=fm, fill=VIOLET_SOFT+(a,))
    p3 = ease_out_cubic(prog(frame, B1+B2+B3+B4+3.5, B1+B2+B3+B4+4.7))
    if p3 > 0:
        f = font(FONT_BOLD, 56)
        img = glow_text(img, W//2, 740, "New builds every Friday.", f, WHITE)
        d = ImageDraw.Draw(img)
        draw_centered(d, W//2, 740, "New builds every Friday.", f, WHITE, int(255*p3))
    return img

# ================= MAIN =================
def main():
    particles = Particles(900)
    total_frames = int(TOTAL * FPS)
    print(f"rendering {total_frames} frames ({TOTAL}s)", flush=True)
    for f in range(total_frames):
        t = f / FPS
        if t < B1:
            img = beat1(f)
        elif t < B1+B2:
            img = beat2(f, particles)
        elif t < B1+B2+B3:
            img = beat3(f)
        elif t < B1+B2+B3+B4:
            img = beat4(f)
        else:
            img = beat5(f)
        img.save(f"{OUT}/frames/f_{f:05d}.png")
        if f % 150 == 0:
            print(f"  frame {f}/{total_frames}", flush=True)
    print("done", flush=True)

if __name__ == "__main__":
    main()
