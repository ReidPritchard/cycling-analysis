"""
Data processors for transforming and analyzing data.
"""

from .matching import match_rider_names
from .race_analytics import (
    calculate_climb_stats,
    calculate_stage_stats,
    prepare_race_data,
)
from .rider_analytics import (
    calculate_rider_demographics,
    calculate_rider_metrics,
    process_season_results,
)

__all__ = [
    "calculate_rider_metrics",
    "process_season_results",
    "calculate_rider_demographics",
    "prepare_race_data",
    "calculate_stage_stats",
    "calculate_climb_stats",
    "match_rider_names",
]
