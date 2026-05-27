"""GemeenteOplossingen connector.

This connector is based on the proven API usage from the existing Huizen RIS Monitor beta:

- GET {base_url}documents?limit=1
- response path: result.totalCount
- GET {base_url}documents?limit={limit}&offset={offset}
- response path: result.documents
- download URL pattern: {base_url}documents/{id}/download
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import requests

from open_ris_monitor.connectors.base import BaseConnector


class GemeenteOplossingenConnector(BaseConnector):
    """Connector for the GemeenteOplossingen RIS API v2."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        user_agent: str = "open-ris-monitor/0.1",
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": user_agent,
            }
        )

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = urljoin(self.base_url, path.lstrip("/"))
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object from {url}, got {type(payload).__name__}")
        return payload

    @staticmethod
    def _result(payload: dict[str, Any]) -> dict[str, Any]:
        result = payload.get("result")
        if not isinstance(result, dict):
            raise KeyError("Expected response field 'result' to be an object.")
        return result

    def fetch_document_count(self) -> int:
        """Return ``result.totalCount`` from the documents endpoint."""
        payload = self._get_json("documents", params={"limit": 1})
        result = self._result(payload)
        total_count = result.get("totalCount")
        if total_count is None:
            raise KeyError("Expected response field 'result.totalCount'.")
        return int(total_count)

    def fetch_documents(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch raw documents from ``result.documents``."""
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if offset < 0:
            raise ValueError("offset must be 0 or greater")

        payload = self._get_json("documents", params={"limit": limit, "offset": offset})
        result = self._result(payload)
        documents = result.get("documents")
        if not isinstance(documents, list):
            raise KeyError("Expected response field 'result.documents' to be a list.")
        return documents

    def build_document_download_url(self, document_id: str | int) -> str:
        """Build the public download URL for a document."""
        return urljoin(self.base_url, f"documents/{document_id}/download")

    def download_document(self, document_id: str | int) -> bytes:
        """Download a document file.

        Keep disabled in the default MVP pipeline unless explicitly configured.
        """
        url = self.build_document_download_url(document_id)
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.content
