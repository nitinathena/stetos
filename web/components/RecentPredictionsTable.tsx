import type { PredictionRow } from "@/lib/dashboard-data";

function formatTimestamp(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function SourceBadge({ source }: { source: PredictionRow["source"] }) {
  const label = source === "user_upload" ? "Upload" : "Sync";
  return (
    <span
      className="rounded-full px-2 py-0.5 text-xs font-medium"
      style={{ background: "var(--surface-muted)", color: "currentColor", opacity: 0.75 }}
    >
      {label}
    </span>
  );
}

function PredictionCell({ prediction }: { prediction: PredictionRow["prediction"] }) {
  const isAbnormal = prediction === "abnormal";
  const colorVar = isAbnormal ? "--status-abnormal" : "--status-normal";
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className="h-2 w-2 shrink-0 rounded-full"
        style={{ background: `var(${colorVar})` }}
        aria-hidden="true"
      />
      <span style={{ color: `var(${colorVar})` }} className="font-medium capitalize">
        {prediction}
      </span>
    </span>
  );
}

export default function RecentPredictionsTable({ rows }: { rows: PredictionRow[] }) {
  if (rows.length === 0) {
    return (
      <p className="py-8 text-center text-sm opacity-60">
        No predictions logged yet.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b" style={{ borderColor: "var(--border)" }}>
            <th className="py-2 pr-4 font-medium opacity-60">Filename</th>
            <th className="py-2 pr-4 font-medium opacity-60">Prediction</th>
            <th className="py-2 pr-4 font-medium opacity-60">Confidence</th>
            <th className="py-2 pr-4 font-medium opacity-60">Source</th>
            <th className="py-2 pr-4 font-medium opacity-60">Time</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b last:border-0" style={{ borderColor: "var(--border)" }}>
              <td className="py-2.5 pr-4 font-mono text-xs">{row.filename}</td>
              <td className="py-2.5 pr-4">
                <PredictionCell prediction={row.prediction} />
              </td>
              <td className="py-2.5 pr-4 tabular-nums">{Math.round(row.confidence * 100)}%</td>
              <td className="py-2.5 pr-4">
                <SourceBadge source={row.source} />
              </td>
              <td className="py-2.5 pr-4 opacity-70">{formatTimestamp(row.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
