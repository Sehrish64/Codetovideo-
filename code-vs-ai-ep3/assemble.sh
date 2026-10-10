#!/bin/bash
# Assemble EP3: bumpers + content + full audio mix
set -e
cd "$(dirname "$0")"
CH="$HOME/workspace/imagine_media/ai-video-channel"
DUR_TOTAL=73
DUR_CONTENT=62

echo "== 1. encode content frames"
ffmpeg -y -v error -framerate 30 -i frames/f%05d.png \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 30 content.mp4

echo "== 2. prep audio stems"
ffmpeg -y -v error -i "$CH/codetovideo-intro-bumper.mp4" -vn -ar 48000 -ac 2 intro_a.wav
ffmpeg -y -v error -i "$CH/codetovideo-outro.mp4" -vn -ar 48000 -ac 2 outro_a.wav
# concat VO parts (trimmed wavs)
ffmpeg -y -v error -i vo_part1_trim.wav -i vo_part2_trim.wav \
  -filter_complex "[0:a][1:a]concat=n=2:v=0:a=1,aresample=48000,apad=whole_dur=$DUR_TOTAL[vo]" \
  -map "[vo]" -ac 2 vo48.wav
# music: loop Division to total, 20%, end fade
ffmpeg -y -v error -stream_loop 2 -i music.mp3 -ar 48000 -ac 2 -t $DUR_TOTAL \
  -af "afade=t=out:st=69:d=4,volume=0.2" music73.wav
# sfx stem (already 62s stereo) -> pad
ffmpeg -y -v error -i sfx_stem.wav -ar 48000 -ac 2 -t $DUR_TOTAL sfx73.wav

echo "== 3. mix (deterministic pure-sum)"
ffmpeg -y -v error \
  -i intro_a.wav -i vo48.wav -i music73.wav -i sfx73.wav -i outro_a.wav \
  -filter_complex "\
[0:a]pan=stereo|c0=c0|c1=c0,volume=1.0,adelay=0|0,apad=whole_dur=$DUR_TOTAL[s0]; \
[1:a]pan=stereo|c0=c0|c1=c0,volume=3.162,adelay=5000|5000,apad=whole_dur=$DUR_TOTAL[s1]; \
[2:a]pan=stereo|c0=c0|c1=c0,volume=1.0,adelay=0|0,apad=whole_dur=$DUR_TOTAL[s2]; \
[3:a]pan=stereo|c0=c0|c1=c0,volume=1.0,adelay=4000|4000,apad=whole_dur=$DUR_TOTAL[s3]; \
[4:a]pan=stereo|c0=c0|c1=c0,volume=1.0,adelay=66000|66000,apad=whole_dur=$DUR_TOTAL[s4]; \
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
  "$CH/code-vs-ai-ep3-film-scene.mp4"

echo "== 6. verify"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$CH/code-vs-ai-ep3-film-scene.mp4"
ffmpeg -v error -i "$CH/code-vs-ai-ep3-film-scene.mp4" -f null - && echo "DECODE CLEAN"
