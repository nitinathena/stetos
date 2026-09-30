"use client";

import { useCallback, useState } from "react";

type Result = { filename: string; prediction: "normal" | "abnormal"; confidence: number; warning?: string };

import PredictionResult from "./PredictionResult";

export default function UploadForm() {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);

  const uploadFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".wav")) {
      setError("Please upload a .wav file.");
      return;
    }

    setIsUploading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const json = await res.json();

      if (!res.ok) {
        setError(json.error ?? "Something went wrong processing this recording.");
      } else {
        setResult(json);
      }
    } catch {
      setError("Could not reach the server. Check your connection and try again.");
    } finally {
      setIsUploading(false);
    }
  }, []);

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="text-2xl font-semibold tracking-tight">Upload a recording</h1>
      <p className="mt-1 text-sm opacity-70">
        Drag and drop a .wav heart sound recording, or select one below.
      </p>

      <label
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          const file = e.dataTransfer.files?.[0];
          if (file) uploadFile(file);
        }}
        className="mt-6 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 text-center transition-colors"
        style={{
          borderColor: isDragging ? "var(--brand)" : "var(--border)",
          background: isDragging ? "var(--surface-muted)" : "var(--surface)",
        }}
      >
        <input
          type="file"
          accept=".wav,audio/wav"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) uploadFile(file);
          }}
        />
        <span className="text-sm font-medium">
          {isUploading ? "Processing..." : "Click to select, or drop a .wav file here"}
        </span>
        <span className="mt-1 text-xs opacity-60">Max 4MB</span>
      </label>

      {error && (
        <div
          className="mt-6 rounded-lg border p-4 text-sm"
          style={{ borderColor: "var(--status-abnormal-border)", background: "var(--status-abnormal-bg)", color: "var(--status-abnormal)" }}
        >
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-3">
          <PredictionResult
            prediction={result.prediction}
            confidence={result.confidence}
            filename={result.filename}
          />
          {result.warning && (
            <p className="text-xs" style={{ color: "var(--warning-text)" }}>
              {result.warning}
            </p>
          )}
          <p
            className="rounded-lg border px-3 py-2 text-xs leading-snug"
            style={{ borderColor: "var(--warning-border)", background: "var(--warning-bg)", color: "var(--warning-text)" }}
          >
            Reminder: this is an experimental research prototype, not a medical
            diagnosis. Don&apos;t use this result to make any decision about a
            real heart condition.
          </p>
        </div>
      )}
    </div>
  );
}
