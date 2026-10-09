# CodeToVideo — Launch Trailer Build Scripts

Source code for the CodeToVideo YouTube channel launch package:
**channel trailer (36s)**, **intro bumper (4s)**, **outro (7s)**,
and the **subscribe-bell / like / comment overlays**.

Watch it live: https://www.youtube.com/@CodeToVideo

## Brand identity

- Background: dark ink `#0A0A0B`
- Accent: violet `#8B5CF6`
- Type: white, DejaVu Sans family

## Files

| Script | Builds |
|---|---|
| `lib.py` | Shared drawing helpers (colors, fonts, easing, text utils) |
| `render_trailer.py` | Trailer frames → `trailer/frames_trailer/` (36s @ 30fps, 1920×1080) |
| `render_assets.py` | Intro bumper + outro frames |
| `render_overlays.py` | Like + comment overlays (ProRes 4444 with real alpha) |
| `mix_audio.py` | Synthesizes/places SFX stems and mixes with the music bed |
| `encode_assets.py` | Encodes intro/outro/bell with SFX to final files |

Only code is committed here — no binaries, audio, or rendered frames.

## Requirements

- Python 3
- `pip install pillow numpy`
- `ffmpeg` (with `libx264` and `prores_ks`)
- DejaVu fonts (`/usr/share/fonts/truetype/dejavu/` on Debian/Ubuntu)

## How to run

```bash
cd trailer
python3 render_trailer.py    # render trailer frames
python3 render_assets.py     # render intro + outro frames
python3 render_overlays.py   # render like/comment overlays
python3 mix_audio.py         # build the audio mix
python3 encode_assets.py     # encode final videos
```

Frame folders are created automatically. Encode the trailer frames to video with:

```bash
ffmpeg -framerate 30 -i trailer/frames_trailer/frame_%04d.png \
  -i trailer_mix.wav -c:v libx264 -crf 18 -pix_fmt yuv420p \
  -c:a aac -shortest codetovideo-trailer.mp4
```

## Quality rules (standing)

Every video built from these scripts must pass before delivery:

1. Spell-check all on-screen text
2. Text stays inside screen bounds (eyeball extracted frames)
3. Full `ffmpeg -f null` decode — clean, no errors
4. SFX on every meaningful animation
5. No emojis inside videos

## License

Code is original work for the CodeToVideo channel.
Music used in the trailer: *Cipher* by Kevin MacLeod (incompetech.com),
licensed under CC BY 3.0 — credit him if you reuse the mix.
