"""Quality issue model."""

from __future__ import annotations

from datetime import datetime

from open_ris_monitor.models.common import CanonicalModel


class QualityIssue(CanonicalModel):
    id: str
    resource_type: str
    resource_id: str
    severity: str
    issue_type: str
    message: str
    detected_at: datetime
