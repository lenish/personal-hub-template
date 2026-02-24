import { Suspense } from "react";
import Link from "next/link";
import { getSpotifyListens, getSpotifyPlaylists } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Music, Clock, Disc3, ListMusic } from "lucide-react";
import type { SpotifyTrack, SpotifyPlaylist } from "@/lib/types";

export const dynamic = "force-dynamic";

function formatDuration(ms: number | null): string {
  if (!ms) return "";
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDays = Math.floor(diffHr / 24);
  if (diffDays === 1) return "yesterday";
  return `${diffDays}d ago`;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function groupByDay(tracks: SpotifyTrack[]): Map<string, SpotifyTrack[]> {
  const groups = new Map<string, SpotifyTrack[]>();
  for (const track of tracks) {
    const day = track.date.split("T")[0];
    const existing = groups.get(day);
    if (existing) {
      existing.push(track);
    } else {
      groups.set(day, [track]);
    }
  }
  return groups;
}

function TabNav({ active }: { active: "listens" | "playlists" }) {
  const tabs = [
    { key: "listens" as const, label: "Recent Listens", href: "/dash/music" },
    { key: "playlists" as const, label: "Playlists", href: "/dash/music?tab=playlists" },
  ];
  return (
    <div className="flex gap-1 rounded-lg bg-muted p-1">
      {tabs.map((t) => (
        <Link
          key={t.key}
          href={t.href}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
            active === t.key
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          {t.label}
        </Link>
      ))}
    </div>
  );
}

function PlaylistCard({ playlist }: { playlist: SpotifyPlaylist }) {
  return (
    <Link
      href={`/dash/music/playlist/${playlist.playlist_id}`}
      className="group flex items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-muted/50"
    >
      {playlist.image_url ? (
        <img
          src={playlist.image_url}
          alt={playlist.title}
          className="h-14 w-14 shrink-0 rounded object-cover"
          loading="lazy"
        />
      ) : (
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded bg-muted">
          <ListMusic className="h-6 w-6 text-muted-foreground" />
        </div>
      )}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium group-hover:underline">
          {playlist.title}
        </p>
        <p className="truncate text-xs text-muted-foreground">
          {playlist.track_count} track{playlist.track_count !== 1 ? "s" : ""}
          {playlist.owner_name ? ` \u00B7 ${playlist.owner_name}` : ""}
        </p>
      </div>
    </Link>
  );
}

function TrackRow({ track }: { track: SpotifyTrack }) {
  const spotifyUrl = track.track_id
    ? `https://open.spotify.com/track/${track.track_id}`
    : null;

  return (
    <div className="flex items-center gap-3 px-4 py-2.5 sm:px-6">
      {track.album_art_url ? (
        <img
          src={track.album_art_url}
          alt={track.album_name}
          className="h-10 w-10 shrink-0 rounded object-cover"
          loading="lazy"
        />
      ) : (
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-muted">
          <Music className="h-4 w-4 text-muted-foreground" />
        </div>
      )}
      <div className="min-w-0 flex-1">
        {spotifyUrl ? (
          <a
            href={spotifyUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="truncate text-sm font-medium hover:underline block"
          >
            {track.track_name}
          </a>
        ) : (
          <p className="truncate text-sm font-medium">{track.track_name}</p>
        )}
        <p className="truncate text-xs text-muted-foreground">
          {track.artist_name}
          {track.album_name ? ` \u00B7 ${track.album_name}` : ""}
        </p>
      </div>
      <div className="shrink-0 text-right">
        {track.duration_ms && (
          <p className="text-xs text-muted-foreground">
            {formatDuration(track.duration_ms)}
          </p>
        )}
        <p className="text-[11px] text-muted-foreground">
          {formatTimeAgo(track.played_at || track.date)}
        </p>
      </div>
    </div>
  );
}

async function PlaylistsTab() {
  const data = await getSpotifyPlaylists().catch(() => ({ source: "spotify", count: 0, data: [] }));
  const playlists = data.data;

  if (playlists.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-muted-foreground">
          No playlists synced yet. Enable Spotify to sync playlists.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">{playlists.length} playlists</p>
      <div className="grid gap-2 sm:grid-cols-2">
        {playlists.map((pl) => (
          <PlaylistCard key={pl.id} playlist={pl} />
        ))}
      </div>
    </div>
  );
}

async function ListensTab() {
  const data = await getSpotifyListens(7).catch(() => ({ source: "spotify", count: 0, data: [] }));
  const tracks = data.data;

  const now = new Date();
  const todayStr = now.toISOString().split("T")[0];
  const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  const todayCount = tracks.filter((t) => t.date.startsWith(todayStr)).length;
  const weekCount = tracks.filter((t) => new Date(t.date) >= weekAgo).length;
  const uniqueArtists = new Set(tracks.map((t) => t.artist_name)).size;
  const totalMs = tracks.reduce((sum, t) => sum + (t.duration_ms ?? 0), 0);
  const totalHours = Math.floor(totalMs / 3600000);
  const totalMinutes = Math.floor((totalMs % 3600000) / 60000);
  const grouped = groupByDay(tracks);

  return (
    <>
      <div className="grid gap-3 grid-cols-2 sm:grid-cols-4">
        <Card>
          <CardContent className="flex flex-col gap-1 py-3.5">
            <div className="flex items-center gap-1.5">
              <Music className="h-3.5 w-3.5 text-green-500" />
              <span className="text-xs text-muted-foreground">Today</span>
            </div>
            <span className="text-xl font-bold">{todayCount}</span>
            <span className="text-[11px] text-muted-foreground">tracks</span>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex flex-col gap-1 py-3.5">
            <div className="flex items-center gap-1.5">
              <Disc3 className="h-3.5 w-3.5 text-purple-500" />
              <span className="text-xs text-muted-foreground">This week</span>
            </div>
            <span className="text-xl font-bold">{weekCount}</span>
            <span className="text-[11px] text-muted-foreground">tracks</span>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex flex-col gap-1 py-3.5">
            <div className="flex items-center gap-1.5">
              <Music className="h-3.5 w-3.5 text-blue-500" />
              <span className="text-xs text-muted-foreground">Artists</span>
            </div>
            <span className="text-xl font-bold">{uniqueArtists}</span>
            <span className="text-[11px] text-muted-foreground">unique</span>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex flex-col gap-1 py-3.5">
            <div className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-amber-500" />
              <span className="text-xs text-muted-foreground">Listening</span>
            </div>
            <span className="text-xl font-bold">
              {totalHours > 0 ? `${totalHours}h` : ""}{totalMinutes}m
            </span>
            <span className="text-[11px] text-muted-foreground">this week</span>
          </CardContent>
        </Card>
      </div>

      {tracks.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-sm text-muted-foreground">
            No listening data yet. Connect Spotify and play some music!
          </CardContent>
        </Card>
      ) : (
        Array.from(grouped.entries()).map(([day, dayTracks]) => (
          <Card key={day}>
            <CardHeader className="pb-0">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {day === todayStr ? "Today" : formatDate(day)}
                <span className="ml-2 text-xs font-normal">
                  {dayTracks.length} track{dayTracks.length !== 1 ? "s" : ""}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 pt-2">
              <div className="divide-y divide-border/50">
                {dayTracks.map((track) => (
                  <TrackRow key={track.id} track={track} />
                ))}
              </div>
            </CardContent>
          </Card>
        ))
      )}

      <p className="pb-4 text-center text-xs text-muted-foreground">
        Data from Spotify. Showing last 7 days.
      </p>
    </>
  );
}

export default async function MusicPage({
  searchParams,
}: {
  searchParams: Promise<{ tab?: string }>;
}) {
  const { tab } = await searchParams;
  const active = tab === "playlists" ? "playlists" : "listens";

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Music</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Spotify listening history and playlists
        </p>
      </div>

      <TabNav active={active} />

      <Suspense
        fallback={
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-lg border bg-muted/50" />
            ))}
          </div>
        }
      >
        {active === "playlists" ? <PlaylistsTab /> : <ListensTab />}
      </Suspense>
    </div>
  );
}
