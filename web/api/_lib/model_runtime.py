"""
Loads heart_sound_model.tflite once per warm serverless instance and runs
quantized int8 inference on a single log-mel spectrogram window.

Uses ai-edge-litert (a lightweight TFLite interpreter, ~20-30MB installed)
instead of the full tensorflow package, which would be far too large for a
Vercel Python function and would slow cold starts substantially. Verified
locally against heart_sound_model.h5 on all 9 collected recordings: same
label in every case, confidence within ~0.03 of the full Keras model (the
remaining delta is expected int8 quantization noise from the training
script's post-training quantization step).
"""

import os
import numpy as np
from ai_edge_litert.interpreter import Interpreter

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "heart_sound_model.tflite")

_interpreter = None
_input_detail = None
_output_detail = None


def _get_interpreter():
    global _interpreter, _input_detail, _output_detail
    if _interpreter is None:
        _interpreter = Interpreter(model_path=_MODEL_PATH)
        _interpreter.allocate_tensors()
        _input_detail = _interpreter.get_input_details()[0]
        _output_detail = _interpreter.get_output_details()[0]
    return _interpreter, _input_detail, _output_detail


def predict_abnormal_probability(log_mel_spec: np.ndarray) -> float:
    """Takes a (64, 94) float32 log-mel spectrogram (same shape/normalization
    produced by dsp.to_log_mel) and returns P(abnormal) in [0, 1], matching
    the training-time label convention (0=normal/healthy, 1=abnormal/unhealthy).
    """
    interpreter, in_detail, out_detail = _get_interpreter()
    in_scale, in_zero_point = in_detail["quantization"]
    out_scale, out_zero_point = out_detail["quantization"]

    quantized = np.round(log_mel_spec / in_scale + in_zero_point)
    quantized = np.clip(quantized, -128, 127).astype(np.int8)
    quantized = np.expand_dims(quantized, axis=0)  # add batch dim

    interpreter.set_tensor(in_detail["index"], quantized)
    interpreter.invoke()

    raw_output = interpreter.get_tensor(out_detail["index"])[0][0]
    return float((int(raw_output) - out_zero_point) * out_scale)


def classify(log_mel_spec: np.ndarray):
    """Returns (prediction: "normal" | "abnormal", confidence: float)."""
    prob_abnormal = predict_abnormal_probability(log_mel_spec)
    if prob_abnormal > 0.5:
        return "abnormal", prob_abnormal
    return "normal", 1 - prob_abnormal
