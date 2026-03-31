import { Loader2 } from "lucide-react";
import { AdminStatsCards } from "@/components/admin/admin-stats-cards";
import { AdminCostChart } from "@/components/admin/admin-cost-chart";
import { AdminJobTable } from "@/components/admin/admin-job-table";
import { useAdminStats, useAdminDailyStats } from "@/hooks/use-admin-stats";

export default function AdminPage() {
  const { data: stats, isLoading: statsLoading } = useAdminStats();
  const { data: dailyStats, isLoading: dailyLoading } = useAdminDailyStats(30);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <h1 className="text-2xl font-bold">관리자</h1>

      {/* Stats Cards */}
      {statsLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : stats ? (
        <AdminStatsCards stats={stats} />
      ) : null}

      {/* Cost Chart */}
      {dailyLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : dailyStats ? (
        <AdminCostChart data={dailyStats} />
      ) : null}

      {/* Job Table */}
      <AdminJobTable />
    </div>
  );
}
