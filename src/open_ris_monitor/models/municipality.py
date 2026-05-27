from __future__ import annotations

from pydantic import HttpUrl

from open_ris_monitor.models.common import CanonicalModel


class Municipality(CanonicalModel):
    id: str
    slug: str
    name: str
    country: str = "NL"
    official_identifier: str
    website_url: HttpUrl
    ris_url: HttpUrl
    timezone: str
