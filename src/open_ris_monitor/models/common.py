from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CanonicalModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceTrackedModel(CanonicalModel):
    id: str
    source_id: Optional[str] = None
    retrieved_at: datetime
