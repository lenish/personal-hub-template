"""Sync orchestrator — runs collectors on schedule via APScheduler."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from api.config import settings
from api.database import async_session

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_collector(collector_class):
    """Run a collector within a database session."""
    collector = collector_class()
    async with async_session() as session:
        await collector.run(session)


def setup_scheduler():
    """Register collector jobs based on feature flags and sync intervals."""
    if settings.enable_whoop and settings.whoop_client_id:
        from api.collectors.whoop import WhoopCollector

        async def run_whoop():
            await _run_collector(WhoopCollector)

        scheduler.add_job(
            run_whoop, "interval",
            minutes=settings.whoop_sync_interval,
            id="whoop", replace_existing=True,
        )
        logger.info(f"Scheduled whoop collector every {settings.whoop_sync_interval}m")

    if settings.enable_withings and settings.withings_client_id:
        from api.collectors.withings import WithingsCollector

        async def run_withings():
            await _run_collector(WithingsCollector)

        scheduler.add_job(
            run_withings, "interval",
            minutes=settings.withings_sync_interval,
            id="withings", replace_existing=True,
        )
        logger.info(f"Scheduled withings collector every {settings.withings_sync_interval}m")

    if settings.enable_spotify and settings.spotify_client_id:
        from api.collectors.spotify import SpotifyCollector

        async def run_spotify():
            await _run_collector(SpotifyCollector)

        scheduler.add_job(
            run_spotify, "interval",
            minutes=settings.spotify_sync_interval,
            id="spotify", replace_existing=True,
        )
        logger.info(f"Scheduled spotify collector every {settings.spotify_sync_interval}m")

    if settings.enable_google_calendar and settings.google_client_id:
        from api.collectors.google_calendar import GoogleCalendarCollector

        async def run_calendar():
            await _run_collector(GoogleCalendarCollector)

        scheduler.add_job(
            run_calendar, "interval",
            minutes=settings.google_sync_interval,
            id="google_calendar", replace_existing=True,
        )
        logger.info(f"Scheduled google_calendar collector every {settings.google_sync_interval}m")

    if settings.enable_tldv and settings.tldv_api_key:
        from api.collectors.tldv import TldvCollector

        async def run_tldv():
            await _run_collector(TldvCollector)

        scheduler.add_job(
            run_tldv, "interval",
            minutes=settings.tldv_sync_interval,
            id="tldv", replace_existing=True,
        )
        logger.info(f"Scheduled tldv collector every {settings.tldv_sync_interval}m")


def start_scheduler():
    setup_scheduler()
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
