"""
Shared preprocessing for the CorAscult heart sound pipeline.

This is the single source of truth for turning a raw WAV recording into
the exact log-mel spectrogram representation the model was trained on:
resample -> bandpass filter -> (optional windowing) -> log-mel spectrogram.

Used by:
  - 2_build_dataset.py            (builds dataset.npz for training)
  - 4_predict_own_recordings.py   (local qualitative demo on unlabeled WAVs)
  - web/api/_lib/dsp.py            (synced copy, used by the Vercel inference
                                    endpoint - see web/package.json's build
                                    script for how the copy is kept in sync)

Do not duplicate these functions elsewhere - any drift between training-time
and inference-time preprocessing will silently produce wrong predictions.
"""

import numpy as np
import librosa
from scipy.signal import butter, sosfiltfilt

SAMPLE_RATE = 4000
WINDOW_SECONDS = 3
WINDOW_SAMPLES = SAMPLE_RATE * WINDOW_SECONDS
N_MELS = 64


def bandpass_filter(signal, low=20, high=400, fs=SAMPLE_RATE):
    sos = butter(4, [low, high], btype="band", fs=fs, output="sos")
    return sosfiltfilt(sos, signal)


def to_log_mel(window):
    mel = librosa.feature.melspectrogram(
        y=window, sr=SAMPLE_RATE, n_mels=N_MELS, n_fft=512, hop_length=128
    )
    log_mel = librosa.power_to_db(mel, ref=np.max)
    # Normalize to roughly [-1, 1]
    log_mel = (log_mel - log_mel.mean()) / (log_mel.std() + 1e-8)
    return log_mel.astype(np.float32)


def get_first_window(path_or_buffer):
    """Load a WAV (path or file-like/BytesIO), resample to SAMPLE_RATE,
    bandpass filter, and return the log-mel spectrogram of its first
    WINDOW_SECONDS window (padding with zeros if the recording is shorter).

    This is what both the local single-file demo script and the web
    inference endpoint use - it does not slide across multiple windows the
    way 2_build_dataset.py's process_file() does for building the training
    set.
    """
    signal, _ = librosa.load(path_or_buffer, sr=SAMPLE_RATE, mono=True)
    signal = bandpass_filter(signal)

    if len(signal) < WINDOW_SAMPLES:
        padded = np.zeros(WINDOW_SAMPLES, dtype=np.float32)
        padded[:len(signal)] = signal
        signal = padded

    return to_log_mel(signal[:WINDOW_SAMPLES])
