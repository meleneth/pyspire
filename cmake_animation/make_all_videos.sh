#!/usr/bin/env bash
set -euo pipefail

render() {
  local name="$1"

  echo "=== Rendering $name ==="
  rm -f "${name}.mkv"
  rm -rf output
  mkdir -p output

  python "${name}.py"

  ffmpeg -hide_banner \
    -framerate 60 -i "output/cmake_animation_%06d.png" \
    -c:v png -pix_fmt rgba -compression_level 100 \
    "${name}.mkv"
}

# All available demos
ALL_TARGETS=(
  01_simple_compile
  02_object_compile
  02_object_compile_dirty_main
  02_object_compile_dirty_header
  04_lib_compile
)

# If args are given, use them; otherwise run all
if [[ $# -gt 0 ]]; then
  TARGETS=("$@")
else
  TARGETS=("${ALL_TARGETS[@]}")
fi

for t in "${TARGETS[@]}"; do
  render "$t"
done
