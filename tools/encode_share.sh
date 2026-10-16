#!/bin/bash
# Two-pass H.264 share copy of a HyperFrames render (audio copied untouched, so loudness is preserved).
# usage: tools/encode_share.sh <render.mp4> <out.mp4> [video-bitrate, default 5M]
set -euo pipefail
in="$1"; out="$2"; br="${3:-5M}"
log="$(mktemp -d)/x264pass"
ffmpeg -v error -y -i "$in" -c:v libx264 -preset slow -b:v "$br" -pass 1 -passlogfile "$log" -an -f null /dev/null
ffmpeg -v error -y -i "$in" -c:v libx264 -preset slow -b:v "$br" -maxrate 7M -bufsize 10M -pass 2 -passlogfile "$log" \
  -profile:v high -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a copy -movflags +faststart "$out"
rm -rf "$(dirname "$log")"
ls -la "$out"
sha256sum "$out"
