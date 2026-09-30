#!/usr/bin/env bash
# Keeps the Python DSP module and model file used by the Vercel functions in
# sync with the canonical training pipeline files one directory up. Runs
# automatically before every build (see package.json's "prebuild" script) so
# there's never a stale/hand-edited copy of api/_lib/dsp.py or the model.
set -euo pipefail
cd "$(dirname "$0")/.."

cp ../dsp_common.py api/_lib/dsp.py
cp ../heart_sound_model.tflite api/_lib/model/heart_sound_model.tflite

echo "Synced dsp_common.py and heart_sound_model.tflite into web/api/_lib/"
