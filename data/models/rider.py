"""
Rider-related type definitions and data models.
"""

from typing import Any, TypedDict


class RiderData(TypedDict):
    """TypedDict for rider data structure."""

    full_name: str
    fantasy_name: str
    team: str
    stars: int
    pcs_data: dict[str, Any] | None
    pcs_matched_name: str | None
    pcs_rider_url: str | None
    matched_startlist_rider: dict[str, Any] | None
