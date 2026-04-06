from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ModuleOut(BaseModel):
    id: str
    name: str
    version: str


class ReadinessRequestIn(BaseModel):
    """Client sends all saved item responses (localStorage payload shape)."""

    responses: dict[str, Any] = Field(
        ...,
        description="module_item_id -> { status, checks, attested, ... }",
    )
