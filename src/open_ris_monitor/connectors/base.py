"""Base connector contract for source systems."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Minimal connector contract for milestone 1.

    Milestone 1 is document-first and metadata-only. Meetings and agenda items
    will be added after the document endpoint is harvested reliably.
    """

    @abstractmethod
    def fetch_document_count(self) -> int:
        """Return the total number of documents available in the source system."""

    @abstractmethod
    def fetch_documents(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch raw document records from the source system."""

    @abstractmethod
    def fetch_latest_documents(self, limit: int = 500) -> list[dict[str, Any]]:
        """Fetch the latest document records from the source system."""

    @abstractmethod
    def build_document_download_url(self, document_id: str | int) -> str:
        """Build a document download URL without downloading the document."""
