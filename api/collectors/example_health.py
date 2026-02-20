"""
Example health data collector using webhook pattern.

This is a simple example showing how to receive health data from
an external source (e.g., iOS Health Auto Export app) via webhook.
"""

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from api.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class HealthWebhookCollector(BaseCollector):
    """Example collector that receives health data via webhook."""

    source = "health-webhook"
    category = "health"

    async def collect(self, session: AsyncSession) -> int:
        """
        This collector doesn't actively fetch data.
        Data is pushed to it via webhook endpoint.

        See api/routers/health.py for webhook endpoint implementation.
        """
        logger.info("[health-webhook] This collector receives data via webhook")
        return 0

    @staticmethod
    async def process_webhook_data(
        session: AsyncSession,
        metrics: list[dict],
    ) -> int:
        """
        Process health metrics received from webhook.

        Args:
            session: Database session
            metrics: List of health metric dicts from webhook

        Returns:
            Number of metrics processed

        Example webhook payload:
            {
                "metrics": [
                    {
                        "type": "StepCount",
                        "value": 8542,
                        "unit": "count",
                        "date": "2026-02-21",
                        "source": "iPhone"
                    },
                    {
                        "type": "HeartRate",
                        "value": 68,
                        "unit": "bpm",
                        "date": "2026-02-21T10:30:00Z",
                        "source": "Apple Watch"
                    }
                ]
            }
        """
        items = []

        for metric in metrics:
            # Parse timestamp
            date_str = metric.get("date", "")
            try:
                if "T" in date_str:
                    created_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    created_at = datetime.fromisoformat(f"{date_str}T00:00:00+00:00")
            except (ValueError, TypeError):
                logger.warning(f"[health-webhook] Invalid date: {date_str}")
                continue

            metric_type = metric.get("type", "Unknown")
            value = metric.get("value")
            unit = metric.get("unit", "")

            # Create unique ID combining type and date
            source_id = f"{metric_type.lower()}-{created_at.strftime('%Y%m%d-%H%M')}"

            items.append(
                {
                    "source": "health-webhook",
                    "source_id": source_id,
                    "category": "health",
                    "item_type": metric_type.lower(),
                    "title": f"{metric_type}: {value} {unit}",
                    "content": None,
                    "metadata_": {
                        "value": value,
                        "unit": unit,
                        "type": metric_type,
                        "device": metric.get("source", "Unknown"),
                        "raw": metric,
                    },
                    "tags": ["health", "webhook", metric_type.lower()],
                    "is_public": False,
                    "source_url": None,
                    "created_at": created_at,
                }
            )

        # Use base collector's upsert method
        collector = HealthWebhookCollector()
        count = await collector.upsert_items(session, items)
        logger.info(f"[health-webhook] Processed {count} metrics")
        return count
