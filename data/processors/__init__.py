"""
Data processors for transforming and analyzing data.
"""

from .rider_matching import (
    match_fantasy_to_pcs,
    match_fantasy_to_race_data,
    match_riders_across_sources,
    # Legacy compatibility
    match_rider_names,
)
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
    # Unified matching functions
    "match_fantasy_to_pcs",
    "match_fantasy_to_race_data",
    "match_riders_across_sources",
    # Legacy compatibility
    "match_rider_names",
]
