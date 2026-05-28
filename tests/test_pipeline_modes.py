from __future__ import annotations

from open_ris_monitor.pipeline.run import parse_max_documents


def test_parse_max_documents_zero_means_no_cap() -> None:
    assert parse_max_documents(0) is None


def test_parse_max_documents_positive_value_is_cap() -> None:
    assert parse_max_documents(500) == 500
