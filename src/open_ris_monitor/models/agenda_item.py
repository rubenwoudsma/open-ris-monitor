"""Agenda item model."""

from __future__ import annotations

from pydantic import HttpUrl

from open_ris_monitor.models.common import SourceTrackedModel


class AgendaItem(SourceTrackedModel):
    municipality_id: str
    source_system_id: str
    meeting_id: str | None = None
    number: str | None = None
    title: str
    description: str | None = None
    position: int | None = None
    status: str | None = None
    web_url: HttpUrl | None = None
