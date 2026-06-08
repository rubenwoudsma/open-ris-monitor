"""Canonical document model for the Open RIS Monitor MVP."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class Document(BaseModel):
    """Canonical metadata representation of a RIS document.

    The model keeps the original source document type for traceability and adds
    a compact normalized type for filtering and analysis.
    """

    id: str
    schema_version: str = "1.0.0"
    municipality_id: str
    source_system_id: str
    source_id: str
    source_object_id: str | None = None
    title: str
    description: str | None = None
    document_type: str | None = None
    normalized_document_type: str | None = None
    normalized_document_type_label: str | None = None
    filename: str | None = None
    file_size_bytes: int | None = None
    publication_datetime: datetime | None = None
    publication_timezone: str | None = None
    is_confidential: bool = False
    is_tabsign_document: bool = False
    source_url: HttpUrl | None = None
    download_url: HttpUrl | None = None
    url: str | None = None  # Contractveld v1.0.0
    retrieved_at: datetime
    raw: dict[str, Any] = Field(default_factory=dict)
