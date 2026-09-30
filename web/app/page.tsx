import { getDashboardData } from "@/lib/dashboard-data";
import StatCard from "@/components/StatCard";
import DistributionChart from "@/components/DistributionChart";
import RecentPredictionsTable from "@/components/RecentPredictionsTable";
import SyncNowButton from "@/components/SyncNowButton";

export const dynamic = "force-dynamic"; // always fetch fresh predictions, never cache this page

function formatLastSync(iso: string | null) {
  if (!iso) return "Never";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default async function Home() {
  let data;
  try {
    data = await getDashboardData();
  } catch (e) {
    return (
      <div
        className="rounded-xl border p-8 text-center"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <h1 className="text-xl font-semibold">Dashboard not connected yet</h1>
        <p className="mt-2 text-sm opacity-70">
          {e instanceof Error ? e.message : "Could not load dashboard data."}
        </p>
        <p className="mt-1 text-xs opacity-50">
          Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (see .env.example) and
          run web/supabase/schema.sql, then reload.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm opacity-60">Overview of all processed heart sound recordings.</p>
        </div>
        <SyncNowButton />
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Total processed" value={data.totalCount.toLocaleString()} />
        <StatCard label="Normal" value={data.normalCount.toLocaleString()} accentVar="--status-normal" />
        <StatCard label="Abnormal" value={data.abnormalCount.toLocaleString()} accentVar="--status-abnormal" />
        <StatCard label="Last sync" value={formatLastSync(data.lastSyncTime)} />
      </div>

      <div
        className="rounded-xl border p-5"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <h2 className="text-sm font-semibold">Normal vs. abnormal over time</h2>
        <div className="mt-4">
          <DistributionChart data={data.dailyCounts} />
        </div>
      </div>

      <div
        className="rounded-xl border p-5"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <h2 className="text-sm font-semibold">Recent predictions</h2>
        <div className="mt-4">
          <RecentPredictionsTable rows={data.recent} />
        </div>
      </div>
    </div>
  );
}
