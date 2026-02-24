"""System resource monitoring and database overview."""

import math
import os
import shutil
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from api.database import engine

router = APIRouter(prefix="/api/system", tags=["system"])


def _human_size(size_bytes: int) -> str:
    """Convert bytes to a human-readable string."""
    if size_bytes == 0:
        return "0 B"
    units = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    i = min(i, len(units) - 1)
    value = size_bytes / (1024 ** i)
    return f"{value:.1f} {units[i]}"


@router.get("/resources")
async def get_resources():
    """Get system resource usage (CPU, memory, disk)."""
    disk = shutil.disk_usage("/")
    disk_total_gb = round(disk.total / (1024**3), 1)
    disk_used_gb = round(disk.used / (1024**3), 1)
    disk_pct = round(disk.used / disk.total * 100, 1) if disk.total else 0.0

    return {
        "cpu": {
            "cores": os.cpu_count() or 1,
            "load_avg": list(os.getloadavg()),
        },
        "disk": {
            "total_gb": disk_total_gb,
            "used_gb": disk_used_gb,
            "usage_pct": disk_pct,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/db/overview")
async def db_overview():
    """Get database size, table count, and connection pool stats."""
    async with engine.connect() as conn:
        row = (await conn.execute(text(
            "SELECT pg_database_size(current_database()) AS db_size"
        ))).one()
        db_size_bytes = row.db_size

        stats = (await conn.execute(text(
            "SELECT count(*) AS table_count, coalesce(sum(n_live_tup), 0) AS total_rows "
            "FROM pg_stat_user_tables"
        ))).one()

    pool = engine.pool
    checked_in = pool.checkedin()
    checked_out = pool.checkedout()
    overflow = pool.overflow()
    size = pool.size()

    return {
        "db_size_bytes": db_size_bytes,
        "db_size_human": _human_size(db_size_bytes),
        "table_count": stats.table_count,
        "total_rows": stats.total_rows,
        "pool": {
            "size": size,
            "checked_in": checked_in,
            "checked_out": checked_out,
            "overflow": overflow,
        },
    }
