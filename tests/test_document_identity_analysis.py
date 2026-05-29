from __future__ import annotations

from open_ris_monitor.analysis.document_identity import (
    analyze_document_identity,
    analyze_document_types,
    normalize_document_type,
)


def test_analyze_document_identity_detects_unique_composite_keys() -> None:
    documents = [
        {"id": "huizen-document-1", "source_id": "1", "source_object_id": "10"},
        {"id": "huizen-document-2", "source_id": "2", "source_object_id": "20"},
    ]

    report = analyze_document_identity(documents)

    assert report["documents_total"] == 2
    assert report["source_id"]["duplicate_count"] == 0
    assert report["source_object_id"]["duplicate_count"] == 0
    assert report["composite_source_key"]["duplicate_count"] == 0
    assert report["recommended_identity_key"] == "municipality_id + source_system_id + source_id + source_object_id"


def test_normalize_document_type_maps_known_source_values() -> None:
    assert normalize_document_type("Raadsvoorstel") == "proposal"
    assert normalize_document_type("Bijlage") == "attachment"
    assert normalize_document_type("Document ter kennisname (Inkomend)") == "notice"
    assert normalize_document_type("Uitnodigingen (Intern)") == "invitation"
    assert normalize_document_type("Rapportage (Intern)") == "report"
    assert normalize_document_type("Toezeggingenlijst (Intern)") == "commitment"
    assert normalize_document_type("Verzoek om informatie (Inkomend)") == "request"
    assert normalize_document_type("Zienswijze (Inkomend)") == "objection_or_response"
    assert normalize_document_type("Onbekend") == "unknown"


def test_analyze_document_types_reports_unknown_count() -> None:
    documents = [
        {"document_type": "Raadsvoorstel"},
        {"document_type": "Document ter kennisname (Inkomend)"},
        {"document_type": "Onbekend"},
    ]

    report = analyze_document_types(documents)

    assert report["documents_total"] == 3
    assert report["unknown_document_type_count"] == 1
    assert report["unknown_document_type_percentage"] == 33.33
    assert report["mapping"]["Document ter kennisname (Inkomend)"]["normalized_document_type"] == "notice"
