#!/usr/bin/env bash
set -euo pipefail
ROOT="${LTX2_ROOT:?Set LTX2_ROOT to your clone of Lightricks/LTX-2}"
SHOT="${SHOT_DIR:?Set SHOT_DIR to the directory holding your source plate and reference frame}"
OUT="${OUT:-$SHOT/OrbitTurn_Reskin/SyncLoRA/diagnostic_81f.mp4}"
BASE="${BASE:-$ROOT/models/ltx-2.3-22b-dev.safetensors}"
UPSCALE="${UPSCALE:-$ROOT/models/ltx-2.3-spatial-upscaler-x2-1.1.safetensors}"
GEMMA="${GEMMA:-$ROOT/models/gemma}"
SYNC="${SYNC:-$ROOT/models/ltx-2.3-sync-lora-3d1t-r256.safetensors}"
DISTILLED="${DISTILLED:-$ROOT/models/ltx-2.3-22b-distilled-lora-384-1.1.safetensors}"
mkdir -p "$(dirname "$OUT")"
cd "$ROOT"
python -m ltx_pipelines.ic_lora \
  --distilled-checkpoint-path "$BASE" \
  --spatial-upsampler-path "$UPSCALE" \
  --gemma-root "$GEMMA" \
  --lora "$SYNC" 1.0 \
  --lora "$DISTILLED" 1.0 \
  --prompt "3d1t" \
  --video-conditioning "$SHOT/orbit_and_turn_4K8Bit_01.mov" 1.0 \
  --images "$SHOT/Orbit_and_turn_Firstframe_Flames_1088p_01.png" 0 1.0 \
  --height 1024 --width 1024 --num-frames 81 --frame-rate 24 --seed 42 \
  --output-path "$OUT"
