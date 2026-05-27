"""Person model placeholder for later milestones."""

from __future__ import annotations

from open_ris_monitor.models.common import CanonicalModel


class Person(CanonicalModel):
    id: str
    name: str
