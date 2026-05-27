"""Source system model."""

from __future__ import annotations

from pydantic import HttpUrl

from open_ris_monitor.models.common import CanonicalModel


class SourceSystem(CanonicalModel):
    id: str
    municipality_id: str
    vendor: str
    connector: str
    base_url: HttpUrl
    api_version: str | None = None
    active: bool = True
