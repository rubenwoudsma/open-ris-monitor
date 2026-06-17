from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable


def _field(record: Any, name: str) -> Any:
    if isinstance(record, dict):
        return record.get(name)
    return getattr(record, name, None)


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _add_identifier(result: set[str], value: Any) -> None:
    text = _as_text(value)
    if text:
        result.add(text)


def _parse_date(value: Any) -> date | None:
    text = _as_text(value)
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        pass
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _first_date(record: Any, field_names: Iterable[str]) -> date | None:
    for name in field_names:
        parsed = _parse_date(_field(record, name))
        if parsed is not None:
            return parsed
    raw = _field(record, "raw")
    if isinstance(raw, dict):
        for name in field_names:
            parsed = _parse_date(raw.get(name))
            if parsed is not None:
                return parsed
    return None


def document_identifiers(document: Any) -> set[str]:
    """Return source and canonical identifiers that may appear in relation records."""
    result: set[str] = set()
    _add_identifier(result, _field(document, "id"))
    _add_identifier(result, _field(document, "source_id"))
    _add_identifier(result, _field(document, "source_object_id"))
    _add_identifier(result, _field(document, "download_url"))
    _add_identifier(result, _field(document, "source_url"))
    raw = _field(document, "raw")
    if isinstance(raw, dict):
        _add_identifier(result, raw.get("id"))
        _add_identifier(result, raw.get("objectId"))
        _add_identifier(result, raw.get("object_id"))
        _add_identifier(result, raw.get("downloadUrl"))
        _add_identifier(result, raw.get("download_url"))
    return result


def relation_document_identifiers(relation: Any) -> set[str]:
    """Return document identifiers from meeting or agenda-item document relations."""
    result: set[str] = set()
    _add_identifier(result, _field(relation, "document_id"))
    _add_identifier(result, _field(relation, "document_source_id"))
    _add_identifier(result, _field(relation, "document_object_id"))
    _add_identifier(result, _field(relation, "document_url"))
    _add_identifier(result, _field(relation, "download_url"))
    document = _field(relation, "document")
    if isinstance(document, dict):
        _add_identifier(result, document.get("id"))
        _add_identifier(result, document.get("source_id"))
        _add_identifier(result, document.get("objectId"))
        _add_identifier(result, document.get("object_id"))
        _add_identifier(result, document.get("source_object_id"))
        _add_identifier(result, document.get("downloadUrl"))
        _add_identifier(result, document.get("download_url"))
    return result


@dataclass(frozen=True)
class UnlinkedDocumentFinding:
    document_id: str | None
    source_id: str | None
    title: str | None
    document_type: str | None
    publication_date: str | None
    meeting_date: str | None
    date_bucket: str
    suspected_reason: str


def _date_bucket(reference: date, meeting_date: date | None, publication_date: date | None) -> str:
    candidate = meeting_date or publication_date
    if candidate is None:
        return "unknown_date"
    delta = (candidate - reference).days
    if delta < -30:
        return "historical"
    if delta < -7:
        return "recent_past"
    if delta <= 7:
        return "near_current"
    return "future"


def _suspected_reason(bucket: str, has_meeting_date: bool) -> str:
    if bucket in {"near_current", "future"} and has_meeting_date:
        return "near_current_or_future_meeting_relations_may_not_be_final_upstream"
    if bucket == "unknown_date":
        return "missing_date_metadata_prevents_relation_window_classification"
    return "no_exposed_relation_in_current_relation_exports"


def classify_unlinked_documents(
    documents: Iterable[Any],
    relation_groups: Iterable[Iterable[Any]],
    *,
    reference_date: date | None = None,
) -> list[UnlinkedDocumentFinding]:
    """Classify documents not represented in current relation exports.

    This diagnostic intentionally does not create links. It compares canonical and
    source document identifiers against existing meeting-level and agenda-item-level
    relation exports, then groups the remaining documents into stable date buckets.
    """
    reference = reference_date or datetime.now(timezone.utc).date()
    related_identifiers: set[str] = set()
    for relations in relation_groups:
        for relation in relations:
            related_identifiers.update(relation_document_identifiers(relation))

    findings: list[UnlinkedDocumentFinding] = []
    for document in documents:
        if not document_identifiers(document).isdisjoint(related_identifiers):
            continue
        publication = _first_date(document, ("publication_date", "publicationDate", "published_at"))
        meeting = _first_date(document, ("meeting_date", "meetingDate", "date"))
        bucket = _date_bucket(reference, meeting, publication)
        findings.append(
            UnlinkedDocumentFinding(
                document_id=_as_text(_field(document, "id")),
                source_id=_as_text(_field(document, "source_id")),
                title=_as_text(_field(document, "title")) or _as_text(_field(document, "description")),
                document_type=_as_text(_field(document, "document_type"))
                or _as_text(_field(document, "documentTypeLabel")),
                publication_date=publication.isoformat() if publication is not None else None,
                meeting_date=meeting.isoformat() if meeting is not None else None,
                date_bucket=bucket,
                suspected_reason=_suspected_reason(bucket, meeting is not None),
            )
        )
    return findings


def summarize_unlinked_documents(findings: Iterable[UnlinkedDocumentFinding]) -> dict[str, dict[str, int]]:
    """Summarize unlinked diagnostics by date bucket, reason and document type."""
    buckets: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    document_types: Counter[str] = Counter()
    for finding in findings:
        buckets[finding.date_bucket] += 1
        reasons[finding.suspected_reason] += 1
        document_types[finding.document_type or "unknown"] += 1
    return {
        "by_date_bucket": dict(sorted(buckets.items())),
        "by_suspected_reason": dict(sorted(reasons.items())),
        "by_document_type": dict(sorted(document_types.items())),
    }
