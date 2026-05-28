"""Checksum enrichment for RIS documents."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable, Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from open_ris_monitor.models.document import Document
from open_ris_monitor.models.document_version import DocumentVersion


def sha256_bytes(content: bytes) -> str:
    """Return the SHA-256 hex digest for bytes."""
    return hashlib.sha256(content).hexdigest()


def load_previous_versions(path: Path) -> list[dict[str, Any]]:
    """Load an existing JSONL document_versions file if present."""
    if not path.exists():
        return []

    versions: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            import json

            versions.append(json.loads(line))
    return versions


def latest_version_by_document_id(versions: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return the latest known version per document id."""
    latest: dict[str, dict[str, Any]] = {}
    for version in versions:
        document_id = str(version.get("document_id", ""))
        if not document_id:
            continue
        previous = latest.get(document_id)
        if previous is None:
            latest[document_id] = version
            continue
        if str(version.get("retrieved_at", "")) >= str(previous.get("retrieved_at", "")):
            latest[document_id] = version
    return latest


def select_checksum_candidates(
    documents: list[Document],
    *,
    max_documents: int,
) -> list[Document]:
    """Select documents for checksum enrichment.

    The newest documents are selected first, because those are most likely to change.
    """
    if max_documents <= 0:
        return []

    def sort_key(document: Document) -> tuple[str, str]:
        publication = document.publication_datetime.isoformat() if document.publication_datetime else ""
        return (publication, document.source_id)

    return sorted(documents, key=sort_key, reverse=True)[:max_documents]


def build_document_version(
    document: Document,
    *,
    file_content: bytes,
    retrieved_at: datetime,
    previous_versions_by_document_id: dict[str, dict[str, Any]] | None = None,
) -> DocumentVersion:
    """Build a DocumentVersion from a downloaded document file."""
    digest = sha256_bytes(file_content)
    previous_versions_by_document_id = previous_versions_by_document_id or {}
    previous = previous_versions_by_document_id.get(document.id)

    previous_id: str | None = None
    content_changed: bool | None = None
    if previous is not None:
        previous_id = str(previous.get("id")) if previous.get("id") else None
        previous_sha = previous.get("sha256")
        content_changed = previous_sha != digest

    version_id = f"{document.id}-sha256-{digest[:16]}"

    return DocumentVersion(
        id=version_id,
        document_id=document.id,
        municipality_id=document.municipality_id,
        source_system_id=document.source_system_id,
        source_id=document.source_id,
        source_object_id=document.source_object_id,
        retrieved_at=retrieved_at,
        download_url=document.download_url,
        sha256=digest,
        downloaded_file_size_bytes=len(file_content),
        source_file_size_bytes=document.file_size_bytes,
        content_changed=content_changed,
        previous_version_id=previous_id,
        raw={
            "filename": document.filename,
            "document_type": document.document_type,
        },
    )


def enrich_document_versions(
    documents: list[Document],
    *,
    download_document: Callable[[str], bytes],
    retrieved_at: datetime,
    max_documents: int,
    previous_versions: list[dict[str, Any]] | None = None,
    request_delay_seconds: float = 0.0,
) -> list[DocumentVersion]:
    """Download selected documents temporarily and return checksum versions."""
    previous_index = latest_version_by_document_id(previous_versions or [])
    candidates = select_checksum_candidates(documents, max_documents=max_documents)
    versions: list[DocumentVersion] = []

    for index, document in enumerate(candidates):
        file_content = download_document(document.source_id)
        versions.append(
            build_document_version(
                document,
                file_content=file_content,
                retrieved_at=retrieved_at,
                previous_versions_by_document_id=previous_index,
            )
        )
        if request_delay_seconds > 0 and index < len(candidates) - 1:
            time.sleep(request_delay_seconds)

    return versions


def merge_document_versions(
    existing_versions: list[dict[str, Any]],
    new_versions: list[DocumentVersion],
) -> list[Any]:
    """Merge existing and new versions, deduplicating by version id."""
    merged: dict[str, Any] = {}
    for version in existing_versions:
        version_id = str(version.get("id", ""))
        if version_id:
            merged[version_id] = version
    for version in new_versions:
        merged[version.id] = version
    return list(merged.values())
