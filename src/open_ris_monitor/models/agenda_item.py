from __future__ import annotations

from pydantic import HttpUrl

from open_ris_monitor.models.common import SourceTrackedModel


class AgendaItem(SourceTrackedModel):
    meeting_id: str
    municipality_id: str
    number: str | None = None
    title: str
    description: str | None = None
    position: int | None = None
    status: str | None = None
    web_url: HttpUrl | None = None
