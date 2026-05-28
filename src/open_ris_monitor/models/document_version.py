"""Document version model for checksum-based document enrichment."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, HttpUrl


class DocumentVersion(BaseModel):
    """A checksum-based observation of a document file at harvest time.

    PDF files are downloaded temporarily during enrichment, but are not stored in Git.
    This model stores the evidence needed to detect whether the source file changed.
    """

    id: str
    document_id: str
    municipality_id: str
    source_system_id: str
    source_id: str
    source_object_id: str | None = None
    retrieved_at: datetime
    download_url: HttpUrl | None = None
    sha256: str
    downloaded_file_size_bytes: int
    source_file_size_bytes: int | None = None
    content_changed: bool | None = None
    previous_version_id: str | None = None
    raw: dict[str, Any] | None = None
