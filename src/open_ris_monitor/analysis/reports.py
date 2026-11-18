"""Pydantic models for analysis and quality reports."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class MeetingWithoutDocumentsFinding(BaseModel):
    """Represents a meeting that has no direct or indirect document relations."""

    meeting_id: str
    meeting_source_id: str
    title: str | None
    date: date | None
    dmu_name: str | None
    url: str | None


class MeetingsWithoutDocumentsReport(BaseModel):
    """A report of meetings that have no document relations."""

    generated_at: datetime = Field(description="The timestamp when the report was generated.")
    meetings_total: int = Field(description="The total number of meetings analyzed.")
    meetings_without_documents_count: int = Field(
        description="The number of meetings found without any document relations."
    )
    findings: list[MeetingWithoutDocumentsFinding] = Field(description="The list of meetings without documents.")


class UnlinkedDocumentFinding(BaseModel):
    """Represents a document that is not linked to any meeting context."""

    document_id: str | None
    source_id: str | None
    title: str | None
    document_type: str | None
    publication_date: str | None
    meeting_date: str | None
    date_bucket: str
    suspected_reason: str


class UnlinkedDocumentsReport(BaseModel):
    """A report of documents that are not linked to any meeting context."""

    generated_at: datetime = Field(description="The timestamp when the report was generated.")
    documents_total: int = Field(description="The total number of documents analyzed.")
    unlinked_documents_count: int = Field(
        description="The number of documents found without any meeting relations."
    )
    summary: dict[str, dict[str, int]] = Field(description="A summary of findings by various categories.")
    findings: list[UnlinkedDocumentFinding] = Field(description="The list of unlinked documents.")