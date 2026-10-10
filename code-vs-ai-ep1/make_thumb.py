"""Thumbnail for Code vs AI EP1: 1280x720, bold CODE vs AI, violet identity."""
import sys, os
sys.path.insert(0, os.path.expanduser("~/workspace/imagine_media/ai-video-channel/trailer"))
from lib import font, FONT_BOLD, text_size, draw_centered, VIOLET, WHITE
from PIL import Image, ImageDraw, ImageFilter
import math

W2, H2 = 1280, 720
img = Image.new("RGB", (W2, H2), (10, 10, 11))
d = ImageDraw.Draw(img)
# bg texture: diagonal violet streaks
for i in range(24):
    x = i*70 - 100
    d.line([x, 0, x+320, H2], fill=(24, 18, 44), width=26)
# left code panel
d.rectangle([40, 60, 600, 660], fill=(14,14,20), outline=(70,70,85), width=4)
fm = font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 34)
code = ["for frame in range(2400):", "    draw(snow)", "    draw(beam)", "    render(frame)"]
y = 130
for ln in code:
    d.text((80, y), ln, font=fm, fill=(235,235,245)); y += 62
d.text((80, y+10), "# no AI. just code.", font=fm, fill=(139,92,246))
# right: CODE vs AI
f1 = font(FONT_BOLD, 130)
draw_centered(d, 940, 130, "CODE", f1, WHITE)
fvs = font(FONT_BOLD, 72)
# vs badge
d.ellipse([940-58, 300-58, 940+58, 300+58], fill=VIOLET)
draw_centered(d, 940, 300-36, "VS", fvs, WHITE)
draw_centered(d, 940, 400, "AI", f1, (235,90,90))
# bottom bar
d.rectangle([40, 640, 1240, 700], fill=(139,92,246))
fb = font(FONT_BOLD, 34)
draw_centered(d, 640, 648, "I built this scene with PURE CODE", fb, (10,10,11))
img.save(os.path.expanduser("~/workspace/imagine_media/ai-video-channel/code-vs-ai-ep1-thumbnail-1280x720.png"))
print("thumb ok")
# spell check note: CODE / VS / AI / code lines verified
