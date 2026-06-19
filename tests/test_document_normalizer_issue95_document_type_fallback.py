"""Regression tests for issue #95 document type display fallback."""

from __future__ import annotations

from datetime import datetime, timezone

from open_ris_monitor.normalizers.gemeenteoplossingen import normalize_document


RETRIEVED_AT = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)


def _normalize(raw_document: dict[str, object]):
    return normalize_document(
        raw_document,
        municipality_id="gm0406",
        source_system_id="huizen-gemeenteoplossingen",
        retrieved_at=RETRIEVED_AT,
    )


def test_document_type_label_uses_explicit_source_label() -> None:
    document = _normalize(
        {
            "description": "Raadsvoorstel Vaststellen jaarverslag",
            "documentTypeLabel": "  Raadsvoorstel  ",
            "id": 25927,
        }
    )

    assert document.document_type == "Raadsvoorstel"
    assert document.normalized_document_type == "proposal"
    assert document.normalized_document_type_label == "Voorstel"


def test_document_type_label_uses_nested_fallback_when_direct_value_is_unknown() -> None:
    document = _normalize(
        {
            "description": "Bijlage bij agenda",
            "documentTypeLabel": "Onbekend",
            "documentType": {"label": "  Bijlage  "},
            "id": 25928,
        }
    )

    assert document.document_type == "Bijlage"
    assert document.normalized_document_type == "attachment"
    assert document.normalized_document_type_label == "Bijlage"


def test_document_type_label_uses_generic_document_when_no_reliable_source_exists() -> None:
    document = _normalize(
        {
            "description": "Algemeen document zonder betrouwbaar type",
            "documentTypeLabel": "unknown",
            "documentType": {"label": "-"},
            "id": 25929,
        }
    )

    assert document.document_type is None
    assert document.normalized_document_type == "unknown"
    assert document.normalized_document_type_label == "Document"


def test_document_type_label_uses_nested_name_fallback() -> None:
    document = _normalize(
        {
            "description": "Memo parkeerbeleid",
            "documentTypeLabel": None,
            "type": {"name": "Memo"},
            "id": 25930,
        }
    )

    assert document.document_type == "Memo"
    assert document.normalized_document_type == "memo_or_advice"
    assert document.normalized_document_type_label == "Memo of advies"
