from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


RawRecord = dict[str, Any]


class ConnectorError(RuntimeError):
    """Raised when a source connector cannot retrieve or parse data."""


class BaseConnector(ABC):
    """Base interface for RIS source connectors.

    Connectors are source-specific. They should return raw source records and
    should not convert records to the canonical Open RIS Monitor data model.
    Normalisation belongs in the pipeline layer.
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    @abstractmethod
    def fetch_meetings(self) -> list[RawRecord]:
        """Fetch raw meeting records from the source system."""

    @abstractmethod
    def fetch_agenda_items(self) -> list[RawRecord]:
        """Fetch raw agenda item records from the source system."""

    @abstractmethod
    def fetch_documents(self) -> list[RawRecord]:
        """Fetch raw document metadata records from the source system."""

    def fetch_document_file(self, download_url: str) -> bytes:
        """Fetch a document file.

        Document downloads are deliberately optional. The MVP should first work
        with metadata-only harvesting before enabling PDF enrichment.
        """
        raise NotImplementedError(
            "Document file download is not implemented for this connector yet."
        )
