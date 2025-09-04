#!/usr/bin/bash
python cmake_grinding.py

ffmpeg -framerate 60 -i "output/cmake_animation_%06d.png" \
  -c:v libvpx-vp9 -pix_fmt yuva420p \
  output.mkv
