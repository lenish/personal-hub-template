// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Health Summary
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface HealthSummaryResponse {
  days: number;
  total_items: number;
  data: Record<string, HealthSummaryItem[]>;
}

export interface HealthSummaryItem {
  date: string;
  title: string;
  // Whoop recovery
  recovery_score?: number;
  hrv_rmssd?: number;
  resting_hr?: number;
  spo2?: number;
  skin_temp?: number;
  // Whoop sleep
  performance?: number;
  efficiency?: number;
  respiratory_rate?: number;
  total_sleep_hours?: number;
  rem_hours?: number;
  deep_hours?: number;
  disturbances?: number;
  // Whoop workout
  sport?: string;
  strain?: number;
  avg_hr?: number;
  max_hr?: number;
  calories_kj?: number;
  distance_m?: number;
  // Withings body composition
  weight?: number;
  fat_ratio?: number;
  fat_mass_weight?: number;
  fat_free_mass?: number;
  muscle_mass?: number;
  bone_mass?: number;
  hydration?: number;
  // Withings blood pressure
  systolic_bp?: number;
  diastolic_bp?: number;
  heart_pulse?: number;
  // Apple Health
  value?: number;
  unit?: string;
  agg?: string;
  data_points?: number;
  raw?: Record<string, unknown>;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Whoop
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface WhoopResponse {
  source: string;
  count: number;
  data: WhoopItem[];
}

export interface WhoopItem {
  id: string;
  type: "recovery" | "sleep" | "workout";
  date: string;
  title: string;
  recovery_score?: number;
  hrv_rmssd?: number;
  resting_hr?: number;
  spo2?: number;
  skin_temp?: number;
  performance?: number;
  efficiency?: number;
  respiratory_rate?: number;
  total_sleep_hours?: number;
  rem_hours?: number;
  deep_hours?: number;
  disturbances?: number;
  sport?: string;
  strain?: number;
  avg_hr?: number;
  max_hr?: number;
  calories_kj?: number;
  distance_m?: number;
  raw?: Record<string, unknown>;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Apple Health
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface AppleHealthResponse {
  source: string;
  count: number;
  data: AppleHealthItem[];
}

export interface AppleHealthItem {
  id: string;
  type: string;
  date: string;
  title: string;
  value: number;
  unit: string;
  agg: string;
  data_points: number;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Withings
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface WithingsResponse {
  source: string;
  count: number;
  data: WithingsItem[];
}

export interface WithingsItem {
  id: string;
  type: "body_composition" | "blood_pressure" | "sleep";
  date: string;
  title: string;
  weight?: number;
  height?: number;
  fat_free_mass?: number;
  fat_ratio?: number;
  fat_mass_weight?: number;
  muscle_mass?: number;
  hydration?: number;
  bone_mass?: number;
  systolic_bp?: number;
  diastolic_bp?: number;
  heart_pulse?: number;
  total_sleep_hours?: number;
  deep_hours?: number;
  rem_hours?: number;
  light_hours?: number;
  sleep_score?: number;
  raw?: Record<string, unknown>;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Collector (Generic)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface CollectorItem {
  id: string;
  type: string;
  date: string;
  title: string;
  content?: string | null;
  [key: string]: unknown;
}

export interface CollectorDataResponse {
  source: string;
  count: number;
  data: CollectorItem[];
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Sync Status
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface SyncStatusResponse {
  [source: string]: {
    last_sync: string | null;
    status: string;
    items_synced: number;
    error: string | null;
  };
}

export type CollectorSyncStatusResponse = SyncStatusResponse;

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Spotify
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface SpotifyTrack {
  id: string;
  type: string;
  date: string;
  title: string;
  track_id: string;
  track_name: string;
  artist_name: string;
  album_name: string;
  album_art_url: string | null;
  duration_ms: number | null;
  explicit: boolean;
  played_at: string;
  context_type: string | null;
  context_uri: string | null;
}

export interface SpotifyListensResponse {
  source: string;
  count: number;
  data: SpotifyTrack[];
}

export interface SpotifyPlaylist {
  id: string;
  type: string;
  date: string;
  title: string;
  playlist_id: string;
  track_count: number;
  image_url: string | null;
  owner_name: string;
  owner_id: string;
  public: boolean | null;
  collaborative: boolean;
  snapshot_id: string;
}

export interface SpotifyPlaylistsResponse {
  source: string;
  count: number;
  data: SpotifyPlaylist[];
}

export interface SpotifyPlaylistTrack {
  id: string;
  type: string;
  date: string;
  title: string;
  track_id: string;
  track_name: string;
  artist_name: string;
  album_name: string;
  album_art_url: string | null;
  duration_ms: number | null;
  explicit: boolean;
  added_at: string;
  added_by: string;
  playlist_id: string;
  playlist_name: string;
  position: number;
}

export interface SpotifyPlaylistTracksResponse {
  source: string;
  playlist_id: string;
  count: number;
  data: SpotifyPlaylistTrack[];
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// System
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface ServerResourcesResponse {
  cpu: { usage_pct: number; cores: number; load_avg: number[] };
  memory: { total_mb: number; used_mb: number; usage_pct: number };
  disk: { total_gb: number; used_gb: number; usage_pct: number };
  uptime_seconds: number;
  timestamp: string;
}

export interface InternalService {
  name: string;
  port: number | null;
  status: "ok" | "error" | "unreachable";
  response_ms: number | null;
}

export interface ExternalApiStatus {
  status: string;
  last_sync: string | null;
  items_synced: number;
  error: string | null;
}

export interface CredentialStatus {
  name: string;
  group: string;
  present: boolean;
}

export interface ServiceStatusResponse {
  internal_services: InternalService[];
  external_apis: Record<string, ExternalApiStatus>;
  credentials: CredentialStatus[];
  database: { status: string; response_ms: number | null };
  timestamp: string;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Google Calendar
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export interface CalendarEvent {
  id: string;
  type: string;
  date: string;
  title: string;
  start_time: string;
  end_time: string;
  location?: string | null;
  description?: string | null;
  calendar_id: string;
  all_day: boolean;
}

export interface CalendarEventsResponse {
  source: string;
  count: number;
  data: CalendarEvent[];
}
