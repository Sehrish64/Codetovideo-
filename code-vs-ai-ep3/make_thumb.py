"""EP3 thumbnail 1280x720: cinematic night scene + PURE CODE FILM text."""
import math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, "/home/hatch/workspace/imagine_media/ai-video-channel/trailer")
from lib import W, H, VIOLET, WHITE, font, text_size, draw_centered, FONT_BOLD, FONT_MONO_B

TW, TH = 1280, 720
img = Image.new("RGB", (TW, TH), (6, 10, 22))
d = ImageDraw.Draw(img)

# night sky gradient
for y in range(TH):
    t = y / TH
    c = (int(6 + 12 * t), int(10 + 24 * t), int(26 + 30 * t))
    d.line([(0, y), (TW, y)], fill=c)

# stars
rng = np.random.default_rng(7)
for _ in range(140):
    x, y = rng.uniform(0, TW), rng.uniform(0, 400)
    b = int(150 + 90 * rng.uniform())
    d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(b, b, b + 15))

# moon
d.ellipse([1060, 50, 1180, 170], fill=(232, 238, 248))

# mountains
d.polygon([(0, 480), (200, 380), (420, 460), (640, 360), (860, 470), (1080, 390),
           (1280, 460), (1280, 720), (0, 720)], fill=(18, 30, 54))

# radio tower (right)
tx = 1020
d.polygon([(tx - 60, 560), (tx + 60, 560), (tx + 18, 220), (tx - 18, 220)], fill=(10, 12, 22))
for yy in range(240, 540, 36):
    wf = (yy - 220) / 340
    hw = 18 + wf * 42
    d.line([(tx - hw, yy), (tx + hw, yy)], fill=(30, 34, 54), width=4)
d.ellipse([tx - 10, 168, tx + 10, 188], fill=(255, 90, 90))
# signal rings
for k, rr in enumerate([46, 88, 130]):
    d.ellipse([tx - rr, 178 - rr // 2, tx + rr, 178 + rr // 2],
              outline=(139, 92, 246), width=5)

# snow ground
d.polygon([(0, 560), (TW, 540), (TW, TH), (0, TH)], fill=(36, 50, 80))

# walker silhouette (center-right, clear of text band)
wx, wy = 850, 660
col = (14, 16, 26)
d.line([wx, wy - 100, wx, wy - 160], fill=col, width=22)          # torso
d.line([wx, wy - 100, wx - 28, wy - 40], fill=col, width=12)      # leg back
d.line([wx, wy - 100, wx + 30, wy], fill=col, width=12)           # leg fwd
d.line([wx, wy - 148, wx + 34, wy - 100], fill=col, width=10)     # arm
d.ellipse([wx - 2, wy - 196, wx + 34, wy - 160], fill=col)        # head
d.line([wx + 12, wy - 100, wx + 16, wy - 160], fill=VIOLET, width=3)  # rim

# snow dots
for _ in range(130):
    x, y = rng.uniform(0, TW), rng.uniform(0, TH)
    r = rng.uniform(1.5, 3.5)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 240, 252))

# searchlight beam from tower toward walker (soft, wide)
beam = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
ImageDraw.Draw(beam).polygon(
    [(tx - 14, 300), (tx + 14, 300), (wx + 70, wy), (wx - 70, wy)],
    fill=(190, 175, 255, 70))
beam = beam.filter(ImageFilter.GaussianBlur(12))
img_r = img.convert("RGBA")
img_r.alpha_composite(beam)
d = ImageDraw.Draw(img_r)

def glow_text(cx, y, s, fnt, fill, gc=VIOLET):
    tw, th = text_size(d, s, fnt)
    lay = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((cx - tw / 2, y), s, font=fnt, fill=gc + (150,))
    lay = lay.filter(ImageFilter.GaussianBlur(14))
    img_r.alpha_composite(lay)
    d.text((cx - tw / 2, y), s, font=fnt, fill=fill)

# dark band behind text for readability
d.rectangle([40, 500, 760, 700], fill=(5, 5, 10, 200))
glow_text(400, 515, "PURE CODE", font(FONT_BOLD, 92), WHITE + (255,))
f2 = font(FONT_BOLD, 64)
d.text((70, 620), "FILM SCENE", font=f2, fill=VIOLET + (255,))

img_r.convert("RGB").save(
    "/home/hatch/workspace/imagine_media/ai-video-channel/code-vs-ai-ep3-thumbnail-1280x720.png")
print("thumbnail saved")
