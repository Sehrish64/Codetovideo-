"""CodeToVideo launch trailer — 36s @ 30fps, 1920x1080."""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from lib import *
from PIL import Image, ImageDraw

OUT = os.path.expanduser("~/workspace/imagine_media/ai-video-channel/trailer/frames_trailer")
os.makedirs(OUT, exist_ok=True)
DUR = 36.0
NFRAMES = int(DUR * FPS)

TOTAL_CHARS = code_total_chars()

def draw_orbit_rings(draw, t, cx, cy, base_r=120, rings=3):
    for i in range(rings):
        r = base_r + i * 70 + 20 * math.sin(t * 1.5 + i)
        w = 3
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=VIOLET + (110,), width=w)
        # orbiting dots
        for k in range(3):
            a = t * (0.8 + 0.25 * i) + k * 2.09 + i
            x = cx + r * math.cos(a); y = cy + r * math.sin(a)
            draw.ellipse([x - 7, y - 7, x + 7, y + 7], fill=VIOLET)
    draw.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=VIOLET)
    draw.polygon([(cx - 9, cy - 14), (cx - 9, cy + 14), (cx + 13, cy)], fill=BG)

def draw_wave_layers(draw, t, x0, y0, w, h, layers=4):
    for L in range(layers):
        pts = []
        amp = h * (0.28 - L * 0.045)
        ymid = y0 + h / 2
        for x in range(0, w, 6):
            y = ymid + amp * math.sin(x * 0.02 + t * (2.2 + L * 0.5) + L * 1.3)
            pts.append((x0 + x, y))
        col = VIOLET if L % 2 == 0 else (200, 170, 255)
        draw.line(pts, fill=col + (200 - L * 30,), width=4)

def draw_bar_viz(draw, t, x0, y0, w, h, bars=28):
    bw = w / bars
    for i in range(bars):
        v = 0.5 + 0.5 * math.sin(t * 3.0 + i * 0.55) * math.sin(t * 1.1 + i * 0.2)
        bh = max(6, v * h)
        x = x0 + i * bw + 3
        y = y0 + h - bh
        c = VIOLET if i % 3 else WHITE
        draw.rounded_rectangle([x, y, x + bw - 6, y0 + h], radius=4, fill=c)

def card(draw, frame, t0, title, sub, accent=True):
    """Full-screen kinetic series card."""
    t = frame / FPS - t0
    img = None
    # slide-in title
    p = ease_out_cubic(prog(frame, t0, t0 + 0.5))
    # exit
    ex = ease_in_cubic(prog(frame, t0 + 2.6, t0 + 3.0))
    yoff = (1 - p) * 160 + ex * -160
    alpha = int(255 * (1 - ex))
    f_big = font(FONT_BOLD, 120)
    f_sub = font(FONT_REG, 44)
    tw, th = text_size(draw, title, f_big)
    cx = W / 2
    y = H / 2 - 90 + yoff
    # violet underline bar grows
    bp = ease_out_cubic(prog(frame, t0 + 0.3, t0 + 0.8))
    draw_centered(draw, cx, y, title, f_big, WHITE, alpha)
    bar_w = tw * bp
    draw.rectangle([cx - bar_w / 2, y + th + 26, cx + bar_w / 2, y + th + 38],
                   fill=VIOLET + (alpha,))
    sp = ease_out_cubic(prog(frame, t0 + 0.5, t0 + 1.0))
    draw_centered(draw, cx, y + th + 80 + (1 - sp) * 60, sub, f_sub,
                  MUTED, int(alpha * sp))

def render_frame(i):
    t = i / FPS
    img = canvas()
    d = ImageDraw.Draw(img, "RGBA")
    parts = Particles(900, seed=11)

    # ---------- 0.0 - 6.2 : HOOK : code typing -> render flash ----------
    if t < 6.2:
        # fade in
        fi = ease_out_cubic(prog(i, 0, 0.8))
        # terminal window
        wx0, wy0, wx1, wy1 = 240, 180, 1680, 900
        d.rounded_rectangle([wx0, wy0, wx1, wy1], radius=18, fill=CODE_BG + (int(255 * fi),))
        d.rounded_rectangle([wx0, wy0, wx1, wy0 + 64], radius=18, fill=(24, 24, 30) + (int(255 * fi),))
        d.rectangle([wx0, wy0 + 40, wx1, wy0 + 64], fill=(24, 24, 30) + (int(255 * fi),))
        for ci, cc in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse([wx0 + 28 + ci * 34, wy0 + 20, wx0 + 48 + ci * 34, wy0 + 40],
                      fill=cc + (int(255 * fi),))
        draw_centered(d, (wx0 + wx1) / 2, wy0 + 14, "intro.tsx  —  codetovideo",
                      font(FONT_MONO, 22), MUTED, int(255 * fi))
        # typing
        if t > 0.8:
            chars = int((t - 0.8) * 52)
            render_code_frame(d, min(chars, TOTAL_CHARS), x0=wx0 + 60, y0=wy0 + 110,
                              line_h=50, font_size=32)
        # render bar 5.0-5.8
        if 5.0 <= t < 5.8:
            rp = prog(i, 5.0, 5.8)
            bx0, bx1 = 560, 1360
            d.rounded_rectangle([bx0, 940, bx1, 972], radius=16, fill=(30, 30, 38))
            d.rounded_rectangle([bx0, 940, bx0 + (bx1 - bx0) * ease_in_out(rp), 972],
                                radius=16, fill=VIOLET)
            draw_centered(d, W / 2, 985, "RENDERING", font(FONT_MONO_B, 26), WHITE)
        # flash
        if 5.8 <= t < 6.2:
            fp = prog(i, 5.8, 6.2)
            flash = int(255 * (1 - fp))
            white = Image.new("RGB", (W, H), (flash, flash, flash))
            img = Image.blend(img, white, 1 - fp * 0.4)

    # ---------- 6.2 - 9.0 : particles -> formed animation ----------
    elif t < 9.0:
        st = t - 6.2
        # burst at start handled by continuous emission; draw forming rings
        fade = ease_out_cubic(prog(i, 6.2, 6.8))
        # particle burst ring expanding
        for k in range(3):
            rr = (st * 900 + k * 160) % 900
            a = int(120 * max(0, 1 - rr / 900))
            d.ellipse([W/2 - rr, H/2 - rr, W/2 + rr, H/2 + rr],
                      outline=VIOLET + (a,), width=5)
        draw_orbit_rings(d, st * 1.4, W / 2, H / 2 - 40, base_r=110)
        draw_wave_layers(d, st * 1.6, 240, 800, 1440, 160)
        if st > 0.9:
            p = ease_out_cubic(prog(i, 7.1, 7.8))
            img2 = glow_text(img, W / 2, 120, "THIS IS CODE", font(FONT_BOLD, 88),
                             WHITE, radius=22)
            img = img2
            d = ImageDraw.Draw(img, "RGBA")
        if st > 1.7:
            p = ease_out_cubic(prog(i, 7.9, 8.6))
            d.rectangle([0, 0, W, H], fill=(10, 10, 11, int(140 * p)))
            draw_centered(d, W / 2, H / 2 - 60, "BECOMING VIDEO",
                          font(FONT_BOLD, 110), VIOLET, int(255 * p))

    # ---------- 9.0 - 12.5 : split code | result ----------
    elif t < 12.5:
        st = t - 9.0
        sp = ease_out_cubic(prog(i, 9.0, 9.6))
        # left panel code
        d.rounded_rectangle([80, 200, 900, 880], radius=18, fill=CODE_BG)
        chars = int(st * 60)
        # mini snippet
        mini = [("// live build", "comment"), ("const x = spring(frame);", "plain"),
                ("circle(r * x);", "tag")]
        y = 280
        rem = chars
        f = font(FONT_MONO, 30)
        for tx, tok in mini:
            if rem >= len(tx):
                d.text((130, y), tx, font=f, fill=TOKEN_COLORS[tok]); rem -= len(tx)
            elif rem > 0:
                d.text((130, y), tx[:rem], font=f, fill=TOKEN_COLORS[tok]); rem = 0
            y += 56
        draw_centered(d, 490, 150, "CODE", font(FONT_MONO_B, 34), MUTED)
        # right panel result
        d.rounded_rectangle([1020, 200, 1840, 880], radius=18, fill=(16, 16, 22))
        draw_bar_viz(d, st * 1.5, 1080, 320, 700, 420)
        draw_centered(d, 1430, 150, "VIDEO", font(FONT_MONO_B, 34), VIOLET)
        # divider flash
        d.rectangle([948, 180, 956, 900], fill=VIOLET)
        if st > 2.6:
            p = ease_out_cubic(prog(i, 11.6, 12.2))
            draw_centered(d, W / 2, 920, "no timeline. no keyframes. just code.",
                          font(FONT_REG, 40), WHITE, int(255 * p))

    # ---------- 12.5 - 21.5 : three series cards ----------
    elif t < 21.5:
        cards = [
            (12.5, "RECREATE IT IN CODE", "Famous animations, rebuilt line by line"),
            (15.5, "CODE vs AI", "Hand-coded vs AI-generated. Scored."),
            (18.5, "THE VIDEO BUSINESS", "Real clients. Real money. Real workflow."),
        ]
        for t0, title, sub in cards:
            if t0 <= t < t0 + 3.0:
                card(d, i, t0, title, sub)
                break
        # bg deco rings
        rt = t * 0.6
        for k in range(2):
            rr = 500 + k * 220
            d.ellipse([W/2 - rr, H/2 - rr, W/2 + rr, H/2 + rr],
                      outline=VIOLET + (26,), width=3)

    # ---------- 21.5 - 25.0 : rapid montage pops ----------
    elif t < 25.0:
        st = t - 21.5
        pops = [
            (0.0, "rings"), (0.85, "wave"), (1.7, "bars"), (2.55, "orbs"),
        ]
        for pt, kind in pops:
            if pt <= st < pt + 0.85:
                lp = (st - pt) / 0.85
                a = int(255 * (1 - abs(lp - 0.4) * 2.2))
                a = max(0, min(255, a))
                s = 0.7 + 0.3 * ease_out_cubic(lp)
                cx, cy = W / 2, H / 2
                if kind == "rings":
                    for k in range(3):
                        rr = (60 + k * 90) * s
                        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                                  outline=VIOLET + (a,), width=6)
                elif kind == "wave":
                    draw_wave_layers(d, st * 4, 360, 380, 1200, 320)
                elif kind == "bars":
                    draw_bar_viz(d, st * 4, 560, 340, 800, 400)
                else:
                    for k in range(8):
                        ang = k * 0.785 + st * 2
                        x = cx + 260 * s * math.cos(ang); y = cy + 260 * s * math.sin(ang)
                        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=VIOLET + (a,))
                # code ghost behind
                d.rectangle([0, 0, W, H], fill=(10, 10, 11, 120))
                break

    # ---------- 25.0 - 29.0 : logo mark draws ----------
    elif t < 29.0:
        st = t - 25.0
        cx, cy = W / 2, H / 2 - 60
        # glow bg
        gp = ease_out_cubic(prog(i, 25.0, 26.0))
        for r, al in [(300, 30), (220, 45), (150, 60)]:
            d.ellipse([cx - r * gp, cy - r * gp, cx + r * gp, cy + r * gp],
                      fill=VIOLET + (int(al * gp),))
        # </> strokes draw
        dp = prog(i, 25.4, 26.6)
        lw = 34
        # left bracket <
        x1 = cx - 150
        d.line([(x1 + 90 * dp, cy - 110), (x1, cy)], fill=VIOLET, width=lw)
        if dp > 0.5:
            p2 = (dp - 0.5) * 2
            d.line([(x1, cy), (x1 + 90 * p2, cy + 110)], fill=VIOLET, width=lw)
        # slash /
        sp2 = prog(i, 26.2, 27.0)
        if sp2 > 0:
            d.line([(cx + 40, cy - 110 * sp2), (cx - 40, cy + 110 * sp2)],
                   fill=WHITE, width=lw)
        # play triangle morphs from right bracket
        pp = spring(prog(i, 27.0, 28.0))
        if pp > 0:
            s = 130 * pp
            d.polygon([(cx + 60, cy - s), (cx + 60, cy + s), (cx + 60 + s * 1.5, cy)],
                      fill=VIOLET)
        # particles on hit
        if 26.9 < t < 27.6:
            for k in range(24):
                ang = k * 0.26 + st
                rr = (t - 26.9) * 700
                x = cx + rr * math.cos(ang); y = cy + rr * math.sin(ang)
                d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=WHITE + (180,))

    # ---------- 29.0 - 36.0 : wordmark + CTA ----------
    else:
        st = t - 29.0
        # small logo mark top
        cx = W / 2
        ms = ease_out_cubic(prog(i, 29.0, 29.5))
        mr = 54 * ms
        if mr > 2:
            d.ellipse([cx - mr, 200 - mr, cx + mr, 200 + mr], fill=VIOLET)
            ps = mr * 0.42
            d.polygon([(cx - ps * 0.6, 200 - ps), (cx - ps * 0.6, 200 + ps),
                       (cx + ps, 200)], fill=BG)
        # wordmark kinetic
        wp = spring(prog(i, 29.3, 30.2))
        f_wm = font(FONT_BOLD, int(150 * max(0.01, wp)))
        if wp > 0.05:
            draw_centered(d, cx, 300, "CodeToVideo", f_wm, WHITE)
        # tagline
        tp = ease_out_cubic(prog(i, 30.4, 31.0))
        if tp > 0:
            img = glow_text(img, cx, 500, "Watch code become video.",
                            font(FONT_BOLD, 64), VIOLET, radius=16)
            d = ImageDraw.Draw(img, "RGBA")
        # friday line
        fp = ease_out_cubic(prog(i, 31.2, 31.7))
        draw_centered(d, cx, 620, "New builds every Friday",
                      font(FONT_REG, 44), MUTED, int(255 * fp))
        # subscribe pill
        bp = spring(prog(i, 31.8, 32.5))
        if bp > 0.05:
            pw, ph = int(420 * bp), int(110 * bp)
            px0, py0 = cx - pw / 2, 730
            d.rounded_rectangle([px0, py0, px0 + pw, py0 + ph], radius=ph // 2,
                                fill=(200, 30, 40))
            if bp > 0.8:
                draw_centered(d, cx, py0 + ph / 2 - 28, "SUBSCRIBE",
                              font(FONT_BOLD, 52), WHITE)
            # bell pulse rings
            if st > 3.4:
                for k in range(2):
                    rr = ((st - 3.4) * 300 + k * 90) % 220
                    a = int(100 * (1 - rr / 220))
                    d.ellipse([cx - rr, 785 - rr, cx + rr, 785 + rr],
                              outline=VIOLET + (a,), width=4)
        # fade out last 0.6s
        if t > 35.4:
            fo = prog(i, 35.4, 36.0)
            d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * fo)))

    # letterbox-safe: nothing drawn outside; return
    return img.convert("RGB")

if __name__ == "__main__":
    import time
    t0 = time.time()
    for i in range(NFRAMES):
        img = render_frame(i)
        img.save(f"{OUT}/f{i:05d}.png")
        if i % 120 == 0:
            print(f"frame {i}/{NFRAMES}  {time.time()-t0:.0f}s", flush=True)
    print("DONE", time.time() - t0)
