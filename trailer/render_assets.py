"""CodeToVideo brand assets: intro bumper (4s), outro (7s), subscribe bell (3.5s, alpha)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from lib import *
from PIL import Image, ImageDraw

BASE = os.path.expanduser("~/workspace/imagine_media/ai-video-channel")

def save_frames(frames, subdir):
    out = os.path.join(BASE, "trailer", subdir)
    os.makedirs(out, exist_ok=True)
    for i, img in enumerate(frames):
        img.save(f"{out}/f{i:05d}.png")
    print(subdir, len(frames), "frames")

# ================= INTRO BUMPER 4s =================
def intro_bumper():
    frames = []
    N = 4 * FPS
    for i in range(N):
        t = i / FPS
        img = canvas(); d = ImageDraw.Draw(img, "RGBA")
        cx, cy = W / 2, H / 2 - 60
        # glow build
        gp = ease_out_cubic(prog(i, 0, 0.6))
        for r, al in [(320, 26), (230, 40), (150, 55)]:
            d.ellipse([cx - r * gp, cy - r * gp, cx + r * gp, cy + r * gp],
                      fill=VIOLET + (int(al * gp),))
        # </> strokes
        lw = 40
        dp = prog(i, 0.6, 1.8)
        x1 = cx - 170
        d.line([(x1 + 100 * dp, cy - 125), (x1, cy)], fill=VIOLET, width=lw)
        if dp > 0.5:
            p2 = (dp - 0.5) * 2
            d.line([(x1, cy), (x1 + 100 * p2, cy + 125)], fill=VIOLET, width=lw)
        sp2 = prog(i, 1.3, 2.1)
        if sp2 > 0:
            d.line([(cx + 45, cy - 125 * sp2), (cx - 45, cy + 125 * sp2)],
                   fill=WHITE, width=lw)
        # play triangle morph
        pp = spring(prog(i, 2.0, 2.8))
        if pp > 0:
            s = 150 * pp
            d.polygon([(cx + 70, cy - s), (cx + 70, cy + s), (cx + 70 + s * 1.5, cy)],
                      fill=VIOLET)
        # burst particles on morph hit
        if 2.0 < t < 2.7:
            for k in range(28):
                ang = k * 0.224 + t * 2
                rr = (t - 2.0) * 800
                x = cx + rr * math.cos(ang); y = cy + rr * math.sin(ang)
                d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=WHITE + (170,))
        # wordmark
        wp = ease_out_cubic(prog(i, 2.6, 3.2))
        draw_centered(d, cx, cy + 200, "CodeToVideo", font(FONT_BOLD, 96),
                      WHITE, int(255 * wp))
        # fade out
        if t > 3.5:
            fo = prog(i, 3.5, 4.0)
            d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * fo)))
        frames.append(img.convert("RGB"))
    return frames

# ================= OUTRO 7s =================
def outro():
    frames = []
    N = 7 * FPS
    for i in range(N):
        t = i / FPS
        img = canvas(); d = ImageDraw.Draw(img, "RGBA")
        # tagline kinetic
        tp = spring(prog(i, 0.1, 0.9))
        if tp > 0.03:
            f = font(FONT_BOLD, int(92 * tp))
            draw_centered(d, W / 2, 180, "Watch code become video.", f, VIOLET)
        # subscribe pill + bell
        bp = spring(prog(i, 1.0, 1.8))
        if bp > 0.05:
            pw, ph = int(460 * bp), int(120 * bp)
            px0, py0 = W / 2 - pw / 2, 360
            d.rounded_rectangle([px0, py0, px0 + pw, py0 + ph], radius=ph // 2,
                                fill=(200, 30, 40))
            if bp > 0.85:
                # bell icon left
                bx, by = px0 + 70, py0 + ph / 2
                d.ellipse([bx - 26, by - 30, bx + 26, by + 10], outline=WHITE, width=7)
                d.polygon([(bx - 26, by - 26), (bx + 26, by - 26), (bx, by - 52)], fill=WHITE)
                d.ellipse([bx - 8, by + 16, bx + 8, by + 32], fill=WHITE)
                draw_centered(d, W / 2 + 40, py0 + ph / 2 - 30, "SUBSCRIBE",
                              font(FONT_BOLD, 54), WHITE)
        # cursor click at 2.2
        if 2.0 < t < 2.6:
            cp = prog(i, 2.0, 2.3)
            s = 1 - 0.25 * math.sin(cp * math.pi)
            cx, cy = W / 2 + 180, 420
            d.polygon([(cx, cy), (cx, cy + 44 * s), (cx + 16 * s, cy + 32 * s),
                       (cx + 10 * s, cy + 22 * s)], fill=WHITE)
            if 2.25 < t < 2.6:
                rr = (t - 2.25) * 500
                d.ellipse([W/2 - rr, 420 - rr, W/2 + rr, 420 + rr],
                          outline=VIOLET + (int(140 * (1 - rr / 180)),), width=5)
        # next-up panel
        np_ = ease_out_cubic(prog(i, 2.8, 3.5))
        if np_ > 0:
            pw2, ph2 = 900, 300
            px = W / 2 - pw2 / 2
            py = 560 + (1 - np_) * 120
            d.rounded_rectangle([px, py, px + pw2, py + ph2], radius=24,
                                fill=(18, 18, 26, int(255 * np_)))
            d.rounded_rectangle([px, py, px + pw2, py + ph2], radius=24,
                                outline=VIOLET + (int(120 * np_),), width=3)
            draw_centered(d, W / 2, py + 50, "NEXT UP", font(FONT_MONO_B, 36),
                          VIOLET, int(255 * np_))
            draw_centered(d, W / 2, py + 120, "Next build drops Friday",
                          font(FONT_REG, 44), WHITE, int(255 * np_))
            draw_centered(d, W / 2, py + 190, "youtube.com/@CodeToVideo",
                          font(FONT_MONO, 32), MUTED, int(255 * np_))
        if t > 6.3:
            fo = prog(i, 6.3, 7.0)
            d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * fo)))
        frames.append(img.convert("RGB"))
    return frames

# ================= SUBSCRIBE BELL 3.5s (alpha) =================
def sub_bell():
    frames = []
    N = int(3.5 * FPS)
    PW, PH = 560, 130
    for i in range(N):
        t = i / FPS
        img = canvas(alpha=True); d = ImageDraw.Draw(img, "RGBA")
        # slide in from right, hold, slide out
        if t < 0.5:
            xp = ease_out_cubic(t / 0.5)
        elif t < 2.6:
            xp = 1.0
        else:
            xp = 1 - ease_in_cubic((t - 2.6) / 0.9)
        # pill positioned lower-right area, x from offscreen to target
        tx = W - PW - 120
        x0 = tx + (1 - xp) * (PW + 300)
        y0 = H - PH - 140
        a = int(235 * min(1, xp * 1.5))
        d.rounded_rectangle([x0, y0, x0 + PW, y0 + PH], radius=PH // 2,
                            fill=(16, 16, 22, a))
        d.rounded_rectangle([x0, y0, x0 + PW, y0 + PH], radius=PH // 2,
                            outline=VIOLET + (a,), width=3)
        # bell icon with ring wiggle
        bx, by = x0 + 75, y0 + PH / 2
        wig = 0
        if 0.6 < t < 1.6:
            wig = math.sin((t - 0.6) * 18) * 14 * (1 - (t - 0.6))
        # draw bell rotated approx by offsetting
        ox = wig
        d.ellipse([bx - 24 + ox, by - 28, bx + 24 + ox, by + 8], outline=VIOLET + (a,), width=6)
        d.polygon([(bx - 24 + ox, by - 24), (bx + 24 + ox, by - 24), (bx + ox, by - 48)],
                  fill=VIOLET + (a,))
        d.ellipse([bx - 7 + ox, by + 14, bx + 7 + ox, by + 28], fill=VIOLET + (a,))
        # ring waves
        if 0.6 < t < 1.6:
            for k in range(2):
                rr = ((t - 0.6) * 160 + k * 45) % 110
                aa = int(120 * (1 - rr / 110) * min(1, xp))
                d.ellipse([bx - rr, by - rr, bx + rr, by + rr],
                          outline=VIOLET + (aa,), width=3)
        d.text((x0 + 130, y0 + PH / 2 - 26), "Subscribe", font=font(FONT_BOLD, 52),
               fill=WHITE + (a,))
        frames.append(img)
    return frames

if __name__ == "__main__":
    save_frames(intro_bumper(), "frames_intro")
    save_frames(outro(), "frames_outro")
    save_frames(sub_bell(), "frames_bell")
    print("ALL ASSETS DONE")
