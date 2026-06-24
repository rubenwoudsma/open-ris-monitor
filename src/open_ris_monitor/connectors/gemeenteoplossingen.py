from __future__ import annotations

import logging
import time
from collections.abc import Callable
from email.utils import parsedate_to_datetime
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)

DEFAULT_RETRY_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


class GemeenteOplossingenConnector:
    """Connector for the GemeenteOplossingen RIS API.

    The connector keeps the public pipeline lightweight, but is defensive about
    transient upstream failures. Temporary network problems and common overload
    statuses are retried with exponential back-off. Permanent client errors such
    as 400, 401, 403 and 404 are not retried.
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: int = 30,
        request_delay_seconds: float = 0.0,
        retry_attempts: int = 3,
        retry_backoff_seconds: float = 1.0,
        retry_status_codes: set[int] | frozenset[int] | None = None,
        session: requests.Session | None = None,
        sleep_func: Callable[[float], None] = time.sleep,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds
        self.request_delay_seconds = max(0.0, float(request_delay_seconds))
        self.retry_attempts = max(0, int(retry_attempts))
        self.retry_backoff_seconds = max(0.0, float(retry_backoff_seconds))
        self.retry_status_codes = frozenset(retry_status_codes or DEFAULT_RETRY_STATUS_CODES)
        self.session = session or requests.Session()
        self._sleep = sleep_func

    def _sleep_if_needed(self) -> None:
        if self.request_delay_seconds > 0:
            self._sleep(self.request_delay_seconds)

    def _retry_delay(self, attempt: int, response: requests.Response | None = None) -> float:
        retry_after = _parse_retry_after_seconds(response)
        if retry_after is not None:
            return retry_after
        return self.retry_backoff_seconds * (2 ** max(0, attempt - 1))

    def _request(self, path: str, params: dict[str, Any] | None = None) -> requests.Response:
        self._sleep_if_needed()
        url = self.base_url + path.lstrip("/")
        max_attempts = self.retry_attempts + 1
        last_exc: requests.RequestException | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout_seconds)
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_exc = exc
                if attempt >= max_attempts:
                    raise
                delay = self._retry_delay(attempt)
                LOGGER.warning(
                    "Temporary GemeenteOplossingen request failure for %s, attempt %s/%s. "
                    "Retrying in %.2fs: %s",
                    url,
                    attempt,
                    max_attempts,
                    delay,
                    exc,
                )
                self._sleep(delay)
                continue

            if response.status_code in self.retry_status_codes and attempt < max_attempts:
                delay = self._retry_delay(attempt, response=response)
                LOGGER.warning(
                    "Temporary GemeenteOplossingen HTTP %s for %s, attempt %s/%s. "
                    "Retrying in %.2fs.",
                    response.status_code,
                    url,
                    attempt,
                    max_attempts,
                    delay,
                )
                self._sleep(delay)
                continue

            response.raise_for_status()
            return response

        if last_exc is not None:
            raise last_exc
        raise RuntimeError(f"Failed to fetch {url}")

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self._request(path, params=params)
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object from {response.url}, got {type(data).__name__}")
        return data

    def _get_json_or_none_on_404(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Fetch JSON but treat 404 as an absent resource."""
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
        records = result.get(field_name)
        if records is None and field_name != "model":
            records = result.get("model")
        if records is None:
            records = []
        if not isinstance(records, list):
            raise ValueError(f"Expected response field 'result.{field_name}' to be a list")
        if not all(isinstance(record, dict) for record in records):
            raise ValueError(f"Expected every item in 'result.{field_name}' to be an object")
        return records

    def _fetch_paged_result_list(
        self,
        path: str,
        field_name: str,
        *,
        page_size: int = 100,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all records from a paginated nested relation endpoint.

        Several Open Raadsinformatie relation endpoints accept ``offset`` and
        ``limit`` but do not expose a dedicated count method in the connector.
        Walking pages until a short or empty page prevents silently missing
        meeting-level or agenda-item-level relations when a meeting has more
        records than the API default page size.
        """
        if page_size <= 0:
            raise ValueError("page_size must be greater than 0")

        records: list[dict[str, Any]] = []
        offset = 0
        base_params = dict(params or {})

        while True:
            page_params = {**base_params, "limit": page_size, "offset": offset}
            page = self._result_list(self._get_json(path, params=page_params), field_name)
            if not page:
                break
            records.extend(page)
            if len(page) < page_size:
                break
            offset += len(page)

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

    def fetch_meeting_count(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> int:
        """Fetch the count of documented /meetings records.

        Relation backfill should use this documented endpoint for meeting
        discovery instead of the legacy, undocumented /meetingsessions route.
        """
        params: dict[str, Any] = {"limit": 1, "offset": 0}
        if date_from is not None:
            params["date_from"] = date_from
        if date_to is not None:
            params["date_to"] = date_to
        payload = self._get_json("meetings", params=params)
        result = self._result(payload)
        if "totalCount" in result:
            return int(result.get("totalCount", 0))
        return len(self._result_list(payload, "meetings"))

    def fetch_meetings_page(
        self,
        *,
        limit: int,
        offset: int,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch one page from the documented /meetings endpoint."""
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if offset < 0:
            raise ValueError("offset must be 0 or greater")
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if date_from is not None:
            params["date_from"] = date_from
        if date_to is not None:
            params["date_to"] = date_to
        payload = self._get_json("meetings", params=params)
        return self._result_list(payload, "meetings")

    def fetch_all_meetings(
        self,
        *,
        batch_size: int = 100,
        max_meetings: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch meetings through the documented /meetings pagination path."""
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0")
        if max_meetings is not None and max_meetings <= 0:
            raise ValueError("max_meetings must be greater than 0 when provided")

        total_count = self.fetch_meeting_count(date_from=date_from, date_to=date_to)
        target_count = min(total_count, max_meetings) if max_meetings is not None else total_count
        meetings: list[dict[str, Any]] = []
        offset = 0
        while offset < target_count:
            limit = min(batch_size, target_count - offset)
            page = self.fetch_meetings_page(
                limit=limit,
                offset=offset,
                date_from=date_from,
                date_to=date_to,
            )
            if not page:
                break
            meetings.extend(page)
            offset += len(page)
            if len(page) < limit:
                break
        return meetings

    def fetch_latest_meetings(self, limit: int) -> list[dict[str, Any]]:
        """Fetch latest meetings via the documented /meetings endpoint."""
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        total_count = self.fetch_meeting_count()
        offset = max(0, total_count - limit)
        return self.fetch_meetings_page(limit=limit, offset=offset)

    def fetch_meeting_session_count(self) -> int:
        """Fetch count from the legacy /meetingsessions endpoint.

        This method keeps its historical behavior for backwards compatibility
        with older callers and tests. New relation discovery should prefer
        fetch_meeting_count(), fetch_meetings_page(), fetch_all_meetings(),
        or fetch_latest_meetings().
        """
        return self.fetch_legacy_meeting_session_count()

    def fetch_meeting_sessions_page(self, *, limit: int, offset: int) -> list[dict[str, Any]]:
        """Fetch one page from the undocumented legacy /meetingsessions endpoint.

        This method keeps its historical behavior for backwards compatibility
        with existing callers and tests. New relation backfill discovery should
        not call this method. Use fetch_meetings_page(), fetch_all_meetings(),
        fetch_latest_meetings(), or fetch_latest_meeting_sessions() instead.
        """
        return self.fetch_legacy_meeting_sessions_page(limit=limit, offset=offset)

    def fetch_latest_meeting_sessions(self, limit: int) -> list[dict[str, Any]]:
        """Fetch latest records from the legacy /meetingsessions endpoint.

        This method intentionally keeps its historical tail-offset behavior so
        existing callers and tests remain compatible. New relation discovery
        should avoid this legacy endpoint and call fetch_latest_meetings() or
        fetch_all_meetings() instead.
        """
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        total_count = self.fetch_meeting_session_count()
        offset = max(0, total_count - limit)
        return self.fetch_meeting_sessions_page(limit=limit, offset=offset)

    def fetch_legacy_meeting_session_count(self) -> int:
        """Fetch count from the undocumented legacy /meetingsessions endpoint.

        This is intentionally isolated for diagnostics or emergency fallback.
        Relation backfill should prefer the documented /meetings methods above.
        """
        payload = self._get_json("meetingsessions", params={"limit": 1, "offset": 0})
        result = self._result(payload)
        total_count = result.get("totalCount", 0)
        return int(total_count)

    def fetch_legacy_meeting_sessions_page(
        self,
        *,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        """Fetch one page from the undocumented legacy /meetingsessions endpoint."""
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if offset < 0:
            raise ValueError("offset must be 0 or greater")
        payload = self._get_json("meetingsessions", params={"limit": limit, "offset": offset})
        return self._result_list(payload, "meetingsessions")

    def fetch_latest_legacy_meeting_sessions(self, limit: int) -> list[dict[str, Any]]:
        """Fetch latest records from the undocumented legacy /meetingsessions endpoint."""
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        total_count = self.fetch_legacy_meeting_session_count()
        offset = max(0, total_count - limit)
        return self.fetch_legacy_meeting_sessions_page(limit=limit, offset=offset)

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
        """Fetch all pages from /meetings/{meeting_id}/meetingitems."""
        return self._fetch_paged_result_list(f"meetings/{meeting_id}/meetingitems", "meetingitems")

    def fetch_meeting_documents(self, meeting_id: int | str) -> list[dict[str, Any]]:
        """Fetch all pages from /meetings/{meeting_id}/documents."""
        return self._fetch_paged_result_list(f"meetings/{meeting_id}/documents", "documents")

    def fetch_meeting_item_documents(self, meeting_item_id: int | str) -> list[dict[str, Any]]:
        """Fetch all pages from /meetingitems/{meeting_item_id}/documents."""
        return self._fetch_paged_result_list(f"meetingitems/{meeting_item_id}/documents", "documents")


    def _fetch_counted_collection(
        self,
        path: str,
        field_name: str,
        *,
        batch_size: int = 100,
        max_records: int | None = None,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch a top-level paginated collection defensively."""
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0")
        if max_records is not None and max_records <= 0:
            raise ValueError("max_records must be greater than 0 when provided")

        base_params = dict(params or {})
        count_payload = self._get_json(path, params={**base_params, "limit": 1, "offset": 0})
        result = self._result(count_payload)
        total_count = result.get("totalCount")
        if total_count is None:
            first_page = self._result_list(count_payload, field_name)
            if len(first_page) < 1:
                return []
            records = list(first_page)
            offset = len(records)
            while True:
                if max_records is not None and len(records) >= max_records:
                    return records[:max_records]
                limit = batch_size if max_records is None else min(batch_size, max_records - len(records))
                page = self._result_list(
                    self._get_json(path, params={**base_params, "limit": limit, "offset": offset}),
                    field_name,
                )
                if not page:
                    break
                records.extend(page)
                if len(page) < limit:
                    break
                offset += len(page)
            return records

        target_count = min(int(total_count), max_records) if max_records is not None else int(total_count)
        records: list[dict[str, Any]] = []
        offset = 0
        while offset < target_count:
            limit = min(batch_size, target_count - offset)
            page = self._result_list(
                self._get_json(path, params={**base_params, "limit": limit, "offset": offset}),
                field_name,
            )
            if not page:
                break
            records.extend(page)
            offset += len(page)
            if len(page) < limit:
                break
        return records

    def fetch_all_groups(
        self,
        *,
        batch_size: int = 100,
        max_records: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all public /groups records."""
        return self._fetch_counted_collection(
            "groups",
            "groups",
            batch_size=batch_size,
            max_records=max_records,
        )

    def fetch_all_persons(
        self,
        *,
        batch_size: int = 100,
        max_records: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all public /persons records."""
        return self._fetch_counted_collection(
            "persons",
            "persons",
            batch_size=batch_size,
            max_records=max_records,
        )

    def fetch_all_roles(
        self,
        *,
        batch_size: int = 100,
        max_records: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all public /roles records."""
        return self._fetch_counted_collection(
            "roles",
            "roles",
            batch_size=batch_size,
            max_records=max_records,
        )

    def fetch_all_positions(
        self,
        *,
        batch_size: int = 100,
        max_records: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all public /positions records."""
        return self._fetch_counted_collection(
            "positions",
            "positions",
            batch_size=batch_size,
            max_records=max_records,
        )

    def fetch_persons_by_group_id(self, group_id: int | str) -> list[dict[str, Any]]:
        """Fetch grounded group membership from /groups/{groupId}/persons."""
        return self._fetch_paged_result_list(f"groups/{group_id}/persons", "persons")

    def build_document_download_url(self, document_id: int | str) -> str:
        return f"{self.base_url}documents/{document_id}/download"

    def download_document(self, document_id: int | str) -> bytes:
        response = self._request(f"documents/{document_id}/download")
        return response.content


def _meeting_to_legacy_meeting_session(meeting: dict[str, Any]) -> dict[str, Any]:
    """Return a minimal legacy session wrapper for documented /meetings records."""
    return {
        "id": meeting.get("id"),
        "meeting": meeting,
        "container": {"meeting": meeting},
    }


def _parse_retry_after_seconds(response: requests.Response | None) -> float | None:
    if response is None:
        return None
    value = response.headers.get("Retry-After")
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        return max(0.0, retry_at.timestamp() - time.time())
