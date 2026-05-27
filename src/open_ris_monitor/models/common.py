"""Shared model configuration."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CanonicalModel(BaseModel):
    """Base model for canonical Open RIS Monitor objects."""

    model_config = ConfigDict(extra="forbid")
