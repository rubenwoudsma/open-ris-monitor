"""Raw relational harvest helpers for meeting and agenda-item context."""

from __future__ import annotations

from typing import Any, Literal, Protocol

import requests

RelationScanMode = Literal["full", "latest"]


class RelationConnector(Protocol):
    """Connector methods needed by the raw relation harvest."""

    def fetch_meetings_page(self, *, limit: int, offset: int) -> list[dict[str, Any]]: ...

    def fetch_latest_meetings(self, limit: int) -> list[dict[str, Any]]: ...

    def fetch_meeting_sessions_page(self, *, limit: int, offset: int) -> list[dict[str, Any]]: ...

    def fetch_latest_meeting_sessions(self, limit: int) -> list[dict[str, Any]]: ...

    def fetch_meeting(self, meeting_id: int | str) -> dict[str, Any] | None: ...

    def fetch_meeting_items(self, meeting_id: int | str) -> list[dict[str, Any]]: ...

    def fetch_meeting_documents(self, meeting_id: int | str) -> list[dict[str, Any]]: ...

    def fetch_meeting_item_documents(self, meeting_item_id: int | str) -> list[dict[str, Any]]: ...


def _as_source_id(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _short_error(exc: BaseException) -> dict[str, str]:
    return {
        "type": type(exc).__name__,
        "message": str(exc)[:500],
    }


def _is_relation_fetch_error(exc: BaseException) -> bool:
    """Return whether a relation endpoint error should not fail the whole harvest."""
    return isinstance(exc, requests.RequestException | ValueError)


def extract_meeting_id_from_session(session: dict[str, Any]) -> str | None:
    """Extract the linked meeting ID from a legacy meetingsession record."""
    container = session.get("container")
    if isinstance(container, dict):
        meeting = container.get("meeting")
        if isinstance(meeting, dict):
            meeting_id = _as_source_id(meeting.get("id"))
            if meeting_id is not None:
                return meeting_id

    meeting = session.get("meeting")
    if isinstance(meeting, dict):
        return _as_source_id(meeting.get("id"))

    return None


def stable_unique(values: list[str]) -> list[str]:
    """Return unique values while preserving first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def fetch_meetings(
    connector: RelationConnector,
    *,
    scan_limit: int,
    batch_size: int = 100,
    scan_mode: RelationScanMode = "full",
) -> list[dict[str, Any]]:
    """Fetch a bounded number of meetings from the documented /meetings endpoint."""
    if scan_limit <= 0:
        raise ValueError("scan_limit must be greater than 0")
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than 0")
    if scan_mode not in {"full", "latest"}:
        raise ValueError("scan_mode must be 'full' or 'latest'")

    if scan_mode == "latest":
        return connector.fetch_latest_meetings(scan_limit)

    meetings: list[dict[str, Any]] = []
    offset = 0
    while len(meetings) < scan_limit:
        limit = min(batch_size, scan_limit - len(meetings))
        page = connector.fetch_meetings_page(limit=limit, offset=offset)
        if not page:
            break
        meetings.extend(page)
        offset += len(page)
        if len(page) < limit:
            break
    return meetings


def fetch_meeting_sessions(
    connector: RelationConnector,
    *,
    scan_limit: int,
    batch_size: int = 100,
    scan_mode: RelationScanMode = "full",
) -> list[dict[str, Any]]:
    """Fetch legacy meetingsession records.

    This helper is retained for backwards compatibility, but #69 relation harvests
    use the documented /meetings traversal instead of /meetingsessions.
    """
    if scan_limit <= 0:
        raise ValueError("scan_limit must be greater than 0")
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than 0")
    if scan_mode not in {"full", "latest"}:
        raise ValueError("scan_mode must be 'full' or 'latest'")

    if scan_mode == "latest":
        return connector.fetch_latest_meeting_sessions(scan_limit)

    sessions: list[dict[str, Any]] = []
    offset = 0
    while len(sessions) < scan_limit:
        limit = min(batch_size, scan_limit - len(sessions))
        page = connector.fetch_meeting_sessions_page(limit=limit, offset=offset)
        if not page:
            break
        sessions.extend(page)
        offset += len(page)
        if len(page) < limit:
            break
    return sessions


def collect_raw_relation_harvest(
    connector: RelationConnector,
    *,
    meeting_scan_limit: int,
    meeting_session_batch_size: int = 100,
    meeting_item_limit: int | None = None,
    meeting_session_scan_mode: RelationScanMode = "full",
) -> dict[str, Any]:
    """Collect raw meetings, meeting items and document relation records.

    The relation scan uses the documented GemeenteOplossingen API traversal:
    /meetings, /meetings/{id}/meetingitems, /meetings/{id}/documents, and
    /meetingitems/{id}/documents. The legacy /meetingsessions endpoint is not
    used for the primary relation harvest because it is undocumented and can fail
    for deeper offsets.
    """
    if meeting_item_limit is not None and meeting_item_limit <= 0:
        raise ValueError("meeting_item_limit must be greater than 0 when provided")

    meetings = fetch_meetings(
        connector,
        scan_limit=meeting_scan_limit,
        batch_size=meeting_session_batch_size,
        scan_mode=meeting_session_scan_mode,
    )
    candidate_meeting_ids = stable_unique(
        [
            meeting_id
            for meeting in meetings
            if (meeting_id := _as_source_id(meeting.get("id"))) is not None
        ]
    )

    skipped_meeting_ids: list[str] = []
    relation_errors: list[dict[str, Any]] = []
    meeting_items: list[dict[str, Any]] = []
    meeting_documents: list[dict[str, Any]] = []
    meeting_item_documents: list[dict[str, Any]] = []
    item_budget_remaining = meeting_item_limit

    for meeting_id in candidate_meeting_ids:
        try:
            documents_for_meeting = connector.fetch_meeting_documents(meeting_id)
        except Exception as exc:
            if not _is_relation_fetch_error(exc):
                raise
            relation_errors.append(
                {
                    "scope": "meeting_documents",
                    "meeting_id": meeting_id,
                    "error": _short_error(exc),
                }
            )
            documents_for_meeting = []

        for document in documents_for_meeting:
            meeting_documents.append({"meeting_id": meeting_id, "document": document})

        if item_budget_remaining is not None and item_budget_remaining <= 0:
            continue

        try:
            items_for_meeting = connector.fetch_meeting_items(meeting_id)
        except Exception as exc:
            if not _is_relation_fetch_error(exc):
                raise
            relation_errors.append(
                {
                    "scope": "meeting_items",
                    "meeting_id": meeting_id,
                    "error": _short_error(exc),
                }
            )
            continue

        if item_budget_remaining is not None:
            items_for_meeting = items_for_meeting[:item_budget_remaining]
            item_budget_remaining -= len(items_for_meeting)

        for item in items_for_meeting:
            item_with_context = dict(item)
            item_with_context.setdefault("meeting_id", meeting_id)
            meeting_items.append(item_with_context)

            meeting_item_id = _as_source_id(item.get("id"))
            if meeting_item_id is None:
                continue

            try:
                documents_for_item = connector.fetch_meeting_item_documents(meeting_item_id)
            except Exception as exc:
                if not _is_relation_fetch_error(exc):
                    raise
                relation_errors.append(
                    {
                        "scope": "meeting_item_documents",
                        "meeting_id": meeting_id,
                        "meeting_item_id": meeting_item_id,
                        "error": _short_error(exc),
                    }
                )
                continue

            for document in documents_for_item:
                meeting_item_documents.append(
                    {
                        "meeting_id": meeting_id,
                        "meeting_item_id": meeting_item_id,
                        "document": document,
                    }
                )

    return {
        "meeting_sessions": [],
        "candidate_meeting_ids": candidate_meeting_ids,
        "skipped_meeting_ids": skipped_meeting_ids,
        "relation_errors": relation_errors,
        "meetings": meetings,
        "meeting_items": meeting_items,
        "meeting_documents": meeting_documents,
        "meeting_item_documents": meeting_item_documents,
        "summary": {
            "meeting_scan_source": "meetings",
            "meeting_session_scan_mode": meeting_session_scan_mode,
            "meeting_sessions_seen": 0,
            "candidate_meetings_seen": len(candidate_meeting_ids),
            "meetings_seen": len(meetings),
            "meetings_skipped": len(skipped_meeting_ids),
            "relation_errors_seen": len(relation_errors),
            "meeting_items_seen": len(meeting_items),
            "meeting_document_relations_seen": len(meeting_documents),
            "meeting_item_document_relations_seen": len(meeting_item_documents),
        },
    }
