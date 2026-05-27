"""Decision model placeholder for later milestones."""

from __future__ import annotations

from datetime import date

from open_ris_monitor.models.common import CanonicalModel


class Decision(CanonicalModel):
    id: str
    meeting_id: str | None = None
    agenda_item_id: str | None = None
    title: str
    decision_text: str | None = None
    decision_type: str | None = None
    result: str | None = None
    date_decided: date | None = None
