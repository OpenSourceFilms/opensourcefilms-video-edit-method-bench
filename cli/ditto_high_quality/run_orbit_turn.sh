#!/usr/bin/env bash
set -euo pipefail
ROOT="${DITTO_ROOT:?Set DITTO_ROOT to your clone of EzioBy/Ditto}"
SHOT="${SHOT_DIR:?Set SHOT_DIR to the directory holding your source plate and reference frame}"
OUT="${OUT:-$SHOT/OrbitTurn_Reskin/Ditto_HQ/diagnostic_73f.mp4}"
LORA="${DITTO_LORA:?Set DITTO_LORA to the desired official Ditto model .safetensors path}"
mkdir -p "$(dirname "$OUT")"
cd "$ROOT"
python inference/infer_ditto.py \
 --input_video "$SHOT/orbit_and_turn_4K8Bit_01.mov" \
 --output_video "$OUT" \
 --prompt "Remove the actor completely for the entire shot. Reconstruct the room background and preserve the exact camera movement, acceleration, framing, perspective, parallax, timing and late optical focus pull. Keep wall, window and sconce geometry stable; do not add people or objects." \
 --lora_path "$LORA" --num_frames 73 --device_id 0
