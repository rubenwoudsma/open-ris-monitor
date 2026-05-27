from __future__ import annotations

from datetime import date

from pydantic import HttpUrl

from open_ris_monitor.models.common import SourceTrackedModel


class Document(SourceTrackedModel):
    municipality_id: str
    source_system_id: str
    meeting_id: str | None = None
    agenda_item_id: str | None = None
    title: str
    document_type: str | None = None
    filename: str | None = None
    mime_type: str | None = None
    source_url: HttpUrl | None = None
    download_url: HttpUrl | None = None
    date_published: date | None = None
    date_meeting: date | None = None
    language: str | None = "nl"
    sha256: str | None = None
    file_size_bytes: int | None = None
    text_status: str = "not_processed"
