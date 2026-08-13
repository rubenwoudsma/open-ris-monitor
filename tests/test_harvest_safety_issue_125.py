from __future__ import annotations

import json
from pathlib import Path

import pytest

from open_ris_monitor.pipeline.harvest_safety import (
    guard_against_output_shrink,
    protect_public_outputs,
)
from open_ris_monitor.pipeline.record_identity import document_record_key
from open_ris_monitor.pipeline.run import _merge_document_records


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_issue125_allows_duplicate_compaction_when_no_document_identity_is_lost(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    existing = tmp_path / "existing"
    generated = tmp_path / "generated"
    _write_jsonl(
        existing / "documents.jsonl",
        [
            {"id": "huizen-document-1", "source_id": "1", "retrieved_at": "old-a"},
            {"id": "huizen-document-1", "source_id": "1", "retrieved_at": "old-b"},
            {"id": "huizen-document-2", "source_id": "2", "retrieved_at": "old-a"},
            {"id": "huizen-document-2", "source_id": "2", "retrieved_at": "old-b"},
        ],
    )
    _write_jsonl(
        generated / "documents.jsonl",
        [
            {"id": "huizen-document-1", "source_id": "1", "retrieved_at": "new"},
            {"id": "huizen-document-2", "source_id": "2", "retrieved_at": "new"},
            {"id": "huizen-document-3", "source_id": "3", "retrieved_at": "new"},
        ],
    )

    counts = guard_against_output_shrink(existing, generated)

    assert counts["documents.jsonl"] == (4, 3)
    output = capsys.readouterr().out
    assert "Safe duplicate compaction for documents.jsonl" in output
    assert "unique identities 2 -> 3" in output


def test_issue125_blocks_identity_loss_even_when_row_count_is_unchanged(tmp_path: Path) -> None:
    existing = tmp_path / "existing"
    generated = tmp_path / "generated"
    _write_jsonl(
        existing / "documents.jsonl",
        [{"id": "huizen-document-1"}, {"id": "huizen-document-2"}],
    )
    _write_jsonl(
        generated / "documents.jsonl",
        [{"id": "huizen-document-1"}, {"id": "huizen-document-3"}],
    )

    with pytest.raises(RuntimeError, match=r"missing identities=1 .*huizen-document-2"):
        guard_against_output_shrink(existing, generated)


def test_issue125_shrink_override_is_restricted_to_authoritative_profiles(tmp_path: Path) -> None:
    existing = tmp_path / "existing"
    generated = tmp_path / "generated"

    with pytest.raises(RuntimeError, match="only valid for backfill/full profiles"):
        protect_public_outputs(
            existing,
            generated,
            profile="public",
            allow_output_shrink=True,
        )


def test_issue125_document_merge_and_safety_share_canonical_identity() -> None:
    existing = [
        {
            "id": "huizen-document-42",
            "source_system_id": "huizen-gemeenteoplossingen",
            "source_id": "42",
            "title": "old",
        }
    ]
    current = [
        {
            "id": "huizen-document-42",
            "source_system_id": "huizen-gemeenteoplossingen-v2",
            "source_id": "42",
            "title": "new",
        }
    ]

    merged = _merge_document_records(existing, current)

    assert document_record_key(existing[0]) == "id:huizen-document-42"
    assert document_record_key(current[0]) == "id:huizen-document-42"
    assert len(merged) == 1
    assert merged[0]["title"] == "new"


def test_issue125_workflow_exposes_manual_backfill_shrink_approval() -> None:
    workflow = Path(".github/workflows/harvest.yml").read_text(encoding="utf-8")

    assert "allow_output_shrink:" in workflow
    assert 'allow_output_shrink="false"' in workflow
    assert 'if [ "$profile" != "backfill" ]; then' in workflow
    assert 'if [ -n "$max_documents" ] && [ "$max_documents" != "0" ]; then' in workflow
    assert "--allow-output-shrink" in workflow
    assert "steps.harvest-inputs.outputs.allow_output_shrink" in workflow
