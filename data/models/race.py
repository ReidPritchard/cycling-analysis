"""
Race-related type definitions and data models.
"""

from typing import Any, TypedDict


class StageData(TypedDict, total=False):
    """Type definition for stage data structure."""

    stage_url: str
    distance: str | None
    profile_icon: str | None
    stage_type: str | None
    vertical_meters: int | None
    avg_temperature: float | None
    date: str | None
    departure: str | None
    arrival: str | None
    won_how: str | None
    race_startlist_quality_score: float | None
    profile_score: float | None
    pcs_points_scale: str | None
    uci_points_scale: str | None
    avg_speed_winner: float | None
    start_time: str | None
    climbs: list[dict[str, Any]]
    results: list[dict[str, Any]] | None
    general_classification: list[dict[str, Any]] | None
    """
    Example:
    points_classification: [
        {
            "rider_name": "Wiebes Lorena",
            "rider_url": "rider/lorena-wiebes",
            "rider_number": 47,
            "team_name": "Team SD Worx - Protime",
            "team_url": "team/team-sd-worx-protime-2025",
            "rank": 1,
            "prev_rank": 1,
            "points": 197,
            "age": 26,
            "nationality": "NL",
            "pcs_points": 197,
            "uci_points": 0
        },
        ...
    ]
    """
    points_classification: list[dict[str, Any]] | None
    kom_classification: list[dict[str, Any]] | None
    youth_classification: list[dict[str, Any]] | None
    team_classification: list[dict[str, Any]] | None


class ComputedRaceInfo(TypedDict, total=False):
    """Type definition for computed properties of a race."""

    # FIXME: Add more computed properties based on
    # what information provides insights for the user

    total_distance: str | None
    total_distance_completed: str | None
    total_distance_incomplete: str | None
    total_vertical_meters: int | None

    stages_completed: int | None
    stages_incomplete: int | None
    shortest_stage: dict[str, Any] | None
    longest_stage: dict[str, Any] | None
    avg_stage_distance: float | None
    avg_stage_vertical_meters: float | None
    # most_common_win_type:

    climbs_completed: int | None
    climbs_incomplete: int | None


class RaceData(TypedDict, total=False):
    """Type definition for race data structure."""

    race_data: dict[str, Any]
    computed_race_info: ComputedRaceInfo | None
    stages: list[StageData]
    climbs: list[dict[str, Any]]
    fetched_at: str
    error: str | None
