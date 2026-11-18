"""Canonical data models for Open RIS Monitor."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class Document(BaseModel):
    """A canonical document record.

    This model represents a document after normalization, providing a stable
    interface for exporters and analysis scripts.
    """

    # Core canonical fields
    id: str = Field(description="The stable canonical ID for the document.")
    schema_version: str = Field(default="1.0.0", description="The schema version of this record.")
    municipality_slug: str = Field(description="The slug of the municipality this document belongs to.")

    # Source identifiers
    source_id: str = Field(description="The document identifier from the source system.")
    source_object_id: str | None = Field(default=None, description="An additional source identifier, if available.")

    # Core metadata
    title: str | None = Field(default=None, description="The primary title or name of the document.")
    description: str | None = Field(default=None, description="A longer description, often used as a fallback for title.")
    document_type: str | None = Field(default=None, description="The raw document type label from the source.")
    publication_datetime: datetime | None = Field(default=None, description="The date and time the document was published.")
    is_confidential: bool = Field(default=False, description="Whether the document is marked as confidential.")

    # File metadata
    filename: str | None = Field(default=None, description="The original filename of the document.")
    file_size_bytes: int | None = Field(default=None, description="The size of the document file in bytes.")
    download_url: str | None = Field(default=None, description="A direct URL to download the document file.")
    source_url: str | None = Field(default=None, description="A URL to the document's page in the source RIS.")

    # Normalization and enrichment
    normalized_document_type: str | None = Field(default=None, description="A cleaned, standardized document type.")
    normalized_document_type_label: str | None = Field(default=None, description="A human-readable label for the normalized type.")
    text: str | None = Field(default=None, description="Extracted text content, for future use.")

    # Operational metadata
    retrieved_at: datetime = Field(description="The timestamp when the source record was retrieved.")
    raw: dict[str, Any] = Field(description="The original, unmodified source record as a dictionary.")


class Meeting(BaseModel):
    """A canonical meeting record."""

    # Core canonical fields
    id: str = Field(description="The stable canonical ID for the meeting.")
    schema_version: str = Field(default="1.0.0", description="The schema version of this record.")
    municipality_slug: str = Field(description="The slug of the municipality this meeting belongs to.")
    source_system_id: str = Field(description="Identifier for the source system, e.g., 'gemeenteoplossingen'.")

    # Source identifiers
    source_id: str = Field(description="The meeting identifier from the source system.")

    # Core metadata
    title: str | None = Field(default=None, description="The primary title or description of the meeting.")
    date: date | None = Field(default=None, description="The date of the meeting.")
    start_time: str | None = Field(default=None, description="The start time of the meeting, as text.")
    location: str | None = Field(default=None, description="The location of the meeting.")
    url: str | None = Field(default=None, description="A URL to the meeting's page in the source RIS.")
    is_confidential: bool = Field(default=False, description="Whether the meeting is marked as confidential.")

    # Related body/committee (DMU) metadata
    dmu_id: str | None = Field(default=None, description="Source identifier for the related decision-making unit (committee).")
    dmu_name: str | None = Field(default=None, description="Name of the related decision-making unit.")
    dmu_sort_order: int | None = Field(default=None, description="Sort order for the related decision-making unit.")

    # Operational metadata
    retrieved_at: datetime = Field(description="The timestamp when the source record was retrieved.")
    raw: dict[str, Any] = Field(description="The original, unmodified source record as a dictionary.")


class MeetingItem(BaseModel):
    """A canonical meeting item (agenda item) record."""

    # Core canonical fields
    id: str = Field(description="The stable canonical ID for the meeting item.")
    schema_version: str = Field(default="1.0.0", description="The schema version of this record.")
    municipality_slug: str = Field(description="The slug of the municipality this item belongs to.")
    source_system_id: str = Field(description="Identifier for the source system, e.g., 'gemeenteoplossingen'.")

    # Source identifiers
    source_id: str = Field(description="The meeting item identifier from the source system.")
    meeting_id: str = Field(description="The canonical ID of the parent meeting.")
    meeting_source_id: str = Field(description="The source ID of the parent meeting.")

    # Core metadata
    number: str | None = Field(default=None, description="The agenda item number, as text.")
    sort_order: int | None = Field(default=None, description="The sort order of the item within the meeting.")
    title: str | None = Field(default=None, description="The primary title or description of the item.")
    is_heading: bool = Field(default=False, description="Whether this item is a non-actionable heading.")
    is_confidential: bool = Field(default=False, description="Whether the item is marked as confidential.")

    # Operational metadata
    retrieved_at: datetime = Field(description="The timestamp when the source record was retrieved.")
    raw: dict[str, Any] = Field(description="The original, unmodified source record as a dictionary.")