"""Harvest run model."""

from __future__ import annotations

from datetime import datetime

from open_ris_monitor.models.common import CanonicalModel


class HarvestRun(CanonicalModel):
    id: str
    municipality_id: str
    source_system_id: str
    started_at: datetime
    finished_at: datetime | None = None
    status: str
    meetings_seen: int = 0
    agenda_items_seen: int = 0
    documents_seen: int = 0
    documents_downloaded_temporarily: int = 0
    documents_committed: int = 0
    quality_issues_detected: int = 0
