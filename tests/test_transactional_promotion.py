from __future__ import annotations

from pathlib import Path

import pytest

from open_ris_monitor.pipeline import promote_staged


def _make_dir(path: Path, value: str) -> None:
    path.mkdir(parents=True)
    (path / "value.txt").write_text(value, encoding="utf-8")


def test_promotes_public_and_raw_directories(tmp_path: Path) -> None:
    staged_public = tmp_path / "stage" / "public"
    staged_raw = tmp_path / "stage" / "raw"
    target_public = tmp_path / "data" / "public"
    target_raw = tmp_path / "data" / "raw"
    _make_dir(staged_public, "new-public")
    _make_dir(staged_raw, "new-raw")
    _make_dir(target_public, "old-public")
    _make_dir(target_raw, "old-raw")

    promote_staged.promote_staged_directories(
        staged_public_dir=staged_public,
        target_public_dir=target_public,
        staged_raw_dir=staged_raw,
        target_raw_dir=target_raw,
    )

    assert (target_public / "value.txt").read_text(encoding="utf-8") == "new-public"
    assert (target_raw / "value.txt").read_text(encoding="utf-8") == "new-raw"


def test_promotion_failure_restores_both_targets(tmp_path: Path, monkeypatch) -> None:
    staged_public = tmp_path / "stage" / "public"
    staged_raw = tmp_path / "stage" / "raw"
    target_public = tmp_path / "data" / "public"
    target_raw = tmp_path / "data" / "raw"
    _make_dir(staged_public, "new-public")
    _make_dir(staged_raw, "new-raw")
    _make_dir(target_public, "old-public")
    _make_dir(target_raw, "old-raw")

    real_replace = promote_staged.os.replace
    calls = 0

    def failing_replace(source: Path, target: Path) -> None:
        nonlocal calls
        calls += 1
        if source == staged_raw:
            raise OSError("simulated promotion failure")
        real_replace(source, target)

    monkeypatch.setattr(promote_staged.os, "replace", failing_replace)

    with pytest.raises(OSError, match="simulated"):
        promote_staged.promote_staged_directories(
            staged_public_dir=staged_public,
            target_public_dir=target_public,
            staged_raw_dir=staged_raw,
            target_raw_dir=target_raw,
        )

    assert calls >= 4
    assert (target_public / "value.txt").read_text(encoding="utf-8") == "old-public"
    assert (target_raw / "value.txt").read_text(encoding="utf-8") == "old-raw"
