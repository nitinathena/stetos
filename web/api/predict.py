"""
POST /api/predict

Pure inference endpoint - no database writes here (logging a result into the
"predictions" table is the caller's job: the Next.js upload route inserts
with source="user_upload", and sync.py inserts with source="supabase_sync").
Keeping this endpoint stateless makes it independently testable and reusable
by both callers.

Accepts EITHER:
  - multipart/form-data with a "file" field containing a WAV file, or
  - application/json body: {"supabase_path": "<filename in the heart-sounds bucket>"}

Returns JSON: {"filename": str, "prediction": "normal" | "abnormal", "confidence": float}
"""

import io
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify

from _lib.dsp import get_first_window
from _lib.model_runtime import classify

app = Flask(__name__)

MAX_UPLOAD_BYTES = 4 * 1024 * 1024  # stay under Vercel's 4.5MB request body limit


def _predict_from_buffer(filename: str, buffer: io.BytesIO):
    spec = get_first_window(buffer)
    prediction, confidence = classify(spec)
    return {"filename": filename, "prediction": prediction, "confidence": round(confidence, 4)}


@app.post("/api/predict")
def predict():
    if request.content_type and "multipart/form-data" in request.content_type:
        if "file" not in request.files:
            return jsonify({"error": "No 'file' field in multipart upload"}), 400

        upload = request.files["file"]
        raw = upload.read()
        if len(raw) > MAX_UPLOAD_BYTES:
            return jsonify({"error": "File too large (max 4MB)"}), 413

        try:
            result = _predict_from_buffer(upload.filename or "upload.wav", io.BytesIO(raw))
        except Exception as e:
            return jsonify({"error": f"Could not process WAV file: {e}"}), 400

        return jsonify(result)

    body = request.get_json(silent=True) or {}
    supabase_path = body.get("supabase_path")
    if not supabase_path:
        return jsonify({
            "error": "Provide either a multipart 'file' upload or a JSON "
                     "{'supabase_path': ...} body"
        }), 400

    from _lib.supabase_client import get_service_client, BUCKET_NAME

    try:
        client = get_service_client()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    try:
        raw = client.storage.from_(BUCKET_NAME).download(supabase_path)
    except Exception as e:
        return jsonify({"error": f"Could not download '{supabase_path}' from Supabase: {e}"}), 502

    try:
        result = _predict_from_buffer(supabase_path, io.BytesIO(raw))
    except Exception as e:
        return jsonify({"error": f"Could not process WAV file: {e}"}), 400

    return jsonify(result)


@app.get("/api/predict")
def predict_info():
    return jsonify({
        "error": "Use POST with either a multipart 'file' upload or a JSON "
                 "{'supabase_path': ...} body"
    }), 405
