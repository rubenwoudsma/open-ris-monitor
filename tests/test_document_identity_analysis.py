from __future__ import annotations

from open_ris_monitor.analysis.document_identity import (
    analyze_document_identity,
    analyze_document_types,
    normalize_document_type,
)


def test_analyze_document_identity_counts_duplicates() -> None:
    documents = [
        {"id": "huizen-document-1", "source_id": "1", "source_object_id": "10", "document_type": "Agenda"},
        {"id": "huizen-document-2", "source_id": "2", "source_object_id": "20", "document_type": "Bijlage"},
        {"id": "huizen-document-3", "source_id": "2", "source_object_id": "30", "document_type": "Bijlage"},
    ]

    report = analyze_document_identity(documents)

    assert report["documents_total"] == 3
    assert report["source_id"]["unique_count"] == 2
    assert report["source_id"]["duplicate_count"] == 2
    assert report["source_object_id"]["unique_count"] == 3


def test_document_type_analysis_proposes_compact_categories() -> None:
    documents = [
        {"document_type": "Agenda"},
        {"document_type": "Bijlage"},
        {"document_type": "Bijlage"},
        {"document_type": "Raadsvoorstel"},
        {"document_type": None},
    ]

    report = analyze_document_types(documents)

    assert report["documents_total"] == 5
    assert report["source_document_type_count"] == 4
    assert report["mapping"]["Bijlage"]["normalized_document_type"] == "attachment"
    assert report["mapping"]["Raadsvoorstel"]["normalized_document_type"] == "proposal"


def test_normalize_document_type_handles_known_values() -> None:
    assert normalize_document_type("Mededelingen") == "announcement"
    assert normalize_document_type("Ingekomen stuk") == "incoming_document"
    assert normalize_document_type("Resumés") == "minutes_or_summary"
    assert normalize_document_type("") == "unknown"
