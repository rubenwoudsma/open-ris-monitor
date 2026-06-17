from __future__ import annotations

from datetime import date

from open_ris_monitor.analysis.unlinked_documents import (
    classify_unlinked_documents,
    summarize_unlinked_documents,
)


def test_classify_unlinked_documents_separates_near_current_and_historical_records() -> None:
    documents = [
        {
            "id": "huizen-document-linked",
            "source_id": "100",
            "description": "Linked agenda document",
            "document_type": "Raadsvoorstel",
            "meeting_date": "2026-06-10",
        },
        {
            "id": "huizen-document-near-current",
            "source_id": "101",
            "description": "Upcoming agenda document",
            "document_type": "Bijlage",
            "meeting_date": "2026-06-18",
        },
        {
            "id": "huizen-document-historical",
            "source_id": "102",
            "description": "Old document without relation",
            "document_type": "Motie",
            "publication_date": "2025-01-01",
        },
    ]
    relation_groups = [[{"document_source_id": "100", "meeting_id": "huizen-meeting-1"}], []]

    findings = classify_unlinked_documents(
        documents,
        relation_groups,
        reference_date=date(2026, 6, 17),
    )

    assert [finding.document_id for finding in findings] == [
        "huizen-document-near-current",
        "huizen-document-historical",
    ]
    assert findings[0].date_bucket == "near_current"
    assert (
        findings[0].suspected_reason
        == "near_current_or_future_meeting_relations_may_not_be_final_upstream"
    )
    assert findings[1].date_bucket == "historical"
    assert findings[1].suspected_reason == "no_exposed_relation_in_current_relation_exports"

    assert summarize_unlinked_documents(findings) == {
        "by_date_bucket": {"historical": 1, "near_current": 1},
        "by_suspected_reason": {
            "near_current_or_future_meeting_relations_may_not_be_final_upstream": 1,
            "no_exposed_relation_in_current_relation_exports": 1,
        },
        "by_document_type": {"Bijlage": 1, "Motie": 1},
    }
