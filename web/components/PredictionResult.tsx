type Props = {
  prediction: "normal" | "abnormal";
  confidence: number; // 0-1
  filename?: string;
};

export default function PredictionResult({ prediction, confidence, filename }: Props) {
  const isAbnormal = prediction === "abnormal";
  const pct = Math.round(confidence * 100);

  const colorVar = isAbnormal ? "--status-abnormal" : "--status-normal";
  const bgVar = isAbnormal ? "--status-abnormal-bg" : "--status-normal-bg";
  const borderVar = isAbnormal ? "--status-abnormal-border" : "--status-normal-border";

  return (
    <div
      className="rounded-xl border p-5"
      style={{
        background: `var(${bgVar})`,
        borderColor: `var(${borderVar})`,
      }}
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          {filename && <p className="text-xs opacity-60 mb-1">{filename}</p>}
          <span
            className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold"
            style={{ background: `var(${colorVar})`, color: "white" }}
          >
            {isAbnormal ? "Abnormal" : "Normal"}
          </span>
        </div>
        <span className="text-2xl font-bold tabular-nums" style={{ color: `var(${colorVar})` }}>
          {pct}%
        </span>
      </div>

      {/* Simple confidence meter - not a plot, so no legend/tooltip needed;
          the number beside it is the direct label. */}
      <div
        className="mt-3 h-2 w-full overflow-hidden rounded-full"
        role="meter"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Confidence: ${pct}%`}
        style={{ background: "var(--surface-muted)" }}
      >
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, background: `var(${colorVar})` }}
        />
      </div>
      <p className="mt-1.5 text-xs opacity-60">Model confidence</p>
    </div>
  );
}
