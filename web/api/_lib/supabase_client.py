"""
Server-side Supabase client for the Python functions. Uses the service_role
key so storage downloads and table inserts work regardless of RLS policies -
this key must NEVER be exposed to the browser (it's only read from env vars
inside these serverless functions, never returned in any response).
"""

import os
from supabase import create_client, Client

BUCKET_NAME = "heart-sounds"
PREDICTIONS_TABLE = "predictions"


def get_service_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set as "
            "environment variables (see .env.example)."
        )
    return create_client(url, key)
