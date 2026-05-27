"""Meeting model."""

from __future__ import annotations

from datetime import datetime

from pydantic import HttpUrl

from open_ris_monitor.models.common import SourceTrackedModel


class Meeting(SourceTrackedModel):
    municipality_id: str
    source_system_id: str
    title: str
    body_type: str | None = None
    status: str | None = None
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    location: str | None = None
    web_url: HttpUrl | None = None
