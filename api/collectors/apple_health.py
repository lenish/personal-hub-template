"""Apple Health collector — webhook receiver for Health Auto Export app.

Receives push data from the iOS app, stores raw metrics + aggregated
daily data into the DB.
"""

import hashlib
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from api.collectors.base import BaseCollector
from api.config import settings

logger = logging.getLogger(__name__)

# Metrics and their aggregation method
METRICS_CONFIG = {
    "step_count": {"agg": "sum", "unit": "steps"},
    "walking_running_distance": {"agg": "sum", "unit": "km", "factor": 0.001},
    "apple_exercise_time": {"agg": "sum", "unit": "min"},
    "flights_climbed": {"agg": "sum", "unit": "floors"},
    "heart_rate": {"agg": "avg", "unit": "bpm"},
    "resting_heart_rate": {"agg": "avg", "unit": "bpm"},
    "heart_rate_variability": {"agg": "avg", "unit": "ms"},
    "blood_oxygen_saturation": {"agg": "avg", "unit": "%"},
    "respiratory_rate": {"agg": "avg", "unit": "breaths/min"},
    "vo2_max": {"agg": "avg", "unit": "mL/kg/min"},
    "walking_heart_rate_average": {"agg": "avg", "unit": "bpm"},
    "weight_body_mass": {"agg": "avg", "unit": "kg"},
    "body_fat_percentage": {"agg": "avg", "unit": "%"},
    "body_mass_index": {"agg": "avg", "unit": "kg/m2"},
    "lean_body_mass": {"agg": "avg", "unit": "kg"},
    "basal_energy_burned": {"agg": "sum", "unit": "kcal", "factor": 1 / 4.184},
    "active_energy": {"agg": "sum", "unit": "kcal", "factor": 1 / 4.184},
    "walking_speed": {"agg": "avg", "unit": "km/h"},
    "walking_step_length": {"agg": "avg", "unit": "cm"},
    "walking_double_support_percentage": {"agg": "avg", "unit": "%"},
    "walking_asymmetry_percentage": {"agg": "avg", "unit": "%"},
    "sleep_analysis": {"agg": "sum", "unit": "min"},
    "time_in_daylight": {"agg": "sum", "unit": "min"},
    "mindful_minutes": {"agg": "sum", "unit": "min"},
    "apple_stand_time": {"agg": "sum", "unit": "min"},
}


class AppleHealthCollector(BaseCollector):
    """Processes incoming Apple Health webhook data into daily aggregates."""

    source = "apple_health"
    category = "health"

    def __init__(self):
        self._local_tz = ZoneInfo(settings.timezone)
        self._utc_offset = datetime.now(self._local_tz).utcoffset()

    async def collect(self, session: AsyncSession) -> int:
        raise NotImplementedError("Apple Health uses push via process_webhook()")

    async def process_webhook(self, session: AsyncSession, payload: dict) -> int:
        """Process incoming Health Auto Export payload, aggregate by day, upsert."""
        local_tz = self._local_tz
        utc_offset_str = datetime.now(local_tz).strftime("%z")
        # Format: "+0800" -> "+08:00"
        tz_offset = f"{utc_offset_str[:3]}:{utc_offset_str[3:]}"

        metrics = {m["name"]: m for m in payload.get("data", {}).get("metrics", [])}
        full_items = []

        # Collect all timestamps across all metrics to detect boundary dates
        all_minutes_by_date: dict[str, set[str]] = defaultdict(set)

        for metric_name, config in METRICS_CONFIG.items():
            if metric_name not in metrics:
                continue

            is_sum = config["agg"] == "sum"
            daily_buckets: dict[str, dict[str, float]] = defaultdict(dict)
            daily_vals: dict[str, list[float]] = defaultdict(list)

            for point in metrics[metric_name].get("data", []):
                raw_date = point["date"]
                try:
                    ts = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    local_ts = ts.astimezone(local_tz)
                    date = local_ts.strftime("%Y-%m-%d")
                    minute_key = local_ts.strftime("%H:%M")
                except (ValueError, AttributeError):
                    date = raw_date[:10]
                    minute_key = raw_date[11:16] if len(raw_date) > 16 else "00:00"

                all_minutes_by_date[date].add(minute_key)

                qty = point.get("qty")
                if qty is not None and qty != 0:
                    factor = config.get("factor", 1.0)
                    val = qty * factor
                    if is_sum:
                        bucket = daily_buckets[date]
                        bucket[minute_key] = max(bucket.get(minute_key, 0), val)
                    else:
                        daily_vals[date].append(val)

            # Build aggregated dates
            if is_sum:
                agg_dates = {
                    date: (sum(buckets.values()), len(buckets))
                    for date, buckets in daily_buckets.items()
                }
            else:
                agg_dates = {
                    date: (sum(vals) / len(vals), len(vals))
                    for date, vals in daily_vals.items()
                }

            for date, (value, count) in agg_dates.items():
                item = {
                    "source": self.source,
                    "source_id": f"{metric_name}-{date}",
                    "category": self.category,
                    "item_type": metric_name,
                    "title": f"{metric_name.replace('_', ' ').title()} {date}",
                    "content": None,
                    "metadata_": {
                        "value": round(value, 2),
                        "unit": config["unit"],
                        "agg": config["agg"],
                        "data_points": count,
                    },
                    "tags": ["apple_health", metric_name],
                    "is_public": False,
                    "source_url": None,
                    "created_at": datetime.fromisoformat(f"{date}T00:00:00{tz_offset}"),
                }
                full_items.append(item)

        # Detect partial days: a full day spans 00:xx to 23:xx in local tz
        partial_dates = set()
        for date, minutes in all_minutes_by_date.items():
            if not minutes:
                continue
            earliest = min(minutes)
            latest = max(minutes)
            if earliest > "02:00" or latest < "22:00":
                partial_dates.add(date)

        if partial_dates:
            logger.info(f"[apple_health] Partial days (insert-only): {sorted(partial_dates)}")

        # Split items into full-day (upsert) and partial-day (insert-only)
        final_full = []
        final_partial = []
        for item in full_items:
            item_date = item["created_at"].strftime("%Y-%m-%d") if isinstance(item["created_at"], datetime) else str(item["created_at"])[:10]
            if item_date in partial_dates:
                final_partial.append(item)
            else:
                final_full.append(item)

        # Also store workouts
        for workout in payload.get("data", {}).get("workouts", []):
            start = workout.get("start", "")
            wid = hashlib.sha256(f"{start}_{workout.get('name', '')}".encode()).hexdigest()[:16]
            final_full.append({
                "source": self.source,
                "source_id": f"workout-{wid}",
                "category": self.category,
                "item_type": "workout",
                "title": workout.get("name", "Workout"),
                "content": None,
                "metadata_": workout,
                "tags": ["apple_health", "workout"],
                "is_public": False,
                "source_url": None,
                "created_at": datetime.fromisoformat(start.replace("Z", "+00:00")).astimezone(local_tz) if start else datetime.now(local_tz),
            })

        count_full = await self.upsert_items(session, final_full)
        count_partial = await self.insert_if_not_exists(session, final_partial)
        total = count_full + count_partial
        await self.update_sync_state(session, status="idle", items_synced=total)
        return total
