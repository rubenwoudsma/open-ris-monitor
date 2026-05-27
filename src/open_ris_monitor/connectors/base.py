"""Base connector contract for Open RIS Monitor."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Abstract base class for RIS source connectors.

    Milestone 1 is document-first, because the existing Huizen RIS Monitor beta already
    proves that the GemeenteOplossingen ``documents`` endpoint works.
    """

    @abstractmethod
    def fetch_document_count(self) -> int:
        """Return the total number of documents available from the source."""

    @abstractmethod
    def fetch_documents(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch raw document records from the source."""

    @abstractmethod
    def build_document_download_url(self, document_id: str | int) -> str:
        """Build a public document download URL for a source document ID."""

    def fetch_latest_documents(self, limit: int = 500) -> list[dict[str, Any]]:
        """Fetch the latest documents using the source total count and an offset."""
        total_count = self.fetch_document_count()
        offset = max(0, total_count - limit)
        return self.fetch_documents(limit=limit, offset=offset)

    def fetch_meetings(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch raw meeting records. Optional for milestone 1."""
        raise NotImplementedError("Meeting endpoint has not been validated for this source.")

    def fetch_agenda_items(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch raw agenda item records. Optional for milestone 1."""
        raise NotImplementedError("Agenda item endpoint has not been validated for this source.")

    def download_document(self, document_id: str | int) -> bytes:
        """Download a document file. Optional for milestone 1."""
        raise NotImplementedError("Document downloading is disabled for milestone 1.")
