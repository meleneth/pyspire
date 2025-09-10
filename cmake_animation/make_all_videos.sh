#!/usr/bin/bash
set -euo pipefail

rm -f output.mkv
rm -Rf output
mkdir -p output

python 01_simple_compile.py

ffmpeg -hide_banner \
  -framerate 60 -i "output/cmake_animation_%06d.png" \
  -c:v png -pix_fmt rgba -compression_level 100 \
  01_simple_compile.mkv
