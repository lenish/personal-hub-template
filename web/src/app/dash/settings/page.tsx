export const dynamic = "force-dynamic";

import { auth } from "@/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getAllSyncStatus } from "@/lib/api";

const HEALTH_SOURCES = new Set(["whoop", "apple_health", "withings"]);

function formatSyncTime(iso: string | null): string {
  if (!iso) return "Never";
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function SyncSourceRow({
  name,
  status,
}: {
  name: string;
  status: { last_sync: string | null; status: string; items_synced: number; error: string | null };
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="capitalize">{name.replace(/_/g, " ")}</span>
      <div className="flex items-center gap-3">
        <span className="text-xs text-muted-foreground">
          {formatSyncTime(status.last_sync)}
        </span>
        <span className="text-sm text-muted-foreground">
          {status.items_synced} items
        </span>
        <Badge variant={status.error ? "destructive" : "secondary"}>
          {status.error ? "Error" : "Connected"}
        </Badge>
      </div>
    </div>
  );
}

export default async function SettingsPage() {
  const [session, syncStatus] = await Promise.all([auth(), getAllSyncStatus()]);

  const healthEntries = Object.entries(syncStatus).filter(([src]) =>
    HEALTH_SOURCES.has(src),
  );
  const collectorEntries = Object.entries(syncStatus).filter(
    ([src]) => !HEALTH_SOURCES.has(src),
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Name</span>
            <span>{session?.user?.name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Email</span>
            <span>{session?.user?.email}</span>
          </div>
        </CardContent>
      </Card>

      {healthEntries.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Health Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {healthEntries.map(([source, status]) => (
                <SyncSourceRow key={source} name={source} status={status} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {collectorEntries.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Data Collectors</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {collectorEntries.map(([source, status]) => (
                <SyncSourceRow key={source} name={source} status={status} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
