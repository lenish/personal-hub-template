import type { SyncStatusResponse } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Database } from "lucide-react";

interface AllSyncStatusProps {
  syncStatus: SyncStatusResponse;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function getStatusInfo(status: {
  status: string;
  last_sync: string | null;
  error: string | null;
}): { color: string; label: string } {
  if (status.status === "error" || status.error) {
    return { color: "bg-red-500", label: "Error" };
  }
  if (status.status === "collecting" || status.status === "syncing") {
    return { color: "bg-yellow-500 animate-pulse", label: "Syncing" };
  }
  if (!status.last_sync) {
    return { color: "bg-gray-400", label: "Never synced" };
  }
  const ageMs = Date.now() - new Date(status.last_sync).getTime();
  const ageHours = ageMs / (1000 * 60 * 60);
  if (ageHours > 2) {
    return { color: "bg-yellow-500", label: "Stale" };
  }
  return { color: "bg-green-500", label: "OK" };
}

export function AllSyncStatus({ syncStatus }: AllSyncStatusProps) {
  const entries = Object.entries(syncStatus);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Database className="h-4 w-4 text-muted-foreground" />
          Data Sources
        </CardTitle>
      </CardHeader>
      <CardContent>
        {entries.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No data sources configured
          </p>
        ) : (
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {entries.map(([source, status]) => {
              const info = getStatusInfo(status);
              return (
                <div
                  key={source}
                  className="flex items-center gap-3 rounded-md border px-3 py-2"
                >
                  <span
                    className={`h-2.5 w-2.5 shrink-0 rounded-full ${info.color}`}
                    title={info.label}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium capitalize">
                      {source.replace(/_/g, " ")}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {status.items_synced} items
                      {status.last_sync
                        ? ` · ${timeAgo(status.last_sync)}`
                        : ""}
                    </p>
                  </div>
                  {status.error && (
                    <span
                      className="shrink-0 text-xs text-red-500"
                      title={status.error}
                    >
                      !
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
