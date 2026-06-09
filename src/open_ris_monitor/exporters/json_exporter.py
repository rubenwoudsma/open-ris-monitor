"""JSON and JSONL exporters."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel


def _to_jsonable(record: Any) -> Any:
    if isinstance(record, BaseModel):
        return record.model_dump(mode="json")
    return record


def _as_public_string(value: Any) -> str | None:
    """Return a stripped public string, or None for empty values."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_public_int(value: Any) -> int | None:
    """Return an integer for public metadata, or None when unavailable."""
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed < 0:
        return None
    return parsed


def _as_public_date(value: Any) -> str | None:
    """Return YYYY-MM-DD from a datetime-like value, or None."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()

    text = str(value).strip()
    if not text:
        return None

    # Pydantic model_dump(mode="json") serializes datetimes to ISO strings.
    # Public document exports keep only the date for backward compatibility.
    return text[:10]


def _public_document_record(record: Any) -> dict[str, Any]:
    """Project a canonical document to the compact public export contract.

    The public `documents.jsonl` stays small and stable, but keeps the source
    metadata needed for traceability and clear UI rendering.
    """
    data = _to_jsonable(record)
    if not isinstance(data, dict):
        raise TypeError(f"Cannot export document record of type {type(record)!r}")

    normalized_type = _as_public_string(data.get("normalized_document_type"))
    compact_type = normalized_type or _as_public_string(data.get("type")) or "unknown"
    publication_date = _as_public_date(data.get("publication_datetime") or data.get("date"))
    download_url = _as_public_string(
        data.get("download_url") or data.get("url") or data.get("source_url")
    )

    return {
        "id": _as_public_string(data.get("id")) or "",
        "schema_version": _as_public_string(data.get("schema_version")) or "1.0.0",
        "title": _as_public_string(data.get("title")) or "",
        "type": compact_type,
        "document_type": _as_public_string(data.get("document_type")),
        "normalized_document_type": compact_type,
        "normalized_document_type_label": _as_public_string(
            data.get("normalized_document_type_label")
        ),
        "date": publication_date,
        "url": download_url or "",
        "download_url": download_url,
        "retrieved_at": _as_public_string(data.get("retrieved_at")),
        "source_id": _as_public_string(data.get("source_id")),
        "source_object_id": _as_public_string(data.get("source_object_id")),
        "filename": _as_public_string(data.get("filename")),
        "file_size_bytes": _as_public_int(data.get("file_size_bytes")),
        "text": data.get("text") if data.get("text") is not None else None,
    }


def write_json(path: Path, payload: Any) -> None:
    """Write a JSON document with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(
            _to_jsonable(payload),
            file,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            default=str,
        )
        file.write("\n")


def write_jsonl(path: Path, records: Iterable[Any]) -> None:
    """Write records as newline-delimited JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            payload = (
                _public_document_record(record)
                if path.name == "documents.jsonl"
                else _to_jsonable(record)
            )
            json.dump(payload, file, ensure_ascii=False, sort_keys=True, default=str)
            file.write("\n")
