from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class HarvestRun:
    id: str
    municipality_id: str
    source_system_id: str
    started_at: str
    finished_at: str | None = None
    status: str = "running"
    mode: str = "latest"
    batch_size: int | None = None
    max_documents: int | None = None
    meetings_seen: int = 0
    agenda_items_seen: int = 0
    documents_seen: int = 0
    documents_normalized: int = 0
    documents_committed: int = 0
    documents_downloaded_temporarily: int = 0
    quality_issues_detected: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "municipality_id": self.municipality_id,
            "source_system_id": self.source_system_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status,
            "mode": self.mode,
            "batch_size": self.batch_size,
            "max_documents": self.max_documents,
            "meetings_seen": self.meetings_seen,
            "agenda_items_seen": self.agenda_items_seen,
            "documents_seen": self.documents_seen,
            "documents_normalized": self.documents_normalized,
            "documents_committed": self.documents_committed,
            "documents_downloaded_temporarily": self.documents_downloaded_temporarily,
            "quality_issues_detected": self.quality_issues_detected,
        }
