from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from open_ris_monitor.pipeline import run as pipeline_run


@dataclass(frozen=True)
class ExportableRecord:
    id: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id}


def test_to_public_dicts_accepts_model_records_and_dicts() -> None:
    assert pipeline_run._to_public_dicts(
        [ExportableRecord("model-1"), {"id": "dict-1"}]
    ) == [{"id": "model-1"}, {"id": "dict-1"}]


def test_to_public_dicts_rejects_unknown_record_type() -> None:
    with pytest.raises(TypeError, match="Cannot export relation record"):
        pipeline_run._to_public_dicts([object()])


def test_write_public_relation_exports_writes_expected_jsonl_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, list[dict[str, Any]]] = {}

    def fake_write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
        calls[path.name] = records

    monkeypatch.setattr(pipeline_run, "write_jsonl", fake_write_jsonl)

    outputs = pipeline_run._write_public_relation_exports(
        tmp_path,
        {
            "meetings": [ExportableRecord("huizen-meeting-19")],
            "meeting_items": [ExportableRecord("huizen-meeting-item-142")],
            "meeting_documents": [ExportableRecord("huizen-meeting-19-document-3127")],
            "meeting_item_documents": [
                ExportableRecord("huizen-meeting-item-142-document-158")
            ],
        },
    )

    assert outputs == {
        "meetings": "meetings.jsonl",
        "meeting_items": "meeting_items.jsonl",
        "meeting_documents": "meeting_documents.jsonl",
        "meeting_item_documents": "meeting_item_documents.jsonl",
    }
    assert calls == {
        "meetings.jsonl": [{"id": "huizen-meeting-19"}],
        "meeting_items.jsonl": [{"id": "huizen-meeting-item-142"}],
        "meeting_documents.jsonl": [{"id": "huizen-meeting-19-document-3127"}],
        "meeting_item_documents.jsonl": [
            {"id": "huizen-meeting-item-142-document-158"}
        ],
    }


def test_build_latest_outputs_without_relations() -> None:
    assert pipeline_run._build_latest_outputs(enrich_checksums=False) == {
        "documents": "documents.jsonl",
        "harvest_runs": "harvest_runs.jsonl",
        "document_versions": None,
    }


def test_build_latest_outputs_with_relations_and_checksums() -> None:
    outputs = pipeline_run._build_latest_outputs(
        enrich_checksums=True,
        relation_outputs={
            "meetings": "meetings.jsonl",
            "meeting_items": "meeting_items.jsonl",
            "meeting_documents": "meeting_documents.jsonl",
            "meeting_item_documents": "meeting_item_documents.jsonl",
        },
    )

    assert outputs == {
        "documents": "documents.jsonl",
        "harvest_runs": "harvest_runs.jsonl",
        "document_versions": "document_versions.jsonl",
        "meetings": "meetings.jsonl",
        "meeting_items": "meeting_items.jsonl",
        "meeting_documents": "meeting_documents.jsonl",
        "meeting_item_documents": "meeting_item_documents.jsonl",
    }
