"""Exporters for writing data to JSON and JSONL formats."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel


class PydanticEncoder(json.JSONEncoder):
    """A JSON encoder that can handle Pydantic models and other common types."""

    def default(self, o: Any) -> Any:
        if isinstance(o, BaseModel):
            return o.model_dump()
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)


def write_json(path: Path, data: BaseModel | dict[str, Any]) -> None:
    """Write a dictionary or Pydantic model to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, cls=PydanticEncoder)
        handle.write("\n")


def write_jsonl(path: Path, records: Iterable[BaseModel | dict[str, Any]]) -> None:
    """Write an iterable of dictionaries or Pydantic models to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            if isinstance(record, BaseModel):
                # Use model_dump_json for performance with Pydantic models
                handle.write(record.model_dump_json() + "\n")
            else:
                json_string = json.dumps(record, ensure_ascii=False, cls=PydanticEncoder)
                handle.write(json_string + "\n")