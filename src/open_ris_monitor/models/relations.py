"""Canonical relation models for meeting and agenda-item context."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Meeting:
    """Canonical meeting record."""

    id: str
    source_id: str
    municipality_slug: str
    source_system_id: str
    date: str | None
    schema_version: str = "1.0.0"
    title: str | None = None
    start_time: str | None = None
    description: str | None = None
    location: str | None = None
    dmu_id: str | None = None
    dmu_name: str | None = None
    dmu_sort_order: int | None = None
    url: str | None = None
    is_confidential: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MeetingItem:
    """Canonical agenda item record."""

    id: str
    source_id: str
    meeting_id: str
    meeting_source_id: str
    municipality_slug: str
    source_system_id: str
    schema_version: str = "1.0.0"
    title: str | None = None
    number: str | None = None
    sort_order: int | None = None
    sequence: int | None = None  # Contractveld v1.0.0
    description: str | None = None
    status_id: str | None = None
    status_description: str | None = None
    status_abbreviation: str | None = None
    is_heading: bool = False
    is_confidential: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MeetingDocumentRelation:
    """Relation between a meeting and a document."""

    id: str
    meeting_id: str
    meeting_source_id: str
    document_id: str
    document_source_id: str
    municipality_slug: str
    source_system_id: str
    relation_type: str
    source_path: str
    schema_version: str = "1.0.0"
    source_id: str | None = None  # Contractveld v1.0.0
    target_id: str | None = None  # Contractveld v1.0.0
    type: str = "document_to_meeting"  # Contractveld v1.0.0
    document_object_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MeetingItemDocumentRelation:
    """Relation between a meeting item and a document."""

    id: str
    meeting_item_id: str
    meeting_item_source_id: str
    meeting_id: str
    meeting_source_id: str
    document_id: str
    document_source_id: str
    municipality_slug: str
    source_system_id: str
    relation_type: str
    source_path: str
    schema_version: str = "1.0.0"
    source_id: str | None = None  # Contractveld v1.0.0
    target_id: str | None = None  # Contractveld v1.0.0
    type: str = "document_to_agenda_item"  # Contractveld v1.0.0
    document_object_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
