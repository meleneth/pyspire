#!/usr/bin/bash
set -euo pipefail

rm -f output.mkv
rm -Rf output
mkdir -p output

python cmake_grinding.py

ffmpeg -hide_banner -framerate 60 -i "output/cmake_animation_%06d.png" \
  -c:v libvpx-vp9 -pix_fmt yuva420p \
  output.mkv
