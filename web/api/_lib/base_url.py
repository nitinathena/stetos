"""
Mirrors web/lib/api-base-url.ts for server-to-server calls made from within
the Python functions themselves (sync.py calling predict.py).

Deliberately NOT using VERCEL_URL: it points at the ephemeral per-deployment
hostname, which sits behind Vercel's "Vercel Authentication" deployment
protection - an internal request to it gets redirected to an HTML auth page
instead of reaching the real function. VERCEL_PROJECT_PRODUCTION_URL is the
stable production domain and isn't behind that wall.
"""

import os


def get_base_url():
    production_url = os.environ.get("VERCEL_PROJECT_PRODUCTION_URL")
    if production_url:
        return f"https://{production_url}"

    deployment_url = os.environ.get("VERCEL_URL")
    if deployment_url:
        return f"https://{deployment_url}"

    return "http://localhost:3000"
