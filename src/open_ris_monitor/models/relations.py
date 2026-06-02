"""Canonical relation models for meeting and agenda-item context."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Meeting:
    """Canonical meeting record.

    A meeting is a source-system meeting, normalized into stable identifiers and
    reusable public fields. The model intentionally keeps the source meeting ID
    next to the project-level ID.
    """

    id: str
    source_id: str
    municipality_slug: str
    source_system_id: str
    date: str | None
    start_time: str | None
    description: str | None
    location: str | None
    dmu_id: str | None
    dmu_name: str | None
    dmu_sort_order: int | None
    url: str | None
    is_confidential: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MeetingItem:
    """Canonical agenda item record.

    GemeenteOplossingen names these records `meetingitems`. In the public data
    model they represent agenda items within a meeting.
    """

    id: str
    source_id: str
    meeting_id: str
    meeting_source_id: str
    municipality_slug: str
    source_system_id: str
    number: str | None
    sort_order: int | None
    title: str | None
    description: str | None
    status_id: str | None
    status_description: str | None
    status_abbreviation: str | None
    is_heading: bool
    is_confidential: bool

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
    document_object_id: str | None
    municipality_slug: str
    source_system_id: str
    relation_type: str
    source_path: str

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
    document_object_id: str | None
    municipality_slug: str
    source_system_id: str
    relation_type: str
    source_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
