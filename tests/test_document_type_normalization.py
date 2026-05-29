from open_ris_monitor.normalizers.document_types import normalize_document_type


def test_normalize_known_document_types() -> None:
    assert normalize_document_type("Raadsvoorstel").value == "proposal"
    assert normalize_document_type("Bijlage").value == "attachment"
    assert normalize_document_type("Document ter kennisname (Inkomend)").value == "notice"
    assert normalize_document_type("Toezeggingenlijst (Intern)").value == "commitment"
    assert normalize_document_type("Onbekend").value == "unknown"


def test_normalize_unseen_but_obvious_document_type() -> None:
    result = normalize_document_type("Nieuwe beleidsnota over parkeren")
    assert result.value == "policy_or_plan"
    assert result.label == "Beleid, plan of nota"
