#!/bin/bash
# Assemble Code vs AI EP1: intro + main + outro, mixed audio
set -e
D=~/workspace/imagine_media/ai-video-channel/code-vs-ai
A=~/workspace/imagine_media/ai-video-channel
OUT=$A/code-vs-ai-ep1.mp4
MUS=~/workspace/imagine_media/maths-channel/music-options/"The Builder.mp3"

echo "== encode main silent =="
ffmpeg -y -v error -framerate 30 -i $D/frames/f_%05d.png \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart $D/main_silent.mp4

echo "== prepare audio stems =="
# VO part1 (lines 1-4): at main 1s. VO part2 (lines 5-6): at main 38s. Pad to 60s.
# NOTE: apad whole_dur takes seconds; trim to 60s with atrim after.
ffmpeg -y -v error -i $D/vo_part1.mp3 -i $D/vo_part2.mp3 -filter_complex "
[0:a]adelay=1000|1000[p1d];
[1:a]adelay=38000|38000[p2d];
[p1d][p2d]amix=inputs=2:normalize=0,atrim=0:60[vo]" -map "[vo]" $D/vo_pad.wav
# music: trim to 60s, duck under VO
ffmpeg -y -v error -i "$MUS" -t 60 -af "volume=0.42,apad=whole_dur=60" $D/mus_pad.wav

echo "== mix (deterministic amerge recipe) =="
# VO source ~-28dB -> +10dB boost (volume=3.2) to sit clearly on top.
# Music source ~-22.5dB at volume=0.42 -> ~-30dB bed. SFX punchy peaks.
ffmpeg -y -v error \
 -i $D/vo_pad.wav -i $D/mus_pad.wav -i $D/sfx_stem.wav \
 -filter_complex "
 [0:a]pan=stereo|c0=c0|c1=c0,volume=3.2,apad=whole_dur=60[vo];
 [1:a]pan=stereo|c0=c0|c1=c0,volume=1.0,apad=whole_dur=60[mu];
 [2:a]pan=stereo|c0=c0|c1=c0,volume=0.9,apad=whole_dur=60[sfx];
 [vo][mu][sfx]amerge=inputs=3,pan=stereo|c0=c0+c2+c4|c1=c1+c3+c5,alimiter=limit=0.95:level_in=1:level_out=1,atrim=0:60[a]" \
 -map "[a]" -c:a aac -b:a 192k $D/mix.m4a

echo "== mux main =="
ffmpeg -y -v error -i $D/main_silent.mp4 -i $D/mix.m4a \
  -c:v copy -c:a copy -shortest $D/main_full.mp4

echo "== concat intro + main + outro =="
# normalize all to same codec params first
for f in $A/codetovideo-intro-bumper.mp4 $D/main_full.mp4 $A/codetovideo-outro.mp4; do :; done
ffmpeg -y -v error -i $A/codetovideo-intro-bumper.mp4 -i $D/main_full.mp4 -i $A/codetovideo-outro.mp4 \
 -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]" \
 -map "[v]" -map "[a]" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k \
 -movflags +faststart "$OUT"

echo "== verify =="
ffmpeg -v error -i "$OUT" -f null - 2>&1 | head -5
DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT")
echo "final: $OUT (${DUR}s)"
ls -lh "$OUT"
