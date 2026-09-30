"""
Step 2: Turn labeled WAV files into a spectrogram dataset for training.

Install first:
    pip install librosa numpy scipy soundfile

Expected folder layout (create these yourself):

    data/
      physionet/
        normal/      <- PhysioNet/CinC 2016 or CirCor recordings labeled normal
        abnormal/    <- labeled abnormal
      collected/
        healthy/     <- your own recordings, sorted after listening
        unhealthy/

To get public data: download the PhysioNet/CinC 2016 Heart Sound Database
or CirCor DigiScope dataset from physionet.org, then use its REFERENCE.csv
(or similar) to sort files into data/physionet/normal and
data/physionet/abnormal by hand or with a small script - the exact label
format differs slightly by dataset version, so this step is left manual.

This script:
  1. Loads every WAV from all four folders
  2. Resamples to 4000 Hz (heart sound energy is almost entirely under 1kHz)
  3. Bandpass filters 20-400 Hz to strip noise outside the physiological range
  4. Splits each recording into 3-second windows (50% overlap)
  5. Converts each window to a log-mel spectrogram
  6. Saves everything to dataset.npz for the training script
"""

import os
import re
import glob
import numpy as np
import librosa

from dsp_common import SAMPLE_RATE, WINDOW_SAMPLES, bandpass_filter, to_log_mel

HOP_SAMPLES = WINDOW_SAMPLES // 2  # 50% overlap

FOLDERS = {
    "data/physionet/normal": 0,
    "data/physionet/abnormal": 1,
    "data/collected/healthy": 0,
    "data/collected/unhealthy": 1,
}

_SUBSET_RE = re.compile(r"^([a-f])\d+\.wav$")


def extract_subset(path):
    """PhysioNet 2016 pools six separate sub-databases (recorded with
    different equipment/sites), encoded as the filename's first letter
    (a-f, e.g. "a0007.wav"). Returns that letter, or "collected" for your
    own ESP32 recordings, which don't follow this naming scheme.

    This is tracked per-window so 3_train_model.py can check for and
    correct subset-level class imbalance - naive training can otherwise
    learn to key on whichever sub-database dominates a class's file count
    rather than genuine pathology features (see the per-subset accuracy
    breakdown this enables).
    """
    match = _SUBSET_RE.match(os.path.basename(path))
    return match.group(1) if match else "collected"


def process_file(path):
    signal, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True)
    signal = bandpass_filter(signal)

    windows = []
    for start in range(0, len(signal) - WINDOW_SAMPLES, HOP_SAMPLES):
        windows.append(signal[start:start + WINDOW_SAMPLES])

    if not windows and len(signal) > SAMPLE_RATE:
        # Recording shorter than one full window but still usable - pad it
        padded = np.zeros(WINDOW_SAMPLES, dtype=np.float32)
        padded[:len(signal)] = signal[:WINDOW_SAMPLES]
        windows = [padded]

    return [to_log_mel(w) for w in windows]


def main():
    X, y, subset = [], [], []

    for folder, label in FOLDERS.items():
        wav_files = glob.glob(os.path.join(folder, "*.wav"))
        print(f"{folder}: {len(wav_files)} files")

        for path in wav_files:
            try:
                specs = process_file(path)
                X.extend(specs)
                y.extend([label] * len(specs))
                subset.extend([extract_subset(path)] * len(specs))
            except Exception as e:
                print(f"  Skipping {path}: {e}")

    X = np.array(X)
    y = np.array(y)
    subset = np.array(subset)

    print(f"\nTotal windows: {len(X)}")
    print(f"Healthy: {np.sum(y == 0)}, Unhealthy: {np.sum(y == 1)}")
    print(f"Spectrogram shape: {X.shape[1:]}")

    print("\nWindows per source subset (PhysioNet sub-database a-f, or "
          "'collected' for your own ESP32 recordings):")
    for s in sorted(set(subset)):
        mask = subset == s
        print(f"  {s}: {mask.sum()} windows "
              f"({np.sum(y[mask] == 0)} normal, {np.sum(y[mask] == 1)} abnormal)")

    np.savez("dataset.npz", X=X, y=y, subset=subset)
    print("\nSaved dataset.npz (X, y, and per-window subset labels)")


if __name__ == "__main__":
    main()
