"""
Step 1: Download recorded heart sound WAVs from Supabase Storage.

Install first:
    pip install supabase

Fill in SUPABASE_URL and SUPABASE_KEY below (same project as your firmware -
you can use either the anon key or, since this runs locally and not on the
device, the service_role key if you want to bypass RLS entirely for this
step).
"""

import os
from supabase import create_client

SUPABASE_URL = "https://hmvxfwgzwsimafwiwiet.supabase.co"
SUPABASE_KEY = "sb_publishable_qpeU-P0rBFDfyJ3QA9SyPA_4vLRJbtb"
BUCKET_NAME = "heart-sounds"
LOCAL_FOLDER = "data/collected"


def main():
    os.makedirs(LOCAL_FOLDER, exist_ok=True)
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    files = client.storage.from_(BUCKET_NAME).list()
    print(f"Found {len(files)} files in bucket '{BUCKET_NAME}'")

    for f in files:
        filename = f["name"]
        local_path = os.path.join(LOCAL_FOLDER, filename)

        if os.path.exists(local_path):
            print(f"Skipping (already downloaded): {filename}")
            continue

        print(f"Downloading: {filename}")
        data = client.storage.from_(BUCKET_NAME).download(filename)
        with open(local_path, "wb") as out_file:
            out_file.write(data)

    print(f"\nDone. Files saved to {LOCAL_FOLDER}/")
    print("Next: listen to each recording and sort into data/collected/healthy/")
    print("and data/collected/unhealthy/ subfolders before running step 2.")


if __name__ == "__main__":
    main()
