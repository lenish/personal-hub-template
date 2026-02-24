"use client";

import { useEffect, useMemo, useState } from "react";
import { Globe } from "lucide-react";
import { MonthGrid } from "@/components/calendar/month-grid";
import { EventList } from "@/components/calendar/event-list";
import type { CollectorItem } from "@/lib/types";

const TIMEZONES = [
  { label: "UTC", value: "UTC" },
  { label: "Seoul (KST)", value: "Asia/Seoul" },
  { label: "Tokyo (JST)", value: "Asia/Tokyo" },
  { label: "Singapore (SGT)", value: "Asia/Singapore" },
  { label: "New York (ET)", value: "America/New_York" },
  { label: "San Francisco (PT)", value: "America/Los_Angeles" },
  { label: "London (GMT)", value: "Europe/London" },
] as const;

function todayStr(tz: string) {
  return new Date().toLocaleDateString("en-CA", { timeZone: tz });
}

export default function CalendarPage() {
  const [events, setEvents] = useState<CollectorItem[]>([]);
  const [timezone, setTimezone] = useState("UTC");
  const [selectedDate, setSelectedDate] = useState(() => todayStr("UTC"));

  useEffect(() => {
    fetch("/api/collectors/google_calendar?days=30")
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status}`);
        return res.json();
      })
      .then((data) => setEvents(data.data ?? []))
      .catch(() => setEvents([]));
  }, []);

  useEffect(() => {
    setSelectedDate(todayStr(timezone));
  }, [timezone]);

  const eventDates = useMemo(
    () =>
      new Set(
        events.map((e) =>
          new Date(e.date).toLocaleDateString("en-CA", {
            timeZone: timezone,
          }),
        ),
      ),
    [events, timezone],
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Calendar</h1>
        <div className="flex items-center gap-2">
          <Globe className="h-4 w-4 text-muted-foreground" />
          <select
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="rounded-md border bg-background px-2 py-1 text-sm text-foreground"
          >
            {TIMEZONES.map((tz) => (
              <option key={tz.value} value={tz.value}>
                {tz.label}
              </option>
            ))}
          </select>
        </div>
      </div>
      <MonthGrid
        eventDates={eventDates}
        selectedDate={selectedDate}
        onDayClick={setSelectedDate}
      />
      <EventList events={events} selectedDate={selectedDate} timezone={timezone} />
    </div>
  );
}
