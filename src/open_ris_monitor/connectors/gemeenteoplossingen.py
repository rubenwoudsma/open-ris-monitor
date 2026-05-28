from __future__ import annotations

import time
from typing import Any

import requests


class GemeenteOplossingenConnector:
    """Connector for the GemeenteOplossingen RIS API.

    The constructor intentionally accepts both positional and keyword usage:

        GemeenteOplossingenConnector("https://example/api/v2/")
        GemeenteOplossingenConnector(base_url="https://example/api/v2/")

    It also accepts request_delay_seconds, which is used by the paginated
    full-harvest flow to avoid hammering the RIS API with back-to-back requests.
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: int = 30,
        request_delay_seconds: float = 0.0,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds
        self.request_delay_seconds = max(0.0, float(request_delay_seconds))
        self.session = session or requests.Session()

    def _sleep_if_needed(self) -> None:
        if self.request_delay_seconds > 0:
            time.sleep(self.request_delay_seconds)

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._sleep_if_needed()
        url = self.base_url + path.lstrip("/")
        response = self.session.get(url, params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object from {url}, got {type(data).__name__}")
        return data

    @staticmethod
    def _result(payload: dict[str, Any]) -> dict[str, Any]:
        result = payload.get("result", {})
        if not isinstance(result, dict):
            raise ValueError("Expected response field 'result' to be an object")
        return result

    def fetch_document_count(self) -> int:
        payload = self._get_json("documents", params={"limit": 1, "offset": 0})
        result = self._result(payload)
        total_count = result.get("totalCount", 0)
        return int(total_count)

    def fetch_documents_page(self, *, limit: int, offset: int) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if offset < 0:
            raise ValueError("offset must be 0 or greater")

        payload = self._get_json("documents", params={"limit": limit, "offset": offset})
        result = self._result(payload)
        documents = result.get("documents", [])
        if not isinstance(documents, list):
            raise ValueError("Expected response field 'result.documents' to be a list")
        return documents

    def fetch_latest_documents(self, limit: int) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

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
            raise ValueError("batch_size must be greater than 0")
        if max_documents is not None and max_documents <= 0:
            raise ValueError("max_documents must be greater than 0 when provided")

        total_count = self.fetch_document_count()
        target_count = min(total_count, max_documents) if max_documents is not None else total_count

        documents: list[dict[str, Any]] = []
        offset = 0

        while offset < target_count:
            limit = min(batch_size, target_count - offset)
            page = self.fetch_documents_page(limit=limit, offset=offset)
            if not page:
                break

            documents.extend(page)
            offset += len(page)

            if len(page) < limit:
                break

        return documents

    def build_document_download_url(self, document_id: int | str) -> str:
        return f"{self.base_url}documents/{document_id}/download"
