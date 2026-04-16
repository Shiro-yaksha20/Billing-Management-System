"""Repository utility helpers."""

from __future__ import annotations


def escape_like(term: str) -> str:
    """Escape SQL LIKE wildcard characters."""
    return term.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
