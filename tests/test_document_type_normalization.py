from open_ris_monitor.normalizers.document_types import (
    clean_document_type_label,
    normalize_document_type,
)


def test_normalize_known_document_types() -> None:
    assert normalize_document_type("Raadsvoorstel").value == "proposal"
    assert normalize_document_type("Bijlage").value == "attachment"
    assert normalize_document_type("Document ter kennisname (Inkomend)").value == "notice"
    assert normalize_document_type("Toezeggingenlijst (Intern)").value == "commitment"
    assert normalize_document_type("Onbekend").value == "unknown"
    assert normalize_document_type("Onbekend").label == "Document"


def test_normalize_unseen_but_obvious_document_type() -> None:
    result = normalize_document_type("Nieuwe beleidsnota over parkeren")

    assert result.value == "policy_or_plan"
    assert result.label == "Beleid, plan of nota"


def test_clean_document_type_label_removes_whitespace() -> None:
    assert clean_document_type_label("  Raadsvoorstel\n\t2026  ") == "Raadsvoorstel 2026"


def test_null_like_document_type_values_are_generic_documents() -> None:
    for value in (None, "", "   ", "None", "null", "unknown", "Onbekend", "n/a", "-"):
        result = normalize_document_type(value)

        assert clean_document_type_label(value) is None
        assert result.value == "unknown"
        assert result.label == "Document"
