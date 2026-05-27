"""Tests for JSON exporters."""

from __future__ import annotations

import json

from open_ris_monitor.exporters.json_exporter import write_jsonl


def test_write_jsonl_writes_one_record_per_line(tmp_path) -> None:
    path = tmp_path / "records.jsonl"

    write_jsonl(path, [{"id": "a"}, {"id": "b"}])

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"id": "a"}
    assert json.loads(lines[1]) == {"id": "b"}
