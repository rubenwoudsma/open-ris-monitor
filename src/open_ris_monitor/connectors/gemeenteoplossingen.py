from __future__ import annotations

import time
from typing import Any
from urllib.parse import urljoin

import requests

from open_ris_monitor.connectors.base import BaseConnector


class GemeenteOplossingenConnector(BaseConnector):
    """Connector for GemeenteOplossingen RIS API v2.

    The Huizen implementation has a proven documents endpoint:
    /api/v2/documents?limit={limit}&offset={offset}
    """

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: int = 30,
        request_delay_seconds: float = 0.0,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds
        self.request_delay_seconds = request_delay_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "open-ris-monitor/0.1 (+https://github.com/rubenwoudsma/open-ris-monitor)",
            }
        )

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = urljoin(self.base_url, path.lstrip("/"))
        response = self.session.get(url, params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _extract_result(payload: dict[str, Any]) -> dict[str, Any]:
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ValueError("Expected API response to contain object at key 'result'.")
        return result

    @staticmethod
    def _extract_documents(payload: dict[str, Any]) -> list[dict[str, Any]]:
        result = GemeenteOplossingenConnector._extract_result(payload)
        documents = result.get("documents")
        if not isinstance(documents, list):
            raise ValueError("Expected API response to contain list at key 'result.documents'.")
        return [document for document in documents if isinstance(document, dict)]

    def fetch_document_count(self) -> int:
        payload = self._get_json("documents", params={"limit": 1, "offset": 0})
        result = self._extract_result(payload)
        total_count = result.get("totalCount")
        if total_count is None:
            raise ValueError("Expected API response to contain 'result.totalCount'.")
        return int(total_count)

    def fetch_documents_page(self, *, limit: int, offset: int) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be greater than zero")
        if offset < 0:
            raise ValueError("offset must be zero or greater")

        payload = self._get_json("documents", params={"limit": limit, "offset": offset})
        return self._extract_documents(payload)

    def fetch_latest_documents(self, *, limit: int) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        total_count = self.fetch_document_count()
        offset = max(0, total_count - limit)
        return self.fetch_documents_page(limit=limit, offset=offset)

    def fetch_all_documents(
        self,
        *,
        batch_size: int = 100,
        max_documents: int | None = None,
    ) -> list[dict[str, Any]]:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")
        if max_documents is not None and max_documents < 0:
            raise ValueError("max_documents must be zero or greater")

        total_count = self.fetch_document_count()
        target_count = total_count
        if max_documents and max_documents > 0:
            target_count = min(total_count, max_documents)

        documents: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        offset = 0
        while offset < target_count:
            page_limit = min(batch_size, target_count - offset)
            page = self.fetch_documents_page(limit=page_limit, offset=offset)
            if not page:
                break

            for document in page:
                source_id = str(document.get("id", ""))
                if source_id and source_id in seen_ids:
                    continue
                if source_id:
                    seen_ids.add(source_id)
                documents.append(document)

            offset += len(page)
            if len(page) < page_limit:
                break
            if self.request_delay_seconds > 0:
                time.sleep(self.request_delay_seconds)

        return documents

    def build_document_download_url(self, document_id: str | int) -> str:
        return urljoin(self.base_url, f"documents/{document_id}/download")
