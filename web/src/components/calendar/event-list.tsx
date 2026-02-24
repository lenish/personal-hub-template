"use client";

import { useState } from "react";
import {
  CalendarDays,
  Clock,
  MapPin,
  Users,
  ChevronDown,
  ExternalLink,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CollectorItem } from "@/lib/types";

interface EventListProps {
  events: CollectorItem[];
  selectedDate: string;
  timezone?: string;
}

function formatTime(isoString: unknown, tz: string): string | null {
  if (typeof isoString !== "string") return null;
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return null;
    return d.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
      timeZone: tz,
    });
  } catch {
    return null;
  }
}

function formatDisplayDate(dateStr: string): string {
  const [year, month, day] = dateStr.split("-").map(Number);
  const d = new Date(year, month - 1, day);
  return d.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export function EventList({ events, selectedDate, timezone = "UTC" }: EventListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const dayEvents = events
    .filter((e) => {
      const eventDate = new Date(e.date).toLocaleDateString("en-CA", { timeZone: timezone });
      return eventDate === selectedDate;
    })
    .sort((a, b) => {
      const aStart = (a.start as string) ?? a.date;
      const bStart = (b.start as string) ?? b.date;
      return aStart.localeCompare(bStart);
    });

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <CalendarDays className="h-4 w-4" />
          {formatDisplayDate(selectedDate)}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {dayEvents.length === 0 ? (
          <p className="text-sm text-muted-foreground">No events</p>
        ) : (
          <div className="space-y-2">
            {dayEvents.map((event) => {
              const startTime = formatTime(event.start, timezone);
              const endTime = formatTime(event.end, timezone);
              const location = event.location as string | undefined;
              const attendeeCount = event.attendee_count as number | undefined;
              const hangoutLink = event.hangout_link as string | undefined;
              const sourceUrl = event.source_url as string | undefined;
              const isExpanded = expandedId === event.id;
              const timeRange =
                startTime && endTime
                  ? `${startTime} - ${endTime}`
                  : startTime ?? "All day";
              const titleClean = event.title?.replace(/\s*\(\d{4}-\d{2}-\d{2}\)$/, "") ?? "";

              return (
                <div key={event.id} className="rounded-md border">
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : event.id)}
                    className="flex w-full gap-3 p-3 text-left transition-colors hover:bg-accent/50"
                  >
                    <div className="flex shrink-0 items-start pt-0.5 text-muted-foreground">
                      <Clock className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium leading-tight">
                        {titleClean}
                      </p>
                      <p className="text-xs text-muted-foreground">{timeRange}</p>
                    </div>
                    <ChevronDown
                      className={`mt-0.5 h-4 w-4 shrink-0 text-muted-foreground transition-transform ${
                        isExpanded ? "rotate-180" : ""
                      }`}
                    />
                  </button>

                  {isExpanded && (
                    <div className="border-t px-3 py-3 space-y-2">
                      <div className="space-y-1.5 text-xs text-muted-foreground">
                        {location && (
                          <div className="flex items-center gap-2">
                            <MapPin className="h-3 w-3 shrink-0" />
                            <span className="truncate">{location}</span>
                          </div>
                        )}
                        {attendeeCount != null && attendeeCount > 0 && (
                          <div className="flex items-center gap-2">
                            <Users className="h-3 w-3 shrink-0" />
                            <span>{attendeeCount} attendees</span>
                          </div>
                        )}
                        {event.content && (
                          <p className="whitespace-pre-line pt-1 text-sm text-foreground/90">
                            {event.content}
                          </p>
                        )}
                      </div>
                      <div className="flex gap-2">
                        {sourceUrl && (
                          <a
                            href={sourceUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                          >
                            Open in Calendar
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                        {hangoutLink && (
                          <a
                            href={hangoutLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium transition-colors hover:bg-accent"
                          >
                            Join Meet
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    </div>
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
