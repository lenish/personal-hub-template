"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfWeek(year: number, month: number) {
  return new Date(year, month, 1).getDay();
}

function formatDate(year: number, month: number, day: number) {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

interface MonthGridProps {
  eventDates?: Set<string>;
  selectedDate?: string;
  onDayClick?: (date: string) => void;
}

export function MonthGrid({ eventDates, selectedDate, onDayClick }: MonthGridProps) {
  const [current, setCurrent] = useState(() => new Date());
  const year = current.getFullYear();
  const month = current.getMonth();
  const today = new Date();
  const todayStr = formatDate(today.getFullYear(), today.getMonth(), today.getDate());

  const daysInMonth = getDaysInMonth(year, month);
  const firstDay = getFirstDayOfWeek(year, month);

  const prev = () => setCurrent(new Date(year, month - 1, 1));
  const next = () => setCurrent(new Date(year, month + 1, 1));

  const monthLabel = current.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle>{monthLabel}</CardTitle>
          <div className="flex items-center gap-1">
            <button
              onClick={prev}
              className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={next}
              className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-7 text-center text-xs font-medium text-muted-foreground">
          {DAYS.map((d) => (
            <div key={d} className="py-2">
              {d}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-7 text-center text-sm">
          {Array.from({ length: firstDay }).map((_, i) => (
            <div key={`empty-${i}`} className="py-2" />
          ))}
          {Array.from({ length: daysInMonth }).map((_, i) => {
            const day = i + 1;
            const dateStr = formatDate(year, month, day);
            const isToday = dateStr === todayStr;
            const isSelected = dateStr === selectedDate;
            const hasEvents = eventDates?.has(dateStr);

            return (
              <div
                key={day}
                onClick={() => onDayClick?.(dateStr)}
                className={`flex cursor-pointer flex-col items-center gap-0.5 py-1.5 transition-colors hover:bg-accent/50 rounded-md ${
                  isToday ? "font-bold text-primary" : "text-foreground"
                }`}
              >
                <span
                  className={`inline-flex h-7 w-7 items-center justify-center rounded-full ${
                    isToday
                      ? "bg-primary text-primary-foreground"
                      : isSelected
                        ? "ring-2 ring-primary"
                        : ""
                  }`}
                >
                  {day}
                </span>
                {hasEvents && (
                  <span className="h-1 w-1 rounded-full bg-primary" />
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
