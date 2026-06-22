from pathlib import Path

from open_ris_monitor.pipeline.run import (
    _dataset_totals,
    _latest_full_backfill_at,
    _merge_document_records,
)


def test_latest_document_merge_preserves_existing_dataset_records() -> None:
    existing = [
        {"id": "doc-1", "source_system_id": "go", "source_id": "1", "title": "Old"},
        {"id": "doc-2", "source_system_id": "go", "source_id": "2", "title": "Keep"},
    ]
    current = [
        {"id": "doc-1", "source_system_id": "go", "source_id": "1", "title": "Updated"},
        {"id": "doc-3", "source_system_id": "go", "source_id": "3", "title": "New"},
    ]

    merged = _merge_document_records(existing, current)

    assert [record["source_id"] for record in merged] == ["1", "2", "3"]
    assert merged[0]["title"] == "Updated"
    assert merged[1]["title"] == "Keep"
    assert merged[2]["title"] == "New"


def test_dataset_totals_use_existing_relation_exports_when_relations_not_harvested(tmp_path: Path) -> None:
    public_dir = tmp_path
    (public_dir / "meetings.jsonl").write_text('{"id":"m1"}\n{"id":"m2"}\n', encoding="utf-8")
    (public_dir / "meeting_items.jsonl").write_text('{"id":"a1"}\n', encoding="utf-8")
    (public_dir / "meeting_documents.jsonl").write_text('{"id":"r1"}\n', encoding="utf-8")
    (public_dir / "meeting_item_documents.jsonl").write_text('{"id":"r2"}\n{"id":"r3"}\n', encoding="utf-8")

    totals = _dataset_totals(
        public_dir=public_dir,
        documents_total=16342,
        normalized_relations=None,
    )

    assert totals == {
        "dataset_documents_total": 16342,
        "dataset_meetings_total": 2,
        "dataset_agenda_items_total": 1,
        "dataset_document_relations_total": 3,
    }


def test_latest_mode_preserves_previous_full_backfill_timestamp() -> None:
    previous_latest = {
        "mode": "full",
        "generated_at": "2026-06-21T18:40:00+00:00",
    }

    assert _latest_full_backfill_at(
        mode="latest",
        generated_at="2026-06-22T11:30:00+00:00",
        previous_latest=previous_latest,
    ) == "2026-06-21T18:40:00+00:00"


def test_full_mode_sets_current_run_as_full_backfill_timestamp() -> None:
    assert _latest_full_backfill_at(
        mode="full",
        generated_at="2026-06-22T11:30:00+00:00",
        previous_latest={},
    ) == "2026-06-22T11:30:00+00:00"
