export const dynamic = "force-dynamic";

import { getHealthSummary, getAppleHealthData } from "@/lib/api";
import type { HealthSummaryResponse } from "@/lib/types";
import { HealthSummaryCard } from "@/components/health/health-summary-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default async function HealthPage() {
  const [summary, steps] = await Promise.all([
    getHealthSummary(14).catch(
      (): HealthSummaryResponse => ({ days: 14, total_items: 0, data: {} }),
    ),
    getAppleHealthData(14, "step_count").catch(() => ({
      source: "apple_health",
      count: 0,
      data: [],
    })),
  ]);

  const recoveryData = summary.data.recovery ?? [];
  const sleepData = summary.data.sleep ?? [];
  const workoutData = summary.data.workout ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Health</h1>

      {/* Quick Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <HealthSummaryCard
          title="Recovery"
          value={recoveryData[0]?.recovery_score ?? "\u2014"}
          unit="%"
        />
        <HealthSummaryCard
          title="HRV"
          value={recoveryData[0]?.hrv_rmssd?.toFixed(0) ?? "\u2014"}
          unit="ms"
        />
        <HealthSummaryCard
          title="Sleep"
          value={
            sleepData[0]?.total_sleep_hours
              ? sleepData[0].total_sleep_hours.toFixed(1)
              : "\u2014"
          }
          unit="hrs"
        />
        <HealthSummaryCard
          title="Steps"
          value={
            steps.data[0]?.value
              ? Math.round(steps.data[0].value).toLocaleString()
              : "\u2014"
          }
        />
      </div>

      {/* Recovery History */}
      {recoveryData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recovery History (14 days)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recoveryData.map((item, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-md border px-3 py-2"
                >
                  <span className="text-sm">{item.date}</span>
                  <div className="flex items-center gap-4 text-sm">
                    <span>Recovery: {item.recovery_score ?? "\u2014"}%</span>
                    <span>HRV: {item.hrv_rmssd?.toFixed(0) ?? "\u2014"}</span>
                    <span>RHR: {item.resting_hr ?? "\u2014"}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sleep History */}
      {sleepData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Sleep History (14 days)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {sleepData.map((item, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-md border px-3 py-2"
                >
                  <span className="text-sm">{item.date}</span>
                  <div className="flex items-center gap-4 text-sm">
                    <span>
                      Total: {item.total_sleep_hours?.toFixed(1) ?? "\u2014"}h
                    </span>
                    <span>
                      Performance: {item.performance ?? "\u2014"}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Workout History */}
      {workoutData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Workouts (14 days)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {workoutData.map((item, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-md border px-3 py-2"
                >
                  <span className="text-sm">{item.date}</span>
                  <div className="flex items-center gap-4 text-sm">
                    <span>{item.sport ?? "Unknown"}</span>
                    <span>Strain: {item.strain?.toFixed(1) ?? "\u2014"}</span>
                    <span>Calories: {item.calories_kj ?? "\u2014"} kJ</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {summary.total_items === 0 && steps.count === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-sm text-muted-foreground">
            No health data yet. Connect Whoop or Apple Health to get started.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
