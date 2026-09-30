"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import type { DailyCounts } from "@/lib/dashboard-data";

// Colors match PredictionResult/badges elsewhere in the app - same
// normal/abnormal encoding everywhere, not a separate categorical palette.
const NORMAL_COLOR = "#059669";
const ABNORMAL_COLOR = "#dc2626";

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { value: number; dataKey: string }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-lg border px-3 py-2 text-xs shadow-sm"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <p className="mb-1 font-medium">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.dataKey === "normal" ? NORMAL_COLOR : ABNORMAL_COLOR }}>
          {p.dataKey === "normal" ? "Normal" : "Abnormal"}: {p.value}
        </p>
      ))}
    </div>
  );
}

export default function DistributionChart({ data }: { data: DailyCounts[] }) {
  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm opacity-60">
        No predictions yet - once recordings are synced or uploaded, daily
        normal/abnormal counts will show up here.
      </div>
    );
  }

  return (
    <div>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} barCategoryGap="30%" barGap={2}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12, fill: "currentColor" }}
            tickLine={false}
            axisLine={{ stroke: "var(--border)" }}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fontSize: 12, fill: "currentColor" }}
            tickLine={false}
            axisLine={false}
            width={28}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--surface-muted)" }} />
          <Legend
            formatter={(value) => (value === "normal" ? "Normal" : "Abnormal")}
            wrapperStyle={{ fontSize: 12 }}
          />
          <Bar dataKey="normal" fill={NORMAL_COLOR} radius={[4, 4, 0, 0]} maxBarSize={28} />
          <Bar dataKey="abnormal" fill={ABNORMAL_COLOR} radius={[4, 4, 0, 0]} maxBarSize={28} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
