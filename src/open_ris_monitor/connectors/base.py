from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Base contract for RIS source connectors.

    Connectors return raw source records. Mapping to canonical Open RIS Monitor
    models belongs in the normalizer layer.
    """

    @abstractmethod
    def fetch_document_count(self) -> int:
        """Return the total number of documents available at the source."""

    @abstractmethod
    def fetch_documents_page(self, *, limit: int, offset: int) -> list[dict[str, Any]]:
        """Return one page of raw document records from the source."""

    @abstractmethod
    def fetch_latest_documents(self, *, limit: int) -> list[dict[str, Any]]:
        """Return the latest raw document records from the source."""

    @abstractmethod
    def fetch_all_documents(
        self,
        *,
        batch_size: int = 100,
        max_documents: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return raw document records using pagination."""

    @abstractmethod
    def build_document_download_url(self, document_id: str | int) -> str:
        """Build a direct download URL for a source document."""
