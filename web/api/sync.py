"""
GET/POST /api/sync

Lists WAV files in the "heart-sounds" Supabase Storage bucket, finds ones
not already present in the predictions table (matched by filename, across
either source), runs each through the exact same inference logic
/api/predict.py uses (imported in-process from _lib, not an HTTP self-call -
faster and avoids needing to know this deployment's own base URL), and
inserts results with source="supabase_sync".

Auth: requires an `Authorization: Bearer <CRON_SECRET>` header. Vercel Cron
sends this automatically when an env var named exactly CRON_SECRET is set
(see https://vercel.com/docs/cron-jobs/manage-cron-jobs#securing-cron-jobs).
The dashboard's manual "Sync now" button (a Next.js server-side route, never
the browser) attaches the same header.

Designed to be safely re-run / re-triggered: Vercel's own cron docs warn
that cron delivery can occasionally invoke the same run twice, or miss a
run. Since this only ever processes bucket files that aren't already in the
predictions table, re-running it is a no-op for anything already synced.
"""

import io
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify

from _lib.dsp import get_first_window
from _lib.model_runtime import classify

app = Flask(__name__)

# Max new files processed per invocation. Keeps each run well under the
# function's time limit regardless of how large the backlog gets - a big
# bucket just takes a few more cron runs (or a few more clicks of "Sync
# now") to fully catch up, rather than one call trying to do everything
# and risking a timeout.
MAX_FILES_PER_RUN = 5


def _is_authorized():
    expected = os.environ.get("CRON_SECRET")
    if not expected:
        return False
    provided = request.headers.get("Authorization")
    return provided == f"Bearer {expected}"


@app.route("/api/sync", methods=["GET", "POST"])
def sync():
    if not _is_authorized():
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    # Imported here, not at module level: this pulls in supabase's heavier
    # transitive dependencies (cryptography, postgrest, gotrue, etc.) that
    # predict.py never needs. Importing lazily means a failure here (e.g. a
    # C-extension that doesn't load in this runtime) produces a normal JSON
    # error response instead of crashing the whole module before Flask can
    # even start - which otherwise shows up as an opaque platform 500 page
    # with no application log at all.
    try:
        from _lib.supabase_client import get_service_client, BUCKET_NAME, PREDICTIONS_TABLE
    except Exception as e:
        return jsonify({
            "error": f"Failed to import supabase client: {type(e).__name__}: {e}",
            "traceback": traceback.format_exc(),
        }), 500

    try:
        client = get_service_client()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    try:
        bucket_entries = client.storage.from_(BUCKET_NAME).list()
    except Exception as e:
        return jsonify({"error": f"Could not list bucket '{BUCKET_NAME}': {e}"}), 502

    bucket_filenames = sorted(
        e["name"] for e in bucket_entries if e.get("name", "").endswith(".wav")
    )

    try:
        existing_rows = client.table(PREDICTIONS_TABLE).select("filename").execute()
        already_synced = {row["filename"] for row in existing_rows.data}
    except Exception as e:
        return jsonify({"error": f"Could not query predictions table: {e}"}), 502

    new_filenames = [f for f in bucket_filenames if f not in already_synced]
    batch = new_filenames[:MAX_FILES_PER_RUN]

    processed = []
    errors = []
    for filename in batch:
        try:
            raw = client.storage.from_(BUCKET_NAME).download(filename)
            spec = get_first_window(io.BytesIO(raw))
            prediction, confidence = classify(spec)
            confidence = round(confidence, 4)

            client.table(PREDICTIONS_TABLE).insert({
                "filename": filename,
                "source": "supabase_sync",
                "prediction": prediction,
                "confidence": confidence,
            }).execute()

            processed.append({
                "filename": filename,
                "prediction": prediction,
                "confidence": confidence,
            })
        except Exception as e:
            errors.append({"filename": filename, "error": str(e)})

    return jsonify({
        "bucket_file_count": len(bucket_filenames),
        "already_synced_count": len(already_synced),
        "new_files_found": len(new_filenames),
        "processed_this_run": processed,
        "remaining_after_this_run": len(new_filenames) - len(batch),
        "errors": errors,
    })
