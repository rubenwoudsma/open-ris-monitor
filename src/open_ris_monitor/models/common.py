"""Shared model base classes."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CanonicalModel(BaseModel):
    """Base class for canonical Open RIS Monitor models."""

    model_config = ConfigDict(extra="forbid")


class SourceTrackedModel(CanonicalModel):
    """Base class for records that originate from a source system."""

    id: str
    source_id: str | None = None
    retrieved_at: datetime
