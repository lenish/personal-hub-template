"""Base collector class for all data sources."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import DataItem, SyncState

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    Base class for all data collectors.

    Each collector should:
    1. Inherit from BaseCollector
    2. Set source and category class attributes
    3. Implement the collect() method
    4. Use upsert_items() or insert_if_not_exists() to save data
    5. Use update_sync_state() to track sync status

    Example:
        class MyCollector(BaseCollector):
            source = "my-service"
            category = "productivity"

            async def collect(self, session: AsyncSession) -> int:
                # Fetch data from external API
                items = await self.fetch_from_api()

                # Transform to DataItem format
                data_items = [
                    {
                        "source": self.source,
                        "source_id": item["id"],
                        "category": self.category,
                        "item_type": "task",
                        "title": item["title"],
                        "content": item["description"],
                        "metadata_": {"priority": item["priority"]},
                        "created_at": item["created_at"],
                    }
                    for item in items
                ]

                # Save to database
                count = await self.upsert_items(session, data_items)
                return count
    """

    source: str  # e.g., 'whoop', 'slack', 'notion'
    category: str  # e.g., 'health', 'communication', 'productivity'

    @abstractmethod
    async def collect(self, session: AsyncSession) -> int:
        """
        Fetch data from external source and save to database.

        Args:
            session: Database session

        Returns:
            Number of items synced
        """
        ...

    async def upsert_items(self, session: AsyncSession, items: list[dict]) -> int:
        """
        Upsert a batch of DataItems into the database.

        Performs INSERT ... ON CONFLICT UPDATE, deduplicating by (source, source_id).

        Args:
            session: Database session
            items: List of dicts matching DataItem columns

        Returns:
            Number of items processed
        """
        if not items:
            return 0

        # Get metadata column reference (avoid SQLAlchemy MetaData collision)
        metadata_col = DataItem.__table__.c.metadata

        # Deduplicate by (source, source_id)
        seen = {}
        for item in items:
            key = (item["source"], item["source_id"])
            seen[key] = item

        # Prepare database rows
        db_items = []
        for item in seen.values():
            row = dict(item)
            # Handle metadata_ -> metadata column name mapping
            if "metadata_" in row:
                row[metadata_col] = row.pop("metadata_")
            elif "metadata" in row:
                row[metadata_col] = row.pop("metadata")
            db_items.append(row)

        # Batch to stay under PostgreSQL parameter limit
        batch_size = 2000
        for i in range(0, len(db_items), batch_size):
            batch = db_items[i : i + batch_size]
            stmt = pg_insert(DataItem.__table__).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=["source", "source_id"],
                set_={
                    "title": stmt.excluded.title,
                    "content": stmt.excluded.content,
                    metadata_col: stmt.excluded.metadata,
                    "tags": stmt.excluded.tags,
                    "is_public": stmt.excluded.is_public,
                    "source_url": stmt.excluded.source_url,
                    "created_at": stmt.excluded.created_at,
                    "synced_at": text("now()"),
                },
            )
            await session.execute(stmt)

        await session.commit()
        return len(items)

    async def insert_if_not_exists(self, session: AsyncSession, items: list[dict]) -> int:
        """
        Insert items only if they don't already exist (ON CONFLICT DO NOTHING).

        Useful for immutable data that should never be updated.

        Args:
            session: Database session
            items: List of dicts matching DataItem columns

        Returns:
            Number of items processed
        """
        if not items:
            return 0

        metadata_col = DataItem.__table__.c.metadata

        seen = {}
        for item in items:
            key = (item["source"], item["source_id"])
            seen[key] = item

        db_items = []
        for item in seen.values():
            row = dict(item)
            if "metadata_" in row:
                row[metadata_col] = row.pop("metadata_")
            elif "metadata" in row:
                row[metadata_col] = row.pop("metadata")
            db_items.append(row)

        batch_size = 2000
        for i in range(0, len(db_items), batch_size):
            batch = db_items[i : i + batch_size]
            stmt = pg_insert(DataItem.__table__).values(batch)
            stmt = stmt.on_conflict_do_nothing(index_elements=["source", "source_id"])
            await session.execute(stmt)

        await session.commit()
        return len(items)

    async def update_sync_state(
        self,
        session: AsyncSession,
        *,
        status: str = "idle",
        error: str | None = None,
        items_synced: int = 0,
        cursor: dict | None = None,
    ):
        """
        Update synchronization state for this collector.

        Args:
            session: Database session
            status: Sync status ('idle', 'running', 'error')
            error: Error message if status is 'error'
            items_synced: Number of items synced in this run
            cursor: Pagination cursor or other state data
        """
        now = datetime.now(timezone.utc)
        stmt = pg_insert(SyncState).values(
            source=self.source,
            last_sync_at=now,
            status=status,
            error_message=error,
            items_synced=items_synced,
            cursor=cursor or {},
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["source"],
            set_={
                "last_sync_at": now,
                "status": status,
                "error_message": error,
                "items_synced": items_synced,
                **({"cursor": cursor} if cursor is not None else {}),
            },
        )
        await session.execute(stmt)
        await session.commit()

    async def run(self, session: AsyncSession):
        """
        Execute the collector with automatic sync state tracking.

        This is the main entry point for running a collector.
        It handles errors and updates sync state automatically.
        """
        logger.info(f"[{self.source}] Starting collection...")
        await self.update_sync_state(session, status="running")
        try:
            count = await self.collect(session)
            await self.update_sync_state(session, status="idle", items_synced=count)
            logger.info(f"[{self.source}] ✓ Collected {count} items")
        except Exception as e:
            logger.exception(f"[{self.source}] ✗ Collection failed: {e}")
            await self.update_sync_state(session, status="error", error=str(e)[:500])

    async def get_cursor(self, session: AsyncSession) -> dict:
        """
        Retrieve the stored cursor/state for this collector.

        Returns:
            Cursor dictionary (empty dict if none stored)
        """
        result = await session.execute(
            select(SyncState.cursor).where(SyncState.source == self.source)
        )
        row = result.scalar_one_or_none()
        return row or {}
