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
      const json = await res.json();
      if (!res.ok) {
        setMessage(json.error ?? "Sync failed");
      } else {
        setMessage(
          `Synced ${json.processed?.length ?? 0} new recording(s) ` +
          `(${json.bucket_file_count} total in bucket, ${json.already_synced_count} already synced).`
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
