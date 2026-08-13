"""Stable identity helpers for incremental public export merges."""

from __future__ import annotations

import json
from typing import Any


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _json_key(record: dict[str, Any]) -> str:
    """Return a deterministic fallback key when no stable identifier exists."""

    return json.dumps(record, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str)


def document_record_key(record: dict[str, Any]) -> str:
    """Return the canonical identity used for document merges and safety checks.

    Public document exports always carry a deterministic canonical ``id``. Source
    identifiers remain fallback options for legacy or diagnostic records that predate
    the current public export contract.
    """

    canonical_id = _text(record.get("id"))
    if canonical_id:
        return f"id:{canonical_id}"

    source_system_id = _text(record.get("source_system_id")) or ""
    source_id = _text(record.get("source_id"))
    if source_id:
        return f"source:{source_system_id}:{source_id}"

    source_object_id = _text(record.get("source_object_id"))
    if source_object_id:
        return f"source-object:{source_system_id}:{source_object_id}"

    return f"json:{_json_key(record)}"


def public_record_key(record: dict[str, Any], *, filename: str | None = None) -> str:
    """Return a stable identity for one public JSONL record."""

    if filename == "documents.jsonl":
        return document_record_key(record)

    for key in (
        "id",
        "source_id",
        "document_id",
        "meeting_item_id",
        "meeting_id",
        "harvest_run_id",
    ):
        value = _text(record.get(key))
        if value:
            return f"{key}:{value}"
    return f"json:{_json_key(record)}"
