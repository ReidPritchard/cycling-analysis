"""
Race data processing and analytics calculations.
"""

from datetime import datetime
from typing import Any

from data.models.race import ComputedRaceInfo, RaceData, StageData


def _is_stage_completed(stage: StageData) -> bool:
    """Check if a stage has been completed based on available data."""
    # Determine if stage is completed
    is_completed = False

    today = datetime.now().date()
    stage_date = stage.get("date")
    try:
        # Assuming date format is "MM-DD" for 2025
        stage_date_obj = datetime.strptime(f"2025-{stage_date}", "%Y-%m-%d").date()
        is_completed = stage_date_obj <= today
    except ValueError:
        # Check for alternative completion indicators
        is_completed = (
            stage.get("results") is not None
            or stage.get("avg_speed_winner") is not None
            or stage.get("won_how") is not None
        )

    return is_completed


def calculate_stage_stats(stages: list[StageData]) -> dict[str, Any]:
    """Calculate statistics about stages."""
    if not stages:
        return {}

    distances = []
    vertical_meters = []
    completed_stages = []
    incomplete_stages = []

    for stage in stages:
        # Parse distance
        if stage.get("distance") is not None:
            distances.append(stage.get("distance"))

        # Parse vertical meters
        if stage.get("vertical_meters") is not None:
            vertical_meters.append(stage.get("vertical_meters"))

        # Check completion status
        if _is_stage_completed(stage):
            completed_stages.append(stage)
        else:
            incomplete_stages.append(stage)

    # Find shortest and longest stages
    shortest_stage = None
    longest_stage = None
    if distances and stages:
        stages_with_distances = [
            (stage, stage.get("distance"))
            for stage in stages
            if stage.get("distance") is not None
        ]

        if stages_with_distances:
            shortest_stage = min(stages_with_distances, key=lambda x: x[1])[0]
            longest_stage = max(stages_with_distances, key=lambda x: x[1])[0]

    return {
        "total_distance": sum(distances) if distances else None,
        "avg_distance": sum(distances) / len(distances) if distances else None,
        "avg_vertical_meters": (
            sum(vertical_meters) / len(vertical_meters) if vertical_meters else None
        ),
        "shortest_stage": shortest_stage,
        "longest_stage": longest_stage,
        "completed_count": len(completed_stages),
        "incomplete_count": len(incomplete_stages),
        "completed_distance": (
            sum(stage.get("distance", 0.0) for stage in completed_stages)
            if completed_stages
            else None
        ),
        "incomplete_distance": (
            sum(stage.get("distance", 0.0) for stage in incomplete_stages)
            if incomplete_stages
            else None
        ),
    }


def calculate_climb_stats(stages: list[StageData]) -> dict[str, Any]:
    """Calculate statistics about climbs across all stages."""
    total_climbs = 0
    completed_climbs = 0
    incomplete_climbs = 0

    for stage in stages:
        stage_climbs = stage.get("climbs", [])
        stage_climb_count = len(stage_climbs)
        total_climbs += stage_climb_count

        if _is_stage_completed(stage):
            completed_climbs += stage_climb_count
        else:
            incomplete_climbs += stage_climb_count

    return {
        "total_climbs": total_climbs,
        "completed_climbs": completed_climbs,
        "incomplete_climbs": incomplete_climbs,
    }


def prepare_race_data(race_data: RaceData) -> RaceData:
    """
    Calculate computed properties for the race data to provide insights.

    Computes statistics about stages, distances, completion status, and climbs
    to help users understand the race structure and progress.

    Args:
        race_data: Raw race data from load_race_data

    Returns:
        RaceData with computed_race_info populated
    """
    stages = race_data.get("stages", [])

    # Calculate stage statistics
    stage_stats = calculate_stage_stats(stages)

    # Calculate climb statistics
    climb_stats = calculate_climb_stats(stages)

    # Build computed race info
    computed_info: ComputedRaceInfo = {}

    # Stage distance information
    if stage_stats.get("total_distance") is not None:
        computed_info["total_distance"] = f"{stage_stats['total_distance']:.1f} km"

    if stage_stats.get("completed_distance") is not None:
        computed_info["total_distance_completed"] = (
            f"{stage_stats['completed_distance']:.1f} km"
        )

    if stage_stats.get("incomplete_distance") is not None:
        computed_info["total_distance_incomplete"] = (
            f"{stage_stats['incomplete_distance']:.1f} km"
        )

    # Stage completion information
    computed_info["stages_completed"] = stage_stats.get("completed_count")
    computed_info["stages_incomplete"] = stage_stats.get("incomplete_count")

    # Stage analysis
    computed_info["shortest_stage"] = stage_stats.get("shortest_stage")
    computed_info["longest_stage"] = stage_stats.get("longest_stage")

    if stage_stats.get("avg_distance") is not None:
        computed_info["avg_stage_distance"] = round(stage_stats["avg_distance"], 1)

    if stage_stats.get("avg_vertical_meters") is not None:
        computed_info["avg_stage_vertical_meters"] = round(
            stage_stats["avg_vertical_meters"], 1
        )

    # Total vertical meters
    total_vertical = sum(
        stage.get("vertical_meters", 0) or 0
        for stage in stages
        if stage.get("vertical_meters") is not None
    )
    if total_vertical > 0:
        computed_info["total_vertical_meters"] = total_vertical

    # Climb information
    computed_info["climbs_completed"] = climb_stats.get("completed_climbs")
    computed_info["climbs_incomplete"] = climb_stats.get("incomplete_climbs")

    # Store computed info in race data
    race_data["computed_race_info"] = computed_info

    return race_data
