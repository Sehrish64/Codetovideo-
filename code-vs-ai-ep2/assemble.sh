#!/bin/bash
# Assemble EP2: bumpers + content + full audio mix
set -e
cd "$(dirname "$0")"
CH="$HOME/workspace/imagine_media/ai-video-channel"
DUR_TOTAL=83

echo "== 1. encode content frames"
ffmpeg -y -v error -framerate 30 -i frames/f%05d.png \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 30 content.mp4

echo "== 2. prep audio stems"
ffmpeg -y -v error -i "$CH/codetovideo-intro-bumper.mp4" -vn -ar 48000 -ac 2 intro_a.wav
ffmpeg -y -v error -i "$CH/codetovideo-outro.mp4" -vn -ar 48000 -ac 2 outro_a.wav
ffmpeg -y -v error -i music.mp3 -ar 48000 -ac 2 -t $DUR_TOTAL \
  -af "afade=t=out:st=79:d=4,volume=0.22" music83.wav
ffmpeg -y -v error -i vo.mp3 -ar 48000 -ac 2 vo48.wav

echo "== 3. mix (deterministic pure-sum)"
ffmpeg -y -v error \
  -i intro_a.wav -i vo48.wav -i music83.wav -i sfx_stem.wav -i outro_a.wav \
  -filter_complex "\
[0:a]pan=stereo|c0=c0|c1=c0,volume=1.0,adelay=0|0,apad=whole_dur=$DUR_TOTAL[s0]; \
[1:a]pan=stereo|c0=c0|c1=c0,volume=1.0,adelay=5000|5000,apad=whole_dur=$DUR_TOTAL[s1]; \
[2:a]pan=stereo|c0=c0|c1=c0,volume=1.0,adelay=0|0,apad=whole_dur=$DUR_TOTAL[s2]; \
[3:a]pan=stereo|c0=c0|c1=c0,volume=1.0,adelay=4000|4000,apad=whole_dur=$DUR_TOTAL[s3]; \
[4:a]pan=stereo|c0=c0|c1=c0,volume=1.0,adelay=76000|76000,apad=whole_dur=$DUR_TOTAL[s4]; \
[s0][s1][s2][s3][s4]amerge=inputs=5,pan=stereo|c0=c0+c2+c4+c6+c8|c1=c1+c3+c5+c7+c9[mix]" \
  -map "[mix]" -c:a aac -b:a 192k -t $DUR_TOTAL final_audio.m4a

echo "== 4. concat video"
ffmpeg -y -v error \
  -i "$CH/codetovideo-intro-bumper.mp4" -i content.mp4 -i "$CH/codetovideo-outro.mp4" \
  -filter_complex "\
[0:v]scale=1920:1080,fps=30,format=yuv420p[v0]; \
[1:v]scale=1920:1080,fps=30,format=yuv420p[v1]; \
[2:v]scale=1920:1080,fps=30,format=yuv420p[v2]; \
[v0][v1][v2]concat=n=3:v=1:a=0[vout]" \
  -map "[vout]" -c:v libx264 -preset medium -crf 18 -r 30 video_joined.mp4

echo "== 5. mux"
ffmpeg -y -v error -i video_joined.mp4 -i final_audio.m4a \
  -c:v copy -c:a copy -shortest \
  "$CH/code-vs-ai-ep2-radio-station.mp4"

echo "== 6. verify"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$CH/code-vs-ai-ep2-radio-station.mp4"
ffmpeg -v error -i "$CH/code-vs-ai-ep2-radio-station.mp4" -f null - && echo "DECODE CLEAN"
