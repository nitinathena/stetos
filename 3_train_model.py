"""
Step 3: Train a CNN on the spectrograms and export a quantized TFLite model.

Install first:
    pip install tensorflow numpy scikit-learn

Run after 2_build_dataset.py has produced dataset.npz.

Outputs:
  heart_sound_model.h5    - full Keras model (for your own reference/testing)
  heart_sound_model.tflite - int8-quantized model, ready for TFLite Micro on
                             the ESP32-S3

Subset-imbalance handling (added after diagnosing an 82.6%-normal-called-
"abnormal" skew on real hardware recordings):
PhysioNet 2016 pools six separate sub-databases (a-f, different equipment/
sites) that are very unevenly represented - e.g. subset e alone was 76% of
the "normal" training files. A model trained on a plain label-stratified
split can learn "sounds like subset e" as its definition of normal instead
of genuine pathology features, and a validation split stratified the same
way (by label only) inherits the same imbalance, so it doesn't catch this.
This script now:
  1. Splits train/val stratified jointly by (label, subset), not label alone.
  2. Applies a per-subset sample weight, WITHIN each label, on top of the
     existing (unchanged) label class_weight - so subset e's loss
     contribution no longer dwarfs the other subsets' inside the normal
     class, and same for abnormal.
  3. Always prints a per-subset accuracy breakdown after evaluation, so
     this kind of imbalance is caught immediately in future, not discovered
     later through manual diagnosis.
"""

import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report

DATASET_PATH = "dataset.npz"
MODEL_H5_PATH = "heart_sound_model.h5"
MODEL_TFLITE_PATH = "heart_sound_model.tflite"


def build_model(input_shape):
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=input_shape),
        tf.keras.layers.Reshape((*input_shape, 1)),

        tf.keras.layers.Conv2D(8, 3, activation="relu", padding="same"),
        tf.keras.layers.MaxPooling2D(2),

        tf.keras.layers.Conv2D(16, 3, activation="relu", padding="same"),
        tf.keras.layers.MaxPooling2D(2),

        tf.keras.layers.Conv2D(32, 3, activation="relu", padding="same"),
        tf.keras.layers.GlobalAveragePooling2D(),

        tf.keras.layers.Dense(16, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model


def representative_dataset_gen(X_train):
    def gen():
        for i in range(min(200, len(X_train))):
            sample = X_train[i:i + 1].astype(np.float32)
            yield [sample]
    return gen


def compute_subset_balanced_sample_weight(y_train, subset_train, class_weight_dict):
    """Per-sample weight = existing label class_weight * a new within-label
    subset weight. The subset weight is computed SEPARATELY inside each
    label (using only that label's own subset counts), via the same
    sklearn "balanced" formula already used for class_weight - so it only
    corrects subset composition within normal, and separately within
    abnormal, without disturbing the existing normal/abnormal balance.
    """
    sample_weight = np.zeros(len(y_train), dtype=np.float64)
    subset_weight_table = {}  # (label, subset) -> weight, for printing

    for label in np.unique(y_train):
        label_mask = y_train == label
        label_subsets = subset_train[label_mask]
        unique_subsets = np.unique(label_subsets)

        subset_weights = compute_class_weight(
            class_weight="balanced", classes=unique_subsets, y=label_subsets
        )
        within_label_weight = dict(zip(unique_subsets, subset_weights))

        for s, w in within_label_weight.items():
            subset_weight_table[(label, s)] = w

        per_sample_subset_weight = np.array(
            [within_label_weight[s] for s in label_subsets]
        )
        sample_weight[label_mask] = class_weight_dict[label] * per_sample_subset_weight

    return sample_weight, subset_weight_table


def print_per_subset_breakdown(y_val, y_pred, subset_val):
    """Permanent diagnostic: accuracy and per-class recall broken down by
    source subset, so subset-level generalization gaps (like the one that
    prompted this) are visible every time the model trains, not just when
    someone goes looking for them.
    """
    print("\nPer-subset accuracy breakdown (validation set):")
    print(f"  {'subset':<10}{'n':>7}{'accuracy':>10}{'normal recall':>16}{'abnormal recall':>18}")
    for s in sorted(set(subset_val)):
        mask = subset_val == s
        n = mask.sum()
        acc = np.mean(y_pred[mask] == y_val[mask])

        normal_mask = mask & (y_val == 0)
        abnormal_mask = mask & (y_val == 1)
        normal_recall = (
            np.mean(y_pred[normal_mask] == 0) if normal_mask.sum() > 0 else float("nan")
        )
        abnormal_recall = (
            np.mean(y_pred[abnormal_mask] == 1) if abnormal_mask.sum() > 0 else float("nan")
        )

        def fmt(x):
            return f"{x:.1%}" if not np.isnan(x) else "n/a"

        print(f"  {s:<10}{n:>7}{acc:>10.1%}{fmt(normal_recall):>16}{fmt(abnormal_recall):>18}")


def main():
    data = np.load(DATASET_PATH, allow_pickle=True)
    X, y, subset = data["X"], data["y"], data["subset"]
    print(f"Loaded {len(X)} samples, shape {X.shape[1:]}")

    # Stratify jointly by (label, subset) - not label alone - so validation
    # genuinely tests generalization across all subsets, not mostly
    # whichever subset dominates a class's file count.
    joint_strata = np.array([f"{label}_{s}" for label, s in zip(y, subset)])
    (X_train, X_val, y_train, y_val,
     subset_train, subset_val) = train_test_split(
        X, y, subset, test_size=0.2, random_state=42, stratify=joint_strata
    )

    model = build_model(X.shape[1:])
    model.summary()

    # Handle class imbalance (your PhysioNet split is roughly 3.9:1 normal:abnormal) -
    # without this, the model can look "accurate" by mostly just predicting normal.
    class_weights = compute_class_weight(
        class_weight="balanced", classes=np.unique(y_train), y=y_train
    )
    class_weight_dict = dict(zip(np.unique(y_train), class_weights))
    print(f"Class weights: {class_weight_dict}")

    # On top of that, balance subset composition within each label (see
    # module docstring) - Keras' fit() doesn't accept class_weight and
    # sample_weight together, so this folds the class weight in directly.
    sample_weight_train, subset_weight_table = compute_subset_balanced_sample_weight(
        y_train, subset_train, class_weight_dict
    )
    print("Per-(label, subset) sample weights (label class_weight x within-label "
          "subset balance):")
    for (label, s), w in sorted(subset_weight_table.items()):
        label_name = "normal" if label == 0 else "abnormal"
        print(f"  {label_name:<10} subset {s}: {class_weight_dict[label]:.3f} (class) "
              f"x {w:.3f} (subset) = {class_weight_dict[label] * w:.3f}")

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=30,
        batch_size=16,
        sample_weight=sample_weight_train,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss", patience=5, restore_best_weights=True
            )
        ],
    )

    val_loss, val_acc = model.evaluate(X_val, y_val)
    print(f"\nValidation accuracy: {val_acc:.3f}")

    # Accuracy alone is misleading on an imbalanced dataset - check precision/recall
    # per class too, especially recall on class 1 (abnormal), which is the one that
    # actually matters clinically.
    y_pred = (model.predict(X_val) > 0.5).astype(int).flatten()
    print("\nPer-class performance:")
    print(classification_report(y_val, y_pred, target_names=["normal", "abnormal"]))

    print_per_subset_breakdown(y_val, y_pred, subset_val)

    model.save(MODEL_H5_PATH)
    print(f"\nSaved {MODEL_H5_PATH}")

    # Convert to int8-quantized TFLite for on-device inference
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset_gen(X_train)
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    tflite_model = converter.convert()
    with open(MODEL_TFLITE_PATH, "wb") as f:
        f.write(tflite_model)

    print(f"Saved {MODEL_TFLITE_PATH} ({len(tflite_model) / 1024:.1f} KB)")
    print("\nThis .tflite file is what you'll embed on the ESP32-S3 with")
    print("TensorFlow Lite Micro (or convert to a C array with xxd -i).")


if __name__ == "__main__":
    main()
