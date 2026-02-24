import type {
  HealthSummaryResponse,
  WhoopResponse,
  AppleHealthResponse,
  WithingsResponse,
  SyncStatusResponse,
  CollectorSyncStatusResponse,
  CollectorDataResponse,
  SpotifyListensResponse,
  SpotifyPlaylistsResponse,
  SpotifyPlaylistTracksResponse,
  ServerResourcesResponse,
  ServiceStatusResponse,
  CalendarEventsResponse,
} from "./types";

const API_BASE = process.env.API_BASE_URL ?? "http://localhost:8000";
const API_KEY = process.env.API_KEY ?? "";

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    ...(init?.headers as Record<string, string>),
  };
  if (API_KEY) {
    headers["X-API-Key"] = API_KEY;
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    next: { revalidate: 300 },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// Health
export function getHealthSummary(days = 7) {
  return fetchApi<HealthSummaryResponse>(
    `/api/health/summary?days=${days}`,
  );
}

export function getWhoopData(days = 14, itemType?: string) {
  const params = new URLSearchParams({ days: String(days) });
  if (itemType) params.set("item_type", itemType);
  return fetchApi<WhoopResponse>(`/api/health/whoop?${params}`);
}

export function getAppleHealthData(days = 7, metric?: string) {
  const params = new URLSearchParams({ days: String(days) });
  if (metric) params.set("metric", metric);
  return fetchApi<AppleHealthResponse>(`/api/health/apple?${params}`);
}

export function getWithingsData(days = 30, itemType?: string) {
  const params = new URLSearchParams({ days: String(days) });
  if (itemType) params.set("item_type", itemType);
  return fetchApi<WithingsResponse>(`/api/health/withings?${params}`);
}

export function getSyncStatus() {
  return fetchApi<SyncStatusResponse>("/api/health/sync-status");
}

// Collectors
export function getCollectorsSyncStatus() {
  return fetchApi<CollectorSyncStatusResponse>("/api/collectors/sync-status");
}

export function getCollectorData(source: string, days = 7, itemType?: string) {
  const params = new URLSearchParams({ days: String(days) });
  if (itemType) params.set("item_type", itemType);
  return fetchApi<CollectorDataResponse>(
    `/api/collectors/${source}?${params}`,
  );
}

// Spotify
export function getSpotifyListens(days = 7) {
  return fetchApi<SpotifyListensResponse>(
    `/api/collectors/spotify?days=${days}&item_type=listen`,
  );
}

export function getSpotifyPlaylists() {
  return fetchApi<SpotifyPlaylistsResponse>(
    `/api/collectors/spotify?days=3650&item_type=playlist`,
    { next: { revalidate: 0 } },
  );
}

export function getSpotifyPlaylistTracks(playlistId: string) {
  return fetchApi<SpotifyPlaylistTracksResponse>(
    `/api/collectors/spotify/playlists/${playlistId}/tracks`,
    { next: { revalidate: 0 } },
  );
}

// Calendar
export function getCalendarEvents(days = 14) {
  return fetchApi<CalendarEventsResponse>(
    `/api/collectors/google_calendar?days=${days}`,
  );
}

// System
export function getServerResources() {
  return fetchApi<ServerResourcesResponse>("/api/system/resources", {
    next: { revalidate: 0 },
  });
}

export function getServiceStatus() {
  return fetchApi<ServiceStatusResponse>("/api/system/services", {
    next: { revalidate: 0 },
  });
}

// Combined sync status
export async function getAllSyncStatus() {
  const [health, collectors] = await Promise.all([
    getSyncStatus().catch(() => ({} as SyncStatusResponse)),
    getCollectorsSyncStatus().catch(() => ({} as CollectorSyncStatusResponse)),
  ]);
  return { ...health, ...collectors };
}
