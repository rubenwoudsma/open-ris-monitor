from __future__ import annotations

from datetime import datetime

from open_ris_monitor.models.common import CanonicalModel


class DocumentVersion(CanonicalModel):
    id: str
    document_id: str
    retrieved_at: datetime
    sha256: str | None = None
    file_size_bytes: int | None = None
    content_changed: bool | None = None
    metadata_changed: bool | None = None
    previous_version_id: str | None = None
