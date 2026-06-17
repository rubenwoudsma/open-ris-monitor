import json
from pathlib import Path

import pytest

from open_ris_monitor.pipeline.harvest_safety import (
    guard_against_output_shrink,
    protect_public_outputs,
    read_jsonl,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_latest_profile_merges_generated_rows_into_existing_public_output(tmp_path: Path) -> None:
    existing = tmp_path / "existing"
    generated = tmp_path / "generated"
    _write_jsonl(
        existing / "documents.jsonl",
        [
            {"id": "doc-1", "title": "historical"},
            {"id": "doc-2", "title": "old title"},
        ],
    )
    _write_jsonl(
        generated / "documents.jsonl",
        [{"id": "doc-2", "title": "new title"}, {"id": "doc-3", "title": "recent"}],
    )

    counts = protect_public_outputs(existing, generated, profile="latest")

    assert counts["documents.jsonl"] == (2, 3)
    assert read_jsonl(generated / "documents.jsonl") == [
        {"id": "doc-1", "title": "historical"},
        {"id": "doc-2", "title": "new title"},
        {"id": "doc-3", "title": "recent"},
    ]


def test_backfill_profile_fails_when_generated_output_shrinks(tmp_path: Path) -> None:
    existing = tmp_path / "existing"
    generated = tmp_path / "generated"
    _write_jsonl(existing / "documents.jsonl", [{"id": "doc-1"}, {"id": "doc-2"}])
    _write_jsonl(generated / "documents.jsonl", [{"id": "doc-1"}])

    with pytest.raises(RuntimeError, match="documents.jsonl: 2 -> 1"):
        guard_against_output_shrink(existing, generated)


def test_backfill_profile_can_shrink_with_explicit_override(tmp_path: Path) -> None:
    existing = tmp_path / "existing"
    generated = tmp_path / "generated"
    _write_jsonl(existing / "documents.jsonl", [{"id": "doc-1"}, {"id": "doc-2"}])
    _write_jsonl(generated / "documents.jsonl", [{"id": "doc-1"}])

    counts = guard_against_output_shrink(existing, generated, allow_output_shrink=True)

    assert counts["documents.jsonl"] == (2, 1)
