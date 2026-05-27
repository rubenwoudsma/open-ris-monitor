"""Municipality model."""

from __future__ import annotations

from pydantic import HttpUrl

from open_ris_monitor.models.common import CanonicalModel


class Municipality(CanonicalModel):
    id: str
    slug: str
    name: str
    country: str = "NL"
    official_identifier: str | None = None
    website_url: HttpUrl | None = None
    ris_url: HttpUrl | None = None
    timezone: str = "Europe/Amsterdam"
