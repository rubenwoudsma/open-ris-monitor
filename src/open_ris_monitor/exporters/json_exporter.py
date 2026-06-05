"""JSON and JSONL exporters with target-aware schema contract transformation."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel


def _apply_export_contracts(filename: str, data: dict[str, Any]) -> dict[str, Any]:
    """
    Transformeert en filtert de interne datastructuren naar het exacte 
    publieke exportcontract conform de v1.0.0 JSON-schemas.
    Removes additional properties and formats keys to prevent contract deviations.
    """
    if not isinstance(data, dict):
        return data

    # 1. CONTRACT VOOR: documents.jsonl
    if "documents" in filename:
        # Datum extraheren uit datetime object of string (YYYY-MM-DD)
        pub_date = data.get("publication_datetime")
        if pub_date:
            if hasattr(pub_date, "strftime"):
                pub_date = pub_date.strftime("%Y-%m-%d")
            else:
                pub_date = str(pub_date).split(" ")[0].split("T")[0]

        return {
            "id": str(data.get("id", "")),
            "schema_version": "1.0.0",
            "title": str(data.get("title", "")).strip(),
            "type": data.get("normalized_document_type") or "unknown",
            "date": pub_date if pub_date else None,
            "url": str(data.get("download_url") or data.get("source_url") or data.get("url", "")),
            "text": data.get("text") if data.get("text") is not None else None
        }

    # 2. CONTRACT VOOR: meetings.jsonl
    elif "meetings" in filename:
        return {
            "id": str(data.get("id", "")),
            "schema_version": "1.0.0",
            "title": str(data.get("title") or f"Vergadering {data.get('date', '')}").strip(),
            "date": str(data.get("date", "")),
            "start_time": data.get("start_time") or data.get("startTime") or None,
            "location": data.get("location") or None,
            "url": data.get("url") or None
        }

    # 3. CONTRACT VOOR: meeting_items.jsonl (agenda_item.schema.json)
    elif "meeting_items" in filename:
        return {
            "id": str(data.get("id", "")),
            "meeting_id": str(data.get("meeting_id", "")),
            "schema_version": "1.0.0",
            "title": str(data.get("title", "")).strip(),
            "number": data.get("number") or None,
            "sequence": data.get("sort_order") or data.get("sortOrder") or data.get("sequence") or None
        }

    # 4. CONTRACT VOOR: meeting_documents.jsonl / meeting_item_documents.jsonl (relation.schema.json)
    elif "document" in filename and "relation" in filename or "meeting_documents" in filename or "meeting_item_documents" in filename:
        if "item" in filename or "meeting_item_id" in data:
            export_type = "document_to_agenda_item"
            target_id = str(data.get("meeting_item_id") or data.get("target_id", ""))
        else:
            export_type = "document_to_meeting"
            target_id = str(data.get("meeting_id") or data.get("target_id", ""))

        source_id = str(data.get("document_id") or data.get("source_id", ""))

        return {
            "id": str(data.get("id", "")),
            "schema_version": "1.0.0",
            "source_id": source_id,
            "target_id": target_id,
            "type": export_type
        }

    return data


def _to_jsonable(record: Any, filename: str = "", is_public_export: bool = False) -> Any:
    """Convert supported model objects to JSON-serializable structures and conditionally apply contracts."""
    raw_data = record
    if isinstance(record, BaseModel):
        raw_data = record.model_dump(mode="json")
    elif hasattr(record, "to_dict") and callable(record.to_dict):
        raw_data = record.to_dict()
    elif is_dataclass(record) and not isinstance(record, type):
        raw_data = asdict(record)
    
    # Pas de contractfiltering ENKEL toe als we expliciet naar de publieke distributiemap schrijven
    if isinstance(raw_data, dict) and filename and is_public_export:
        return _apply_export_contracts(filename, raw_data)
        
    return raw_data


def write_json(path: Path, payload: Any) -> None:
    """Write a JSON document with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    filename = path.name.lower()
    
    # Controleer of het exportpad naar de publieke productiedata leidt
    is_public_export = "data/public" in path.as_posix()
    
    with path.open("w", encoding="utf-8") as file:
        json.dump(_to_jsonable(payload, filename, is_public_export), file, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        file.write("\n")


def write_jsonl(path: Path, records: Iterable[Any]) -> None:
    """Write records as newline-delimited JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    filename = path.name.lower()
    
    # Controleer of het exportpad naar de publieke productiedata leidt
    is_public_export = "data/public" in path.as_posix()
    
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            json.dump(_to_jsonable(record, filename, is_public_export), file, ensure_ascii=False, sort_keys=True, default=str)
            file.write("\n")
