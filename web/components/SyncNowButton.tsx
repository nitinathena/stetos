"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function SyncNowButton() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const router = useRouter();

  const handleClick = async () => {
    setIsSyncing(true);
    setMessage(null);
    try {
      const res = await fetch("/api/sync-trigger", { method: "POST" });
      // Read as text first - don't let a non-JSON error response (e.g. an
      // HTML error page) blow up as an opaque SyntaxError.
      const bodyText = await res.text();
      let json: Record<string, unknown> | null = null;
      try {
        json = JSON.parse(bodyText);
      } catch {
        // not JSON - fall through, json stays null
      }

      if (!res.ok || !json) {
        const preview = (json?.bodyPreview as string) ?? bodyText.slice(0, 200);
        const errorMsg = (json?.error as string) ?? `HTTP ${res.status}`;
        setMessage(`Sync failed: ${errorMsg}${preview ? ` - ${preview}` : ""}`);
      } else {
        const processed = (json.processed_this_run as unknown[] | undefined)?.length ?? 0;
        const remaining = (json.remaining_after_this_run as number | undefined) ?? 0;
        setMessage(
          `Synced ${processed} new recording(s) ` +
          `(${json.bucket_file_count} total in bucket, ${json.already_synced_count} already synced` +
          (remaining > 0 ? `, ${remaining} still remaining for the next run` : "") +
          `).`
        );
        router.refresh(); // re-fetch the server-rendered dashboard data
      }
    } catch {
      setMessage("Could not reach the server.");
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={isSyncing}
        className="rounded-lg px-4 py-2 text-sm font-medium text-white transition-opacity disabled:opacity-60"
        style={{ background: "var(--brand)" }}
      >
        {isSyncing ? "Syncing..." : "Sync now"}
      </button>
      {message && <p className="mt-2 text-xs opacity-70">{message}</p>}
    </div>
  );
}
