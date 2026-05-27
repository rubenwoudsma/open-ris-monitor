from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Base interface for RIS source connectors."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    @abstractmethod
    def fetch_meetings(self) -> list[dict[str, Any]]:
        """Fetch raw meeting records from the source system."""

    @abstractmethod
    def fetch_agenda_items(self) -> list[dict[str, Any]]:
        """Fetch raw agenda item records from the source system."""

    @abstractmethod
    def fetch_documents(self) -> list[dict[str, Any]]:
        """Fetch raw document metadata records from the source system."""

    def fetch_document_file(self, download_url: str) -> bytes:
        """Fetch a document file. Implement when document enrichment is needed."""
        raise NotImplementedError("Document file download is not implemented for this connector yet.")
