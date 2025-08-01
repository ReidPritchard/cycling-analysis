"""
Pure analytics engine for calculating insights from matched data.

This module performs all analytics calculations separately from data loading
and matching. It operates on matched data and produces insights, metrics,
and computed properties.

Key principles:
- No data loading or matching logic
- Pure functions that take matched data and return analytics
- Clear separation between basic metrics and advanced analytics
- Modular design for different types of analysis
"""

import statistics
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from data.models.combined_analytics import (
    RaceAnalyticsSummary,
    RiderRaceAnalytics,
    StagePerformance,
)
from data.models.race import ComputedRaceInfo, RaceData, StageData
from data.models.unified import RiderMatchInfo

# =============================================================================
# Basic Rider Analytics
# =============================================================================


def calculate_basic_rider_metrics(matched_riders: dict[str, RiderMatchInfo]) -> pd.DataFrame:
    """
    Calculate basic metrics for matched riders using PCS data.

    Args:
        matched_riders: Dict mapping fantasy names to match information

    Returns:
        DataFrame with basic rider metrics
    """
    riders_data = []

    for fantasy_name, match_info in matched_riders.items():
        fantasy_rider = match_info.get("fantasy_rider", {})
        pcs_data = fantasy_rider.get("pcs_data", {})

        # Extract basic information
        rider_data = {
            "fantasy_name": fantasy_name,
            "full_name": fantasy_rider.get("full_name", ""),
            "team": fantasy_rider.get("team", ""),
            "position": fantasy_rider.get("position", ""),
            "stars": fantasy_rider.get("stars", 0),
            "has_pcs_data": match_info.get("has_pcs_data", False),
            "has_race_data": match_info.get("has_race_data", False),
            "canonical_name": match_info.get("canonical_name", ""),
        }

        # Process PCS data if available
        if pcs_data and "error" not in pcs_data:
            # Season results
            season_results = pcs_data.get("season_results", [])

            # Filter for current race only
            # FIXME: Pass race key through args
            race_results = [
                result
                for result in season_results
                if result.get("stage_url", "").startswith("race/tour-de-france-femmes/2025/")
            ]

            # Calculate totals
            total_pcs_points = sum(result.get("pcs_points", 0) for result in race_results)
            total_uci_points = sum(result.get("uci_points", 0) for result in race_results)

            # Calculate per-star ratios
            stars = rider_data["stars"]
            pcs_per_star = total_pcs_points / stars if stars > 0 else 0.0
            uci_per_star = total_uci_points / stars if stars > 0 else 0.0

            # Calculate consistency and trend
            consistency_score, trend_score = _calculate_consistency_and_trend(race_results)

            # Demographics
            demographics = _extract_demographics(pcs_data)

            # Update rider data
            rider_data.update(
                {
                    "total_pcs_points": total_pcs_points,
                    "total_uci_points": total_uci_points,
                    "pcs_per_star": pcs_per_star,
                    "uci_per_star": uci_per_star,
                    "season_results_count": len(race_results),
                    "consistency_score": consistency_score,
                    "trend_score": trend_score,
                    **demographics,
                }
            )
        else:
            # Default values for riders without PCS data
            rider_data.update(
                {
                    "total_pcs_points": 0,
                    "total_uci_points": 0,
                    "pcs_per_star": 0.0,
                    "uci_per_star": 0.0,
                    "season_results_count": 0,
                    "consistency_score": 0.0,
                    "trend_score": 0.0,
                    "age": None,
                    "nationality": "",
                    "weight_kg": None,
                    "height_m": None,
                }
            )

        riders_data.append(rider_data)

    return pd.DataFrame(riders_data)


def calculate_enhanced_rider_analytics(
    matched_riders: dict[str, RiderMatchInfo], race_data: RaceData, race_key: str
) -> pd.DataFrame:
    """
    Calculate enhanced analytics using race stage data.

    Args:
        matched_riders: Dict mapping fantasy names to match information
        race_data: Complete race data with stages
        race_key: Race identifier

    Returns:
        DataFrame with enhanced rider analytics
    """
    # Start with basic metrics
    riders_df = calculate_basic_rider_metrics(matched_riders)

    # Add enhanced analytics columns
    enhanced_columns = {
        "stage_analytics_available": False,
        "avg_stage_position": None,
        "median_stage_position": None,
        "best_stage_position": None,
        "worst_stage_position": None,
        "stage_wins": 0,
        "top_5_finishes": 0,
        "top_10_finishes": 0,
        "gc_current_rank": None,
        "gc_best_rank": None,
        "points_current_rank": None,
        "points_best_rank": None,
        "kom_current_rank": None,
        "kom_best_rank": None,
        "youth_current_rank": None,
        "youth_best_rank": None,
        "rider_type": None,
        "data_completeness_score": 0.0,
    }

    for col, default_val in enhanced_columns.items():
        riders_df[col] = default_val

    # Calculate enhanced analytics for each rider
    for idx, row in riders_df.iterrows():
        fantasy_name = row["fantasy_name"]

        if fantasy_name not in matched_riders:
            continue

        match_info = matched_riders[fantasy_name]
        race_match = match_info.get("race_match")

        if not race_match or race_match.match_confidence < 0.8:
            continue

        # Calculate race-specific analytics
        try:
            race_analytics = calculate_race_specific_analytics(
                match_info["fantasy_rider"], race_data, race_key
            )

            # Update DataFrame with enhanced metrics
            riders_df.at[idx, "stage_analytics_available"] = race_analytics.get(
                "has_stage_data", False
            )
            riders_df.at[idx, "data_completeness_score"] = race_analytics.get(
                "data_completeness_score", 0.0
            )

            # Stage performance
            riders_df.at[idx, "avg_stage_position"] = race_analytics.get("avg_stage_position")
            riders_df.at[idx, "median_stage_position"] = race_analytics.get(
                "median_stage_position"
            )
            riders_df.at[idx, "best_stage_position"] = race_analytics.get("best_stage_position")
            riders_df.at[idx, "worst_stage_position"] = race_analytics.get("worst_stage_position")
            riders_df.at[idx, "stage_wins"] = race_analytics.get("stage_wins", 0)
            riders_df.at[idx, "top_5_finishes"] = race_analytics.get("top_5_stage_finishes", 0)
            riders_df.at[idx, "top_10_finishes"] = race_analytics.get("top_10_stage_finishes", 0)

            # GC analytics
            gc_analytics = race_analytics.get("gc_analytics")
            if gc_analytics:
                riders_df.at[idx, "gc_current_rank"] = gc_analytics.get("current_rank")
                riders_df.at[idx, "gc_best_rank"] = gc_analytics.get("best_rank")

            # Points analytics
            points_analytics = race_analytics.get("points_analytics")
            if points_analytics:
                riders_df.at[idx, "points_current_rank"] = points_analytics.get("current_rank")
                riders_df.at[idx, "points_best_rank"] = points_analytics.get("best_rank")

            # KOM analytics
            kom_analytics = race_analytics.get("kom_analytics")
            if kom_analytics:
                riders_df.at[idx, "kom_current_rank"] = kom_analytics.get("current_rank")
                riders_df.at[idx, "kom_best_rank"] = kom_analytics.get("best_rank")

            # Youth analytics
            youth_analytics = race_analytics.get("youth_analytics")

            if youth_analytics:
                riders_df.at[idx, "youth_current_rank"] = youth_analytics.get("current_rank")
                riders_df.at[idx, "youth_best_rank"] = youth_analytics.get("best_rank")

            # Rider classification
            riders_df.at[idx, "rider_type"] = race_analytics.get("rider_type_classification")

            # Override basic points with more accurate stage-based totals
            stage_pcs_points = race_analytics.get("total_stage_pcs_points", 0)
            stage_uci_points = race_analytics.get("total_stage_uci_points", 0)

            riders_df.at[idx, "total_pcs_points"] = stage_pcs_points
            riders_df.at[idx, "total_uci_points"] = stage_uci_points

            # Recalculate per-star ratios
            stars = row["stars"]
            if stars > 0:
                riders_df.at[idx, "pcs_per_star"] = stage_pcs_points / stars
                riders_df.at[idx, "uci_per_star"] = stage_uci_points / stars

        except Exception as e:
            print(f"Warning: Enhanced analytics failed for {fantasy_name}: {e}")

    return riders_df


# =============================================================================
# Race Analytics
# =============================================================================


def calculate_race_computed_properties(race_data: RaceData) -> ComputedRaceInfo:
    """
    Calculate computed properties for race data.

    Args:
        race_data: Raw race data

    Returns:
        ComputedRaceInfo with calculated properties
    """
    stages = race_data.get("stages", [])

    # Calculate stage statistics
    stage_stats = _calculate_stage_stats(stages)

    # Calculate climb statistics
    climb_stats = _calculate_climb_stats(stages)

    # Build computed info
    computed_info: ComputedRaceInfo = {}

    # Distance information
    if stage_stats.get("total_distance") is not None:
        computed_info["total_distance"] = f"{stage_stats['total_distance']:.1f} km"

    if stage_stats.get("completed_distance") is not None:
        computed_info["total_distance_completed"] = f"{stage_stats['completed_distance']:.1f} km"

    if stage_stats.get("incomplete_distance") is not None:
        computed_info["total_distance_incomplete"] = f"{stage_stats['incomplete_distance']:.1f} km"

    # Stage completion
    computed_info["stages_completed"] = stage_stats.get("completed_count")
    computed_info["stages_incomplete"] = stage_stats.get("incomplete_count")

    # Stage analysis
    computed_info["shortest_stage"] = stage_stats.get("shortest_stage")
    computed_info["longest_stage"] = stage_stats.get("longest_stage")

    if stage_stats.get("avg_distance") is not None:
        computed_info["avg_stage_distance"] = round(stage_stats["avg_distance"], 1)

    if stage_stats.get("avg_vertical_meters") is not None:
        computed_info["avg_stage_vertical_meters"] = round(stage_stats["avg_vertical_meters"], 1)

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

    return computed_info


def calculate_race_analytics_summary(race_data: RaceData, race_key: str) -> RaceAnalyticsSummary:
    """Calculate summary analytics for the entire race."""
    stages = race_data.get("stages", [])
    completed_stages = [stage for stage in stages if stage.get("results")]

    # Calculate stage statistics
    total_distance = 0.0
    stage_types = {}
    total_riders = set()

    for stage in completed_stages:
        # Count stage types
        profile = stage.get("profile_icon", "unknown")
        stage_types[profile] = stage_types.get(profile, 0) + 1

        # Collect all riders
        results = stage.get("results", [])
        for result in results:
            rider_name = result.get("rider_name")
            if rider_name:
                total_riders.add(rider_name)

        # Sum distance (if available and numeric)
        distance_str = stage.get("distance", "")
        if distance_str:
            try:
                # Extract numeric part (e.g., "150.5 km" -> 150.5)
                distance_num = float(distance_str.split()[0])
                total_distance += distance_num
            except (ValueError, IndexError):
                pass

    # Get current leaders
    current_leaders = {}
    if completed_stages:
        last_stage = completed_stages[-1]

        classifications = [
            "general_classification",
            "points_classification",
            "kom_classification",
            "youth_classification",
        ]
        classification_names = ["gc", "points", "kom", "youth"]

        for class_key, class_name in zip(classifications, classification_names, strict=False):
            classification_data = last_stage.get(class_key, [])
            if classification_data:
                leader = classification_data[0]
                current_leaders[class_name] = {
                    "rider_name": leader.get("rider_name"),
                    "team_name": leader.get("team_name"),
                    "nationality": leader.get("nationality"),
                }

    return RaceAnalyticsSummary(
        race_key=race_key,
        total_stages=len(stages),
        completed_stages=len(completed_stages),
        total_riders=len(total_riders),
        active_riders=len(total_riders),  # Simplified - would need DNF tracking
        total_distance_completed=total_distance if total_distance > 0 else None,
        stage_types_distribution=stage_types,
        current_leaders=current_leaders,
        avg_field_size_per_stage=len(total_riders) if completed_stages else None,
    )


# =============================================================================
# Advanced Analytics (from combined_rider_analytics.py)
# =============================================================================


def calculate_race_specific_analytics(
    rider: dict[str, Any], race_data: RaceData, race_key: str
) -> RiderRaceAnalytics:
    """
    Calculate comprehensive race-specific analytics by combining rider data
    with race stage results.

    This is a simplified version that focuses on the most important metrics.
    """
    from data.matching import normalize_rider_name

    # Get rider's canonical name for matching
    canonical_name = rider.get("fantasy_name", "")
    if rider.get("pcs_data"):
        canonical_name = rider["pcs_data"].get("name", canonical_name)

    # Get completed stages
    stages = race_data.get("stages", [])
    completed_stages = [stage for stage in stages if stage.get("results")]

    # Extract stage performances (simplified)
    stage_results = []
    stage_ranks = []

    for i, stage in enumerate(completed_stages, 1):
        stage_results_data = stage.get("results", [])

        # Find rider in stage results
        rider_result = None
        for result in stage_results_data:
            if normalize_rider_name(result.get("rider_name", "")) == normalize_rider_name(
                canonical_name
            ):
                rider_result = result
                break

        if rider_result:
            rank = rider_result.get("rank")
            if rank:
                stage_ranks.append(rank)

                stage_perf = StagePerformance(
                    stage_number=i,
                    stage_rank=rank,
                    stage_pcs_points=rider_result.get("pcs_points", 0),
                    stage_uci_points=rider_result.get("uci_points", 0),
                )
                stage_results.append(stage_perf)

    # Calculate basic statistics
    avg_stage_position = statistics.mean(stage_ranks) if stage_ranks else None
    median_stage_position = statistics.median(stage_ranks) if stage_ranks else None
    best_stage_position = min(stage_ranks) if stage_ranks else None
    worst_stage_position = max(stage_ranks) if stage_ranks else None

    top_10_finishes = sum(1 for rank in stage_ranks if rank <= 10)
    top_5_finishes = sum(1 for rank in stage_ranks if rank <= 5)
    stage_wins = sum(1 for rank in stage_ranks if rank == 1)

    # Calculate point totals
    total_stage_pcs = sum(p.get("stage_pcs_points", 0) for p in stage_results)
    total_stage_uci = sum(p.get("stage_uci_points", 0) for p in stage_results)

    # Data completeness
    has_pcs_data = bool(rider.get("pcs_data"))
    has_stage_data = bool(stage_results)
    completeness = 0.0
    if has_pcs_data:
        completeness += 0.3
    if has_stage_data:
        completeness += 0.7

    return RiderRaceAnalytics(
        # Identification
        rider_name=canonical_name,
        normalized_rider_name=normalize_rider_name(canonical_name),
        fantasy_name=rider.get("fantasy_name"),
        team_name=rider.get("team"),
        # Data tracking
        has_pcs_data=has_pcs_data,
        has_stage_data=has_stage_data,
        data_completeness_score=completeness,
        # Stage performance
        stage_results=stage_results,
        completed_stages=len(stage_results),
        total_stages=len(stages),
        # Aggregated statistics
        avg_stage_position=avg_stage_position,
        median_stage_position=median_stage_position,
        best_stage_position=best_stage_position,
        worst_stage_position=worst_stage_position,
        top_10_stage_finishes=top_10_finishes,
        top_5_stage_finishes=top_5_finishes,
        stage_wins=stage_wins,
        # Points
        total_stage_pcs_points=total_stage_pcs,
        total_stage_uci_points=total_stage_uci,
        total_classification_points={"pcs": total_stage_pcs, "uci": total_stage_uci},
    )


# =============================================================================
# Helper Functions
# =============================================================================


def _calculate_consistency_and_trend(race_results: list[dict[str, Any]]) -> tuple[float, float]:
    """Calculate consistency and trend scores from race results."""
    if len(race_results) < 2:
        return 0.0, 0.0

    # Convert to DataFrame for easier processing
    df = pd.DataFrame(race_results)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # Get numeric GC positions
    positions = pd.to_numeric(df["gc_position"], errors="coerce").dropna()

    if len(positions) < 2:
        return 0.0, 0.0

    # Consistency: coefficient of variation
    consistency_score = positions.std() / positions.mean() if positions.mean() > 0 else 0.0

    # Trend: linear regression slope
    if len(positions) >= 2:
        x_days = (df["date"] - df["date"].min()).dt.days.values[: len(positions)]
        trend_score = np.polyfit(x_days, positions.values, 1)[0]
    else:
        trend_score = 0.0

    return consistency_score, trend_score


def _extract_demographics(pcs_data: dict[str, Any]) -> dict[str, Any]:
    """Extract demographic information from PCS data."""
    demographics = {}

    # Calculate age from birthdate
    if pcs_data.get("birthdate"):
        try:
            datetime_birthday = datetime.strptime(pcs_data["birthdate"], "%Y-%m-%d")
            demographics["age"] = datetime.now().year - datetime_birthday.year
            demographics["birthdate"] = datetime_birthday.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Add other demographic info
    demographics["nationality"] = pcs_data.get("nationality", "")
    demographics["birthplace"] = pcs_data.get("birthplace", "")

    # Convert weight and height
    if pcs_data.get("weight"):
        demographics["weight_kg"] = pcs_data["weight"]
        demographics["weight_lbs"] = pcs_data["weight"] * 2.20462

    if pcs_data.get("height"):
        demographics["height_m"] = pcs_data["height"]
        demographics["height_ft"] = pcs_data["height"] * 3.28084

    return demographics


def _is_stage_completed(stage: StageData) -> bool:
    """Check if a stage has been completed based on available data."""
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


def _calculate_stage_stats(stages: list[StageData]) -> dict[str, Any]:
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
            try:
                # Extract numeric part (e.g., "150.5 km" -> 150.5)
                distance_str = str(stage.get("distance", ""))
                distance_num = float(distance_str.split()[0])
                distances.append(distance_num)
            except (ValueError, IndexError):
                pass

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
            (stage, float(str(stage.get("distance", "0")).split()[0]))
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
            sum(float(str(stage.get("distance", "0")).split()[0]) for stage in completed_stages)
            if completed_stages
            else None
        ),
        "incomplete_distance": (
            sum(float(str(stage.get("distance", "0")).split()[0]) for stage in incomplete_stages)
            if incomplete_stages
            else None
        ),
    }


def _calculate_climb_stats(stages: list[StageData]) -> dict[str, Any]:
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
