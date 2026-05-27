from __future__ import annotations

from datetime import datetime, timezone

GENERIC_FILENAMES = {"besluit.pdf", "bijlage.pdf", "document.pdf", "scan.pdf"}


def detect_generic_filename(document_id: str, filename: str | None) -> dict[str, str] | None:
    if not filename:
        return None
    if filename.lower() not in GENERIC_FILENAMES:
        return None
    return {
        "id": f"quality-{document_id}-generic-filename",
        "resource_type": "document",
        "resource_id": document_id,
        "severity": "warning",
        "issue_type": "generic_filename",
        "message": f"Document heeft generieke bestandsnaam: {filename}",
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }
