"""Raw relational harvest helpers for meeting and agenda-item context."""

from __future__ import annotations

from typing import Any, Protocol


class RelationConnector(Protocol):
    """Connector methods needed by the raw relation harvest."""

    def fetch_meeting_sessions_page(self, *, limit: int, offset: int) -> list[dict[str, Any]]: ...

    def fetch_meeting(self, meeting_id: int | str) -> dict[str, Any] | None: ...

    def fetch_meeting_items(self, meeting_id: int | str) -> list[dict[str, Any]]: ...

    def fetch_meeting_documents(self, meeting_id: int | str) -> list[dict[str, Any]]: ...

    def fetch_meeting_item_documents(self, meeting_item_id: int | str) -> list[dict[str, Any]]: ...


def _as_source_id(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def extract_meeting_id_from_session(session: dict[str, Any]) -> str | None:
    """Extract the linked meeting ID from a meetingsession record.

    GemeenteOplossingen exposes the useful meeting reference through
    `container.meeting.id`. A defensive fallback to a top-level `meeting.id` is
    included for source records that are shaped slightly differently.
    """

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


def fetch_meeting_sessions(
    connector: RelationConnector,
    *,
    scan_limit: int,
    batch_size: int = 100,
) -> list[dict[str, Any]]:
    """Fetch a bounded number of meetingsession records."""

    if scan_limit <= 0:
        raise ValueError("scan_limit must be greater than 0")
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than 0")

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
) -> dict[str, Any]:
    """Collect raw meetings, meeting items and document relation records.

    This step intentionally keeps the output raw. Canonical models and public
    JSONL relation exports are handled in later steps of issue #15.
    """

    if meeting_item_limit is not None and meeting_item_limit <= 0:
        raise ValueError("meeting_item_limit must be greater than 0 when provided")

    meeting_sessions = fetch_meeting_sessions(
        connector,
        scan_limit=meeting_scan_limit,
        batch_size=meeting_session_batch_size,
    )
    candidate_meeting_ids = stable_unique(
        [
            meeting_id
            for session in meeting_sessions
            if (meeting_id := extract_meeting_id_from_session(session)) is not None
        ]
    )

    meetings: list[dict[str, Any]] = []
    skipped_meeting_ids: list[str] = []
    meeting_items: list[dict[str, Any]] = []
    meeting_documents: list[dict[str, Any]] = []
    meeting_item_documents: list[dict[str, Any]] = []

    item_budget_remaining = meeting_item_limit

    for meeting_id in candidate_meeting_ids:
        meeting = connector.fetch_meeting(meeting_id)
        if meeting is None:
            skipped_meeting_ids.append(meeting_id)
            continue

        meetings.append(meeting)

        documents_for_meeting = connector.fetch_meeting_documents(meeting_id)
        for document in documents_for_meeting:
            meeting_documents.append({"meeting_id": meeting_id, "document": document})

        if item_budget_remaining is not None and item_budget_remaining <= 0:
            continue

        items_for_meeting = connector.fetch_meeting_items(meeting_id)
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
            documents_for_item = connector.fetch_meeting_item_documents(meeting_item_id)
            for document in documents_for_item:
                meeting_item_documents.append(
                    {
                        "meeting_id": meeting_id,
                        "meeting_item_id": meeting_item_id,
                        "document": document,
                    }
                )

    return {
        "meeting_sessions": meeting_sessions,
        "candidate_meeting_ids": candidate_meeting_ids,
        "skipped_meeting_ids": skipped_meeting_ids,
        "meetings": meetings,
        "meeting_items": meeting_items,
        "meeting_documents": meeting_documents,
        "meeting_item_documents": meeting_item_documents,
        "summary": {
            "meeting_sessions_seen": len(meeting_sessions),
            "candidate_meetings_seen": len(candidate_meeting_ids),
            "meetings_seen": len(meetings),
            "meetings_skipped": len(skipped_meeting_ids),
            "meeting_items_seen": len(meeting_items),
            "meeting_document_relations_seen": len(meeting_documents),
            "meeting_item_document_relations_seen": len(meeting_item_documents),
        },
    }
