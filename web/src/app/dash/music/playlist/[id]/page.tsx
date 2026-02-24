import Link from "next/link";
import { notFound } from "next/navigation";
import { getSpotifyPlaylistTracks, getSpotifyPlaylists } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowLeft, Music, Clock, ExternalLink } from "lucide-react";
import type { SpotifyPlaylistTrack } from "@/lib/types";

export const dynamic = "force-dynamic";

function formatDuration(ms: number | null): string {
  if (!ms) return "";
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function formatAddedDate(dateStr: string): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function TrackRow({ track, index }: { track: SpotifyPlaylistTrack; index: number }) {
  const spotifyUrl = track.track_id
    ? `https://open.spotify.com/track/${track.track_id}`
    : null;

  return (
    <div className="flex items-center gap-3 px-4 py-2.5 sm:px-6">
      <span className="w-6 shrink-0 text-right text-xs text-muted-foreground">
        {index + 1}
      </span>
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
            className="block truncate text-sm font-medium hover:underline"
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
        {track.added_at && (
          <p className="text-[11px] text-muted-foreground">
            {formatAddedDate(track.added_at)}
          </p>
        )}
      </div>
    </div>
  );
}

export default async function PlaylistDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const [tracksData, playlistsData] = await Promise.all([
    getSpotifyPlaylistTracks(id).catch(() => null),
    getSpotifyPlaylists().catch(() => ({ source: "spotify", count: 0, data: [] })),
  ]);

  if (!tracksData) notFound();

  const playlist = playlistsData.data.find((p) => p.playlist_id === id);
  const tracks = tracksData.data;
  const totalMs = tracks.reduce((sum, t) => sum + (t.duration_ms ?? 0), 0);
  const totalMinutes = Math.floor(totalMs / 60000);
  const totalHours = Math.floor(totalMinutes / 60);
  const remainingMinutes = totalMinutes % 60;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Link
        href="/dash/music?tab=playlists"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Playlists
      </Link>

      <div className="flex items-start gap-4">
        {playlist?.image_url ? (
          <img
            src={playlist.image_url}
            alt={playlist.title}
            className="h-24 w-24 shrink-0 rounded-lg object-cover shadow-md sm:h-32 sm:w-32"
          />
        ) : (
          <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-lg bg-muted sm:h-32 sm:w-32">
            <Music className="h-8 w-8 text-muted-foreground" />
          </div>
        )}
        <div className="min-w-0 flex-1 space-y-1.5">
          <h1 className="text-xl font-bold sm:text-2xl">
            {playlist?.title ?? tracksData.data[0]?.playlist_name ?? "Playlist"}
          </h1>
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            {playlist?.owner_name && <span>{playlist.owner_name}</span>}
            <span>{tracks.length} tracks</span>
            {totalMs > 0 && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {totalHours > 0 ? `${totalHours}h ${remainingMinutes}m` : `${remainingMinutes}m`}
              </span>
            )}
          </div>
          {playlist?.playlist_id && (
            <a
              href={`https://open.spotify.com/playlist/${playlist.playlist_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
            >
              Open in Spotify
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
      </div>

      {tracks.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-sm text-muted-foreground">
            No tracks synced yet for this playlist.
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="divide-y divide-border/50">
              {tracks.map((track, i) => (
                <TrackRow key={track.id} track={track} index={i} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
