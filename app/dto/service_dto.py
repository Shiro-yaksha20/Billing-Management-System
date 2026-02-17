"""Service DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class ServiceData:
    """Service DTO for UI consumption."""

    id: int
    name: str
    description: Optional[str]
    price: Optional[Decimal]
    duration_minutes: Optional[int]
    active: bool
    category: Optional[str]
    display_name: Optional[str]
    variant: Optional[str]
    notes: Optional[str]
