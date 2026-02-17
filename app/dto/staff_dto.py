"""Staff DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class StaffData:
    """Persisted staff data."""

    id: int
    name: str
    phone: Optional[str]
    role: Optional[str]
    active: bool
