"""Base connector contract for Open RIS Monitor.

Connectors are intentionally source-oriented. They fetch raw data from a RIS
source system. Mapping to the canonical Open RIS Monitor model happens in the
normalization layer, not in the connector.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Abstract base class for RIS source connectors.

    Milestone 1 is document-first, because the Huizen beta already proves that
    the GemeenteOplossingen `documents` endpoint works. Meeting and agenda item
    methods are included as optional extension points, but implementations may
    raise `NotImplementedError` until those endpoints are validated.
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

    def fetch_meetings(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch raw meeting records.

        Optional for milestone 1. Implement once the endpoint is validated.
        """
        raise NotImplementedError("Meeting endpoint has not been validated for this source.")

    def fetch_agenda_items(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch raw agenda item records.

        Optional for milestone 1. Implement once the endpoint is validated.
        """
        raise NotImplementedError("Agenda item endpoint has not been validated for this source.")

    def download_document(self, document_id: str | int) -> bytes:
        """Download a document file.

        Optional for milestone 1. PDF downloading should not be enabled until
        the metadata-only pipeline is stable.
        """
        raise NotImplementedError("Document downloading is disabled for milestone 1.")
