#!/usr/bin/env bash
# Build video/demo.mp4 (<= 1:55, 1920x1080, H.264 veryfast, burned-in captions, no audio) from logged artefacts:
# talk slides (talk/main.pdf), final figures (reports/final_eval/figures/*.pdf) and the real demo disassembly
# (experiments/2026-11-26_demo_01310/demo_01310_frames). Needs the conda env `paper` (ffmpeg) and poppler (pdftoppm).
# Usage: bash video/build_video.sh
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
W=$ROOT/video/build
mkdir -p "$W"
FF="conda run --no-capture-output -n paper ffmpeg -y -loglevel error"
FONT=$(fc-match -f '%{file}' 'DejaVu Sans:bold')
FRAMES=$ROOT/experiments/2026-11-26_demo_01310/demo_01310_frames

# stills: slide pages and figures at 1920 px wide, padded to 1920x1080 on white
pdftoppm -png -r 240 -f 5 -l 5 "$ROOT/talk/main.pdf" "$W/pipeline"            # "What we built"
for f in totals_replay_live budget_policy failure_scatter; do
  pdftoppm -png -r 300 -singlefile "$ROOT/reports/final_eval/figures/$f.pdf" "$W/$f"
done
pad="scale=1800:960:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2+40:white,format=yuv420p"

# caption helper: a white band at the top with dark text
cap() { echo "drawbox=x=0:y=0:w=iw:h=110:color=white@0.92:t=fill,drawtext=expansion=none:fontfile=$FONT:text='$1':fontsize=42:fontcolor=0x0b0b0b:x=(w-text_w)/2:y=34"; }

# 1 (0-6 s) hook: the real CMG-RRT rotation removal (last state of the demo, frames 88..106)
$FF -framerate 3.2 -start_number 88 -i "$FRAMES/%04d.png" -frames:v 19 \
  -vf "scale=1920:1080,$(cap 'Which part can come out next? Asking the planner costs 0.04 s ... or 30 s.'),format=yuv420p" \
  -r 30 "$W/s1.mp4"
# 2 (6-16 s) the problem
$FF -f lavfi -i "color=c=white:s=1920x1080:d=10" -vf "drawtext=expansion=none:fontfile=$FONT:text='Each removal test is a CMG-RRT motion-planning query.':fontsize=50:fontcolor=0x0b0b0b:x=(w-text_w)/2:y=380,drawtext=expansion=none:fontfile=$FONT:text='A timeout (30 s) proves nothing - and it dominates the cost.':fontsize=50:fontcolor=0xc44e52:x=(w-text_w)/2:y=500,drawtext=expansion=none:fontfile=$FONT:text='So - which part should we ask about first?':fontsize=50:fontcolor=0x2a78d6:x=(w-text_w)/2:y=620,format=yuv420p" -r 30 "$W/s2.mp4"
# 3 (16-30 s) the system
$FF -loop 1 -t 14 -i "$W/pipeline-05.png" -vf "$pad,$(cap 'GNN + survival head - P(success) and expected cost per part; query in p/c order.')" -r 30 "$W/s3.mp4"
# 4 (30-55 s) a real disassembly with the learned order (13.4 s of frames, slowed to 25 s)
$FF -framerate 4.3 -i "$FRAMES/%04d.png" -vf "scale=1920:1080,$(cap 'A real test assembly - the learned query order, fresh CMG-RRT queries.'),format=yuv420p" -r 30 "$W/s4.mp4"
# 5 (55-75 s) headline result
$FF -loop 1 -t 20 -i "$W/totals_replay_live.png" -vf "$pad,$(cap '347 fresh assemblies, pre-registered - cheaper than ASAP - but no better than fewest contacts.')" -r 30 "$W/s5.mp4"
# 6 (75-90 s) negative result
$FF -loop 1 -t 15 -i "$W/failure_scatter.png" -vf "$pad,$(cap 'Why - a few confident timeouts on larger, unseen assemblies.')" -r 30 "$W/s6.mp4"
# 7 (90-105 s) the policy that worked
$FF -loop 1 -t 15 -i "$W/budget_policy.png" -vf "$pad,$(cap 'Biggest win, not learned - try every part for 3 s first (-72% replay, -50% live).')" -r 30 "$W/s7.mp4"
# 8 (105-113 s) end card
$FF -f lavfi -i "color=c=white:s=1920x1080:d=8" -vf "drawtext=expansion=none:fontfile=$FONT:text='Cost-aware query ordering for assembly-by-disassembly':fontsize=52:fontcolor=0x0b0b0b:x=(w-text_w)/2:y=420,drawtext=expansion=none:fontfile=$FONT:text='github.com/AaronChandler976/curved-path-puzzle-solver':fontsize=46:fontcolor=0x2a78d6:x=(w-text_w)/2:y=540,drawtext=expansion=none:fontfile=$FONT:text='Aaron Chandler - CMPE 258, SJSU, Fall 2026':fontsize=36:fontcolor=0x52514e:x=(w-text_w)/2:y=650,format=yuv420p" -r 30 "$W/s8.mp4"

printf "file '%s'\n" "$W"/s{1,2,3,4,5,6,7,8}.mp4 > "$W/list.txt"
$FF -f concat -safe 0 -i "$W/list.txt" -c:v libx264 -preset veryfast -pix_fmt yuv420p -r 30 -an "$ROOT/video/demo.mp4"
conda run --no-capture-output -n paper ffprobe -v error -show_entries format=duration:stream=width,height,codec_name \
  -of default=nw=1 "$ROOT/video/demo.mp4"
