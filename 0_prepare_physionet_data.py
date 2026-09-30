"""
Step 0: Download and auto-sort the PhysioNet/CinC 2016 heart sound dataset.

Install first:
    pip install kaggle

One-time Kaggle API setup (only needed once):
    1. Go to kaggle.com -> your profile picture -> Settings -> API ->
       "Create New Token". This downloads kaggle.json.
    2. Move it to: ~/.kaggle/kaggle.json
    3. Run: chmod 600 ~/.kaggle/kaggle.json

This script downloads swapnilpanda/heart-sound-database (the PhysioNet 2016
set, repackaged for Kaggle). The classic PhysioNet layout ships a
REFERENCE.csv per subfolder (filename,label where -1 = normal, 1 =
abnormal); this particular Kaggle repackaging instead ships the labels as
directory names (heart_sound/{train,val}/{healthy,unhealthy}/*.wav), with
no REFERENCE.csv anywhere. This script supports both: it sorts by
REFERENCE.csv where present, and falls back to sorting by any "healthy"/
"normal" or "unhealthy"/"abnormal" directory name otherwise. Either way,
every WAV ends up copied into data/physionet/normal/ or
data/physionet/abnormal/ - exactly the folders 2_build_dataset.py expects.

Note: in this repackaging, val/ turned out to be a subset of train/ (same
filenames, same content) rather than a held-out split, so we dedupe by
filename to avoid copying the same recording in twice.
"""

import os
import csv
import shutil
import glob
import kaggle

RAW_DOWNLOAD_PATH = "data/physionet_raw"
NORMAL_DIR = "data/physionet/normal"
ABNORMAL_DIR = "data/physionet/abnormal"


def download_dataset():
    os.makedirs(RAW_DOWNLOAD_PATH, exist_ok=True)
    print("Downloading dataset from Kaggle (this can take a few minutes)...")
    kaggle.api.dataset_download_files(
        "swapnilpanda/heart-sound-database",
        path=RAW_DOWNLOAD_PATH,
        unzip=True,
    )
    print("Download complete.")


def sort_by_reference_csv():
    """Classic PhysioNet layout: REFERENCE.csv (filename,label) per folder."""
    reference_files = glob.glob(
        os.path.join(RAW_DOWNLOAD_PATH, "**", "REFERENCE.csv"), recursive=True
    )
    print(f"Found {len(reference_files)} REFERENCE.csv files")

    normal_count, abnormal_count, missing_count = 0, 0, 0
    copied_names = set()

    for ref_path in reference_files:
        folder = os.path.dirname(ref_path)
        with open(ref_path, newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue
                filename, label = row[0].strip(), row[1].strip()
                wav_name = filename if filename.endswith(".wav") else filename + ".wav"
                src = os.path.join(folder, wav_name)

                if not os.path.exists(src):
                    missing_count += 1
                    continue

                if label == "-1":
                    shutil.copy(src, os.path.join(NORMAL_DIR, wav_name))
                    normal_count += 1
                    copied_names.add(wav_name)
                elif label == "1":
                    shutil.copy(src, os.path.join(ABNORMAL_DIR, wav_name))
                    abnormal_count += 1
                    copied_names.add(wav_name)

    if missing_count:
        print(f"Warning: {missing_count} referenced files were not found on disk")
    return normal_count, abnormal_count, copied_names


def sort_by_folder_name():
    """Fallback for repackagings with no REFERENCE.csv: labels are directory
    names instead (e.g. .../healthy/xyz.wav, .../unhealthy/xyz.wav)."""
    normal_count, abnormal_count = 0, 0
    seen_names = set()

    for wav_path in glob.glob(
        os.path.join(RAW_DOWNLOAD_PATH, "**", "*.wav"), recursive=True
    ):
        parts = {p.lower() for p in wav_path.split(os.sep)}
        wav_name = os.path.basename(wav_path)

        if "normal" in parts or "healthy" in parts:
            dest_dir, label = NORMAL_DIR, "normal"
        elif "abnormal" in parts or "unhealthy" in parts:
            dest_dir, label = ABNORMAL_DIR, "abnormal"
        else:
            continue  # can't tell which class this belongs to - skip it

        # De-dupe: this repackaging's val/ folders turned out to be a subset
        # of train/ (identical filenames), so the same recording would
        # otherwise get copied in twice.
        dedupe_key = (label, wav_name)
        if dedupe_key in seen_names:
            continue
        seen_names.add(dedupe_key)

        shutil.copy(wav_path, os.path.join(dest_dir, wav_name))
        if label == "normal":
            normal_count += 1
        else:
            abnormal_count += 1

    return normal_count, abnormal_count


def sort_dataset():
    os.makedirs(NORMAL_DIR, exist_ok=True)
    os.makedirs(ABNORMAL_DIR, exist_ok=True)

    normal_count, abnormal_count, _ = sort_by_reference_csv()

    if normal_count == 0 and abnormal_count == 0:
        print("No REFERENCE.csv-labeled files found; falling back to sorting "
              "by directory name (healthy/unhealthy or normal/abnormal)...")
        normal_count, abnormal_count = sort_by_folder_name()

    print(f"\nSorted: {normal_count} normal, {abnormal_count} abnormal")


if __name__ == "__main__":
    download_dataset()
    sort_dataset()
    print("\nDone. data/physionet/normal/ and data/physionet/abnormal/ are ready.")
    print("Next: run 2_build_dataset.py")
