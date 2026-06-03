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

    def _get_json_or_none_on_404(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Fetch JSON but treat 404 as an absent resource.

        Some meeting IDs discovered through meetingsessions do not resolve
        through /meetings/{meeting_id}. That is expected source-system
        behaviour and should not fail the relational harvest.
        """

        try:
            return self._get_json(path, params=params)
        except requests.HTTPError as exc:
            response = exc.response
            if response is not None and response.status_code == 404:
                return None
            raise

    @staticmethod
    def _result(payload: dict[str, Any]) -> dict[str, Any]:
        result = payload.get("result", {})
        if not isinstance(result, dict):
            raise ValueError("Expected response field 'result' to be an object")
        return result

    @staticmethod
    def _result_list(payload: dict[str, Any], field_name: str) -> list[dict[str, Any]]:
        result = GemeenteOplossingenConnector._result(payload)
        records = result.get(field_name, [])
        if not isinstance(records, list):
            raise ValueError(f"Expected response field 'result.{field_name}' to be a list")
        if not all(isinstance(record, dict) for record in records):
            raise ValueError(f"Expected every item in 'result.{field_name}' to be an object")
        return records

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
        return self._result_list(payload, "documents")

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

    def fetch_meeting_session_count(self) -> int:
        payload = self._get_json("meetingsessions", params={"limit": 1, "offset": 0})
        result = self._result(payload)
        total_count = result.get("totalCount", 0)
        return int(total_count)

    def fetch_meeting_sessions_page(self, *, limit: int, offset: int) -> list[dict[str, Any]]:
        """Fetch one page from /meetingsessions."""

        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if offset < 0:
            raise ValueError("offset must be 0 or greater")

        payload = self._get_json("meetingsessions", params={"limit": limit, "offset": offset})
        return self._result_list(payload, "meetingsessions")

    def fetch_latest_meeting_sessions(self, limit: int) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        total_count = self.fetch_meeting_session_count()
        offset = max(0, total_count - limit)
        return self.fetch_meeting_sessions_page(limit=limit, offset=offset)

    def fetch_meeting(self, meeting_id: int | str) -> dict[str, Any] | None:
        """Fetch /meetings/{meeting_id}, returning None for 404 responses."""

        payload = self._get_json_or_none_on_404(f"meetings/{meeting_id}")
        if payload is None:
            return None
        result = self._result(payload)
        meeting = result.get("meeting", result)
        if not isinstance(meeting, dict):
            raise ValueError("Expected response field 'result.meeting' to be an object")
        return meeting

    def fetch_meeting_items(self, meeting_id: int | str) -> list[dict[str, Any]]:
        """Fetch /meetings/{meeting_id}/meetingitems."""

        payload = self._get_json(f"meetings/{meeting_id}/meetingitems")
        return self._result_list(payload, "meetingitems")

    def fetch_meeting_documents(self, meeting_id: int | str) -> list[dict[str, Any]]:
        """Fetch /meetings/{meeting_id}/documents."""

        payload = self._get_json(f"meetings/{meeting_id}/documents")
        return self._result_list(payload, "documents")

    def fetch_meeting_item_documents(self, meeting_item_id: int | str) -> list[dict[str, Any]]:
        """Fetch /meetingitems/{meeting_item_id}/documents."""

        payload = self._get_json(f"meetingitems/{meeting_item_id}/documents")
        return self._result_list(payload, "documents")

    def build_document_download_url(self, document_id: int | str) -> str:
        return f"{self.base_url}documents/{document_id}/download"
