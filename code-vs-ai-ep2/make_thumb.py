"""EP2 thumbnail 1280x720."""
import math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, "/home/hatch/workspace/imagine_media/ai-video-channel/trailer")
from lib import W, H, VIOLET, WHITE, MUTED, font, text_size, draw_centered, FONT_BOLD, FONT_MONO_B

TW, TH = 1280, 720
img = Image.new("RGB", (TW, TH), (8, 8, 14))
d = ImageDraw.Draw(img)

# night sky gradient
for y in range(TH):
    t = y / TH
    c = (int(8 + 14 * t), int(8 + 22 * t), int(26 + 30 * t))
    d.line([(0, y), (TW, y)], fill=c)

# stars
rng = np.random.default_rng(7)
for _ in range(120):
    x, y = rng.uniform(0, TW), rng.uniform(0, 420)
    b = int(140 + 100 * rng.uniform())
    d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(b, b, b + 15))

# moon
d.ellipse([1050, 60, 1180, 190], fill=(235, 240, 250))

# snow ground
d.polygon([(0, 560), (TW, 520), (TW, TH), (0, TH)], fill=(52, 68, 100))

# radio tower (right side)
tx = 1010
d.polygon([(tx - 70, 600), (tx + 70, 600), (tx + 20, 240), (tx - 20, 240)], fill=(12, 14, 24))
for yy in range(260, 580, 40):
    wf = (yy - 240) / 360
    hw = 20 + wf * 50
    d.line([(tx - hw, yy), (tx + hw, yy)], fill=(30, 34, 52), width=4)
d.line([(tx, 240), (tx, 150)], fill=(12, 14, 24), width=8)
# beacon + rings
d.ellipse([tx - 12, 138, tx + 12, 162], fill=(255, 80, 80))
for k, rr in enumerate([50, 95, 140]):
    d.ellipse([tx - rr, 150 - rr // 2, tx + rr, 150 + rr // 2],
              outline=(139, 92, 246, 200 - k * 55), width=5)

# snow dots
for _ in range(160):
    x, y = rng.uniform(0, TW), rng.uniform(0, TH)
    r = rng.uniform(1.5, 4)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 240, 252))

# left text block
img_r = img.convert("RGBA")
d = ImageDraw.Draw(img_r)

def glow(cx, y, s, fnt, fill, gc=VIOLET):
    tw, th = text_size(d, s, fnt)
    lay = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((cx - tw / 2, y), s, font=fnt, fill=gc + (150,))
    lay = lay.filter(ImageFilter.GaussianBlur(16))
    img_r.alpha_composite(lay)
    ImageDraw.Draw(img_r).text((cx - tw / 2, y), s, font=fnt, fill=fill)

f1 = font(FONT_BOLD, 118)
glow(430, 130, "PURE CODE", f1, WHITE + (255,))
f2 = font(FONT_BOLD, 54)
d2 = ImageDraw.Draw(img_r)
for i, s in enumerate(["I built an 80s anime scene", "with ZERO AI"]):
    tw, _ = text_size(d2, s, f2)
    d2.text((430 - tw / 2, 300 + i * 72), s, font=f2, fill=(225, 225, 240, 255))

# violet badge
f3 = font(FONT_MONO_B, 40)
s = "1800 FRAMES RENDERED LOCALLY"
tw, _ = text_size(d2, s, f3)
d2.rounded_rectangle([430 - tw / 2 - 34, 480, 430 + tw / 2 + 34, 480 + 84],
                     radius=42, fill=VIOLET + (255,))
d2.text((430 - tw / 2, 496), s, font=f3, fill=(255, 255, 255, 255))

out = img_r.convert("RGB")
out.save("/home/hatch/workspace/imagine_media/ai-video-channel/code-vs-ai-ep2-thumbnail-1280x720.png")
print("thumbnail saved")
