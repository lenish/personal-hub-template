export const dynamic = "force-dynamic";

import {
  getHealthSummary,
  getAppleHealthData,
  getAllSyncStatus,
} from "@/lib/api";
import type { HealthSummaryResponse } from "@/lib/types";
import { HealthSummaryCard } from "@/components/health/health-summary-card";
import { AllSyncStatus } from "@/components/dashboard/all-sync-status";

export default async function DashboardPage() {
  const [summary, steps, syncStatus] = await Promise.all([
    getHealthSummary(7).catch(
      (): HealthSummaryResponse => ({ days: 7, total_items: 0, data: {} }),
    ),
    getAppleHealthData(7, "step_count").catch(() => ({
      source: "apple_health",
      count: 0,
      data: [],
    })),
    getAllSyncStatus().catch(() => ({})),
  ]);

  const recoveryData = summary.data.recovery ?? [];
  const sleepData = summary.data.sleep ?? [];
  const latestRecovery = recoveryData[0];
  const latestSleep = sleepData[0];
  const latestSteps = steps.data[0];

  return (
    <div className="min-w-0 space-y-6 overflow-hidden">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Health Quick Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <HealthSummaryCard
          title="Recovery"
          value={latestRecovery?.recovery_score ?? "\u2014"}
          unit="%"
        />
        <HealthSummaryCard
          title="Resting HR"
          value={latestRecovery?.resting_hr ?? "\u2014"}
          unit="bpm"
        />
        <HealthSummaryCard
          title="Sleep"
          value={
            latestSleep?.total_sleep_hours
              ? latestSleep.total_sleep_hours.toFixed(1)
              : "\u2014"
          }
          unit="hrs"
        />
        <HealthSummaryCard
          title="Steps"
          value={
            latestSteps?.value
              ? Math.round(latestSteps.value).toLocaleString()
              : "\u2014"
          }
        />
      </div>

      {/* All Data Sources */}
      <AllSyncStatus syncStatus={syncStatus} />
    </div>
  );
}
