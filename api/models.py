"""SQLAlchemy database models."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class DataItem(Base):
    """
    Universal data item for storing any kind of personal data.

    This flexible schema allows you to store:
    - Health metrics (Whoop recovery, Apple Health steps, etc.)
    - Messages (Slack, Telegram, etc.)
    - Calendar events
    - Anything with metadata
    """
    __tablename__ = "data_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    # Data source identification
    source: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "whoop", "slack", "apple-health"
    source_id: Mapped[str] = mapped_column(String, nullable=False)  # Original ID from source

    # Classification
    category: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "health", "communication", "productivity"
    item_type: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "recovery", "message", "event"

    # Content
    title: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        server_default=text("'{}'::jsonb")
    )

    # Organization
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        server_default=text("'{}'::text[]")
    )
    is_public: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))

    # References
    source_url: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()")
    )

    __table_args__ = (
        Index("uq_source_source_id", "source", "source_id", unique=True),
        Index("idx_items_category", "category"),
        Index("idx_items_source", "source"),
        Index("idx_items_created", created_at.desc()),
        Index("idx_items_metadata", "metadata", postgresql_using="gin"),
        Index("idx_items_tags", "tags", postgresql_using="gin"),
    )


class SyncState(Base):
    """Track synchronization state for each data source."""
    __tablename__ = "sync_state"

    source: Mapped[str] = mapped_column(String, primary_key=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cursor: Mapped[dict] = mapped_column(
        JSONB,
        server_default=text("'{}'::jsonb")
    )  # Store pagination cursors, last IDs, etc.
    status: Mapped[str] = mapped_column(String, server_default=text("'idle'"))  # idle, syncing, error
    error_message: Mapped[str | None] = mapped_column(Text)
    items_synced: Mapped[int] = mapped_column(Integer, server_default=text("0"))


# Add more models as needed:
# - User (for multi-user support)
# - HealthMetric (if you want separate table for health data)
# - Message (if you want separate table for communications)
# - etc.
