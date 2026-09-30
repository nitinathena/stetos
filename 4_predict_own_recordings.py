"""
Step 4 (optional): Run the trained model on your own unlabeled recordings.

IMPORTANT: These 9 recordings from data/collected/ have no verified ground
truth label, so this script does NOT compute accuracy. It only shows you
what the model predicts for each file - useful as a qualitative "does this
work on real CorAscult hardware" demo, not as a validation metric. Don't
report these predictions as accuracy figures in your competition writeup;
report them as "example output on real device recordings" instead.

Run after 3_train_model.py has produced heart_sound_model.h5.
"""

import os
import glob
import numpy as np
import tensorflow as tf

from dsp_common import get_first_window

MODEL_PATH = "heart_sound_model.h5"
COLLECTED_FOLDER = "data/collected"


def main():
    model = tf.keras.models.load_model(MODEL_PATH)

    wav_files = glob.glob(os.path.join(COLLECTED_FOLDER, "*.wav"))
    if not wav_files:
        print(f"No WAV files found directly in {COLLECTED_FOLDER}/")
        print("(if you already sorted them into healthy/unhealthy subfolders,")
        print("point this script at the parent folder or list both subfolders)")
        return

    print(f"Running inference on {len(wav_files)} unlabeled recordings")
    print("(no ground truth available - this is a qualitative demo only)\n")

    for path in wav_files:
        spec = get_first_window(path)
        spec_input = np.expand_dims(spec, axis=0)
        prob_abnormal = float(model.predict(spec_input, verbose=0)[0][0])

        label = "likely abnormal" if prob_abnormal > 0.5 else "likely normal"
        confidence = prob_abnormal if prob_abnormal > 0.5 else 1 - prob_abnormal

        print(f"{os.path.basename(path)}: {label} (confidence {confidence:.2f})")


if __name__ == "__main__":
    main()
