"""JSON and JSONL exporters."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel


def _to_jsonable(record: Any) -> Any:
    if isinstance(record, BaseModel):
        return record.model_dump(mode="json")
    return record


def write_json(path: Path, payload: Any) -> None:
    """Write a JSON document with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(_to_jsonable(payload), file, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        file.write("\n")


def write_jsonl(path: Path, records: Iterable[Any]) -> None:
    """Write records as newline-delimited JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            json.dump(_to_jsonable(record), file, ensure_ascii=False, sort_keys=True, default=str)
            file.write("\n")
