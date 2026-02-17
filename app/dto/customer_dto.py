"""Customer DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class CustomerData:
    """Persisted customer data."""

    id: int
    name: str
    phone: str
    notes: Optional[str]
    last_visit_at: Optional[datetime]


@dataclass(frozen=True)
class CustomerSummary:
    """Customer summary with statistics."""

    customer: CustomerData
    total_visits: int
    total_spent: Decimal
