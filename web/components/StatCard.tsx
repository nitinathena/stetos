type Props = {
  label: string;
  value: string;
  accentVar?: string;
  sub?: string;
};

export default function StatCard({ label, value, accentVar, sub }: Props) {
  return (
    <div
      className="rounded-xl border p-5"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <p className="text-sm opacity-60">{label}</p>
      <p
        className="mt-1 text-3xl font-bold tabular-nums"
        style={{ color: accentVar ? `var(${accentVar})` : undefined }}
      >
        {value}
      </p>
      {sub && <p className="mt-1 text-xs opacity-50">{sub}</p>}
    </div>
  );
}
