"""Organization model placeholder for later milestones."""

from __future__ import annotations

from open_ris_monitor.models.common import CanonicalModel


class Organization(CanonicalModel):
    id: str
    name: str
    organization_type: str | None = None
