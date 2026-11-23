#!/usr/bin/env bash
# Download YOLOX weights and export them to ONNX.
# Usage (inside the export container): export.sh <model> <output folder>
#   model: nano | s | m   (default s)
set -euo pipefail
MODEL=${1:-s}
OUT=${2:-/models}
URL=https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_${MODEL}.pth
mkdir -p "$OUT"
[ -f "$OUT/yolox_${MODEL}.pth" ] || curl -fL -o "$OUT/yolox_${MODEL}.pth" "$URL"
python tools/export_onnx.py -n "yolox-${MODEL}" -c "$OUT/yolox_${MODEL}.pth" \
    --output-name "$OUT/yolox_${MODEL}.onnx" --opset 11 --no-onnxsim
