"""Business error types."""

from __future__ import annotations

from .validation_errors import ValidationError


class BusinessError(Exception):
    """Base class for business errors."""


class CustomerNotFoundError(BusinessError):
    """Raised when a customer cannot be found."""


class StaffNotFoundError(BusinessError):
    """Raised when a staff member cannot be found."""


class InsufficientDataError(ValidationError):
    """Raised when required data is missing."""


class DiscountExceedsSubtotalError(ValidationError):
    """Raised when a discount exceeds the subtotal."""


class NegativeTotalError(ValidationError):
    """Raised when a calculated total is negative."""

