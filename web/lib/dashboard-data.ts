import "server-only";
import { getSupabaseServerClient, PREDICTIONS_TABLE } from "./supabase-server";

export type PredictionRow = {
  id: number;
  filename: string;
  source: "supabase_sync" | "user_upload";
  prediction: "normal" | "abnormal";
  confidence: number;
  created_at: string;
};

export type DailyCounts = { date: string; normal: number; abnormal: number };

export type DashboardData = {
  totalCount: number;
  normalCount: number;
  abnormalCount: number;
  lastSyncTime: string | null;
  recent: PredictionRow[];
  dailyCounts: DailyCounts[];
};

// Fetches everything the dashboard home page needs in one place. Scale
// note: the daily-counts chart aggregates in JS over up to 2000 recent
// rows rather than a SQL GROUP BY - fine at this project's scale; if this
// table grows large, replace with a Postgres view or RPC that aggregates
// server-side instead.
export async function getDashboardData(): Promise<DashboardData> {
  const supabase = getSupabaseServerClient();

  const [totalRes, normalRes, abnormalRes, lastSyncRes, recentRes, forChartRes] =
    await Promise.all([
      supabase.from(PREDICTIONS_TABLE).select("*", { count: "exact", head: true }),
      supabase
        .from(PREDICTIONS_TABLE)
        .select("*", { count: "exact", head: true })
        .eq("prediction", "normal"),
      supabase
        .from(PREDICTIONS_TABLE)
        .select("*", { count: "exact", head: true })
        .eq("prediction", "abnormal"),
      supabase
        .from(PREDICTIONS_TABLE)
        .select("created_at")
        .eq("source", "supabase_sync")
        .order("created_at", { ascending: false })
        .limit(1),
      supabase
        .from(PREDICTIONS_TABLE)
        .select("*")
        .order("created_at", { ascending: false })
        .limit(20),
      supabase
        .from(PREDICTIONS_TABLE)
        .select("created_at, prediction")
        .order("created_at", { ascending: false })
        .limit(2000),
    ]);

  const dailyMap = new Map<string, { normal: number; abnormal: number }>();
  for (const row of forChartRes.data ?? []) {
    const day = row.created_at.slice(0, 10); // YYYY-MM-DD
    const entry = dailyMap.get(day) ?? { normal: 0, abnormal: 0 };
    if (row.prediction === "normal") entry.normal += 1;
    else entry.abnormal += 1;
    dailyMap.set(day, entry);
  }
  const dailyCounts: DailyCounts[] = Array.from(dailyMap.entries())
    .map(([date, counts]) => ({ date, ...counts }))
    .sort((a, b) => a.date.localeCompare(b.date));

  return {
    totalCount: totalRes.count ?? 0,
    normalCount: normalRes.count ?? 0,
    abnormalCount: abnormalRes.count ?? 0,
    lastSyncTime: lastSyncRes.data?.[0]?.created_at ?? null,
    recent: (recentRes.data as PredictionRow[]) ?? [],
    dailyCounts,
  };
}
