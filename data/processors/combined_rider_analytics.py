"""
Combined rider analytics engine.

Combines rider season results with detailed race stage data to provide
comprehensive analytics with stage-by-stage and classification-specific insights.
"""

import statistics

import numpy as np

from ..models.combined_analytics import (
    ClassificationAnalytics,
    RaceAnalyticsSummary,
    RiderRaceAnalytics,
    StagePerformance,
)
from ..models.race import RaceData, StageData
from ..models.rider import RiderData
from .rider_matching import (
    extract_rider_from_classifications,
    match_fantasy_to_race_data,
    normalize_rider_name,
)


def parse_time_to_seconds(time_str: str | None) -> float | None:
    """Parse time string (HH:MM:SS or MM:SS) to seconds."""
    if not time_str or time_str == "0:00:00":
        return 0.0

    try:
        # Handle different time formats
        if time_str.count(":") == 2:  # HH:MM:SS
            hours, minutes, seconds = time_str.split(":")
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        elif time_str.count(":") == 1:  # MM:SS
            minutes, seconds = time_str.split(":")
            return int(minutes) * 60 + int(seconds)
        else:
            return float(time_str)
    except (ValueError, AttributeError):
        return None


def calculate_time_gap(rider_time: str | None, reference_time: str | None) -> float | None:
    """Calculate time gap in seconds between rider and reference time."""
    if not rider_time or not reference_time:
        return None

    rider_seconds = parse_time_to_seconds(rider_time)
    reference_seconds = parse_time_to_seconds(reference_time)

    if rider_seconds is None or reference_seconds is None:
        return None

    return rider_seconds - reference_seconds


def extract_stage_performance(
    rider_name: str,
    stage_data: StageData,
    stage_number: int,
    winner_time: str | None = None,
    leader_time: str | None = None,
) -> StagePerformance | None:
    """
    Extract comprehensive stage performance for a specific rider.

    Args:
        rider_name: Canonical rider name to search for
        stage_data: Complete stage data
        stage_number: Stage number (1-indexed)
        winner_time: Stage winner's time for gap calculation
        leader_time: GC leader's time for gap calculation

    Returns:
        StagePerformance or None if rider not found
    """
    # Get rider data from all classifications
    classifications = extract_rider_from_classifications(rider_name, stage_data)

    if not classifications:
        return None

    # Use stage results as primary source
    stage_result = classifications.get("results", {}).get("data", {})
    gc_result = classifications.get("gc", {}).get("data", {})
    points_result = classifications.get("points", {}).get("data", {})
    kom_result = classifications.get("kom", {}).get("data", {})
    youth_result = classifications.get("youth", {}).get("data", {})

    # Calculate time gaps
    rider_time = stage_result.get("time")
    time_gap_to_winner = calculate_time_gap(rider_time, winner_time) if winner_time else None
    time_gap_to_leader = (
        calculate_time_gap(gc_result.get("time"), leader_time) if leader_time else None
    )

    # Calculate percentile finish
    stage_results = stage_data.get("results", [])
    percentile_finish = None
    if stage_result.get("rank") and stage_results:
        rank = stage_result.get("rank", 0)
        total_finishers = len(stage_results)
        percentile_finish = (total_finishers - rank + 1) / total_finishers * 100

    # Aggregate classification points
    classification_points = {}
    if stage_result.get("pcs_points"):
        classification_points["stage_pcs"] = stage_result.get("pcs_points", 0)
    if stage_result.get("uci_points"):
        classification_points["stage_uci"] = stage_result.get("uci_points", 0)

    return StagePerformance(
        stage_number=stage_number,
        stage_url=stage_data.get("stage_url"),
        date=stage_data.get("date"),
        stage_type=stage_data.get("stage_type"),
        distance=stage_data.get("distance"),
        profile_icon=stage_data.get("profile_icon"),
        # Stage results
        stage_rank=stage_result.get("rank"),
        time=rider_time,
        time_behind_winner=(
            f"{time_gap_to_winner / 60:.0f}:{time_gap_to_winner % 60:02.0f}"
            if time_gap_to_winner
            else None
        ),
        time_behind_leader=(
            f"{time_gap_to_leader / 60:.0f}:{time_gap_to_leader % 60:02.0f}"
            if time_gap_to_leader
            else None
        ),
        bonus_time=stage_result.get("bonus"),
        status=stage_result.get("status"),
        # Classification positions
        gc_rank=gc_result.get("rank"),
        gc_time=gc_result.get("time"),
        points_rank=points_result.get("rank"),
        kom_rank=kom_result.get("rank"),
        youth_rank=youth_result.get("rank"),
        # Points
        stage_pcs_points=stage_result.get("pcs_points", 0),
        stage_uci_points=stage_result.get("uci_points", 0),
        classification_points=classification_points,
        # Performance metrics
        percentile_finish=percentile_finish,
        time_gap_to_winner_seconds=time_gap_to_winner,
        time_gap_to_leader_seconds=time_gap_to_leader,
    )


def calculate_classification_analytics(
    rider_name: str, stages: list[StageData], classification_type: str
) -> ClassificationAnalytics | None:
    """
    Calculate analytics for a specific classification.

    Args:
        rider_name: Canonical rider name
        stages: List of completed stages
        classification_type: 'gc', 'points', 'kom', 'youth', 'team'

    Returns:
        ClassificationAnalytics or None if no data
    """
    ranks = []
    points_earned = 0

    for stage in stages:
        classifications = extract_rider_from_classifications(rider_name, stage)
        classification_data = classifications.get(classification_type, {}).get("data", {})

        if classification_data:
            rank = classification_data.get("rank")
            if rank:
                ranks.append(rank)

            # Add points from this classification
            if classification_type == "points" or classification_type == "kom":
                points_earned += classification_data.get("pcs_points", 0)

    if not ranks:
        return None

    current_rank = ranks[-1] if ranks else None
    best_rank = min(ranks) if ranks else None
    worst_rank = max(ranks) if ranks else None

    # Calculate additional metrics
    stages_in_top_10 = sum(1 for rank in ranks if rank <= 10)
    stages_in_top_5 = sum(1 for rank in ranks if rank <= 5)
    average_rank = statistics.mean(ranks) if ranks else None
    rank_volatility = statistics.stdev(ranks) if len(ranks) > 1 else 0.0

    return ClassificationAnalytics(
        current_rank=current_rank,
        best_rank=best_rank,
        worst_rank=worst_rank,
        stages_in_top_10=stages_in_top_10,
        stages_in_top_5=stages_in_top_5,
        rank_changes=ranks,
        points_earned=points_earned,
        average_rank=average_rank,
        rank_volatility=rank_volatility,
    )


def calculate_trend_metrics(
    stage_performances: list[StagePerformance],
) -> dict[str, float | None]:
    """
    Calculate performance trends across stages.

    Returns:
        Dictionary with trend metrics
    """
    if len(stage_performances) < 2:
        return {
            "stage_position_trend": None,
            "gc_position_trend": None,
            "time_gap_trend": None,
            "consistency_score": None,
            "improvement_score": None,
        }

    # Extract time series data
    stage_positions = [p.get("stage_rank") for p in stage_performances if p.get("stage_rank")]
    gc_positions = [p.get("gc_rank") for p in stage_performances if p.get("gc_rank")]
    time_gaps = [
        p.get("time_gap_to_leader_seconds")
        for p in stage_performances
        if p.get("time_gap_to_leader_seconds")
    ]

    # Calculate linear trends (negative slope = improvement)
    stage_position_trend = None
    if len(stage_positions) >= 2:
        x = list(range(len(stage_positions)))
        stage_position_trend = np.polyfit(x, stage_positions, 1)[0] if stage_positions else None

    gc_position_trend = None
    if len(gc_positions) >= 2:
        x = list(range(len(gc_positions)))
        gc_position_trend = np.polyfit(x, gc_positions, 1)[0] if gc_positions else None

    time_gap_trend = None
    if len(time_gaps) >= 2:
        x = list(range(len(time_gaps)))
        time_gap_trend = np.polyfit(x, time_gaps, 1)[0] if time_gaps else None

    # Consistency score (coefficient of variation)
    consistency_score = None
    if len(stage_positions) >= 2:
        mean_pos = statistics.mean(stage_positions)
        if mean_pos > 0:
            std_pos = statistics.stdev(stage_positions)
            consistency_score = std_pos / mean_pos

    # Improvement score (comparing first half vs second half)
    improvement_score = None
    if len(stage_positions) >= 4:
        half_point = len(stage_positions) // 2
        first_half_avg = statistics.mean(stage_positions[:half_point])
        second_half_avg = statistics.mean(stage_positions[half_point:])
        # Negative score = improvement (lower positions)
        improvement_score = second_half_avg - first_half_avg

    return {
        "stage_position_trend": stage_position_trend,
        "gc_position_trend": gc_position_trend,
        "time_gap_trend": time_gap_trend,
        "consistency_score": consistency_score,
        "improvement_score": improvement_score,
    }


def classify_rider_type(stage_performances: list[StagePerformance]) -> str | None:
    """
    Classify rider type based on stage performance patterns.

    Returns:
        'sprinter', 'climber', 'gc_contender', 'all_rounder', or None
    """
    if not stage_performances:
        return None

    # Analyze performance by stage type
    flat_stages = []
    hilly_stages = []
    mountain_stages = []

    for perf in stage_performances:
        profile = perf.get("profile_icon", "")
        stage_rank = perf.get("stage_rank")

        if not stage_rank:
            continue

        if profile in ["p1"]:  # Flat
            flat_stages.append(stage_rank)
        elif profile in ["p2", "p3"]:  # Hilly
            hilly_stages.append(stage_rank)
        elif profile in ["p4", "p5"]:  # Mountain
            mountain_stages.append(stage_rank)

    # Calculate average positions by terrain
    avg_flat = statistics.mean(flat_stages) if flat_stages else float("inf")
    avg_hilly = statistics.mean(hilly_stages) if hilly_stages else float("inf")
    avg_mountain = statistics.mean(mountain_stages) if mountain_stages else float("inf")

    # Simple classification logic
    if avg_flat <= 10 and avg_flat < avg_mountain and avg_flat < avg_hilly:
        return "sprinter"
    elif avg_mountain <= 10 and avg_mountain < avg_flat and avg_mountain < avg_hilly:
        return "climber"
    elif all(avg <= 15 for avg in [avg_flat, avg_hilly, avg_mountain] if avg != float("inf")):
        return "all_rounder"
    elif min(avg_flat, avg_hilly, avg_mountain) <= 20:
        return "gc_contender"

    return None


def calculate_race_specific_analytics(
    rider: RiderData, race_data: RaceData, race_key: str
) -> RiderRaceAnalytics:
    """
    Calculate comprehensive race-specific analytics by combining rider data with race stage results.

    Args:
        rider: Fantasy rider data including PCS data
        race_data: Complete race data with stages
        race_key: Race identifier

    Returns:
        RiderRaceAnalytics with complete analytics
    """
    # Match rider to race data
    match_result = match_fantasy_to_race_data(rider, race_data)
    canonical_name = match_result.get("canonical_name", rider.get("fantasy_name", ""))

    # Get completed stages
    stages = race_data.get("stages", [])
    completed_stages = [stage for stage in stages if stage.get("results")]

    # Extract stage performances
    stage_results = []
    for i, stage in enumerate(completed_stages, 1):
        # Get winner time for gap calculations
        stage_results_data = stage.get("results", [])
        winner_time = stage_results_data[0].get("time") if stage_results_data else None

        # Get GC leader time
        gc_data = stage.get("general_classification", [])
        leader_time = gc_data[0].get("time") if gc_data else None

        stage_perf = extract_stage_performance(canonical_name, stage, i, winner_time, leader_time)

        if stage_perf:
            stage_results.append(stage_perf)

    # Calculate aggregated statistics
    stage_ranks = [p.get("stage_rank") for p in stage_results if p.get("stage_rank")]

    avg_stage_position = statistics.mean(stage_ranks) if stage_ranks else None
    median_stage_position = statistics.median(stage_ranks) if stage_ranks else None
    best_stage_position = min(stage_ranks) if stage_ranks else None
    worst_stage_position = max(stage_ranks) if stage_ranks else None

    top_10_finishes = sum(1 for rank in stage_ranks if rank <= 10)
    top_5_finishes = sum(1 for rank in stage_ranks if rank <= 5)
    stage_wins = sum(1 for rank in stage_ranks if rank == 1)

    # Calculate classification analytics
    gc_analytics = calculate_classification_analytics(canonical_name, completed_stages, "gc")
    points_analytics = calculate_classification_analytics(
        canonical_name, completed_stages, "points"
    )
    kom_analytics = calculate_classification_analytics(canonical_name, completed_stages, "kom")
    youth_analytics = calculate_classification_analytics(canonical_name, completed_stages, "youth")

    # Calculate point totals
    total_stage_pcs = sum(p.get("stage_pcs_points", 0) for p in stage_results)
    total_stage_uci = sum(p.get("stage_uci_points", 0) for p in stage_results)

    # Calculate trends and performance metrics
    trends = calculate_trend_metrics(stage_results)

    # Determine best classification
    best_classification = None
    best_rank = float("inf")

    for classification, analytics in [
        ("gc", gc_analytics),
        ("points", points_analytics),
        ("kom", kom_analytics),
        ("youth", youth_analytics),
    ]:
        if analytics and analytics.get("best_rank"):
            if analytics["best_rank"] < best_rank:
                best_rank = analytics["best_rank"]
                best_classification = classification

    # Calculate fantasy metrics
    stars = rider.get("stars", 0)
    points_per_star = (total_stage_pcs / stars) if stars > 0 else None

    # Data completeness score
    has_pcs_data = bool(rider.get("pcs_data"))
    has_stage_data = bool(stage_results)
    completeness = 0.0
    if has_pcs_data:
        completeness += 0.3
    if has_stage_data:
        completeness += 0.7

    # Calculate field position percentile
    field_percentiles = [
        p.get("percentile_finish") for p in stage_results if p.get("percentile_finish")
    ]
    field_position_percentile = statistics.mean(field_percentiles) if field_percentiles else None

    return RiderRaceAnalytics(
        # Identification
        rider_name=canonical_name,
        normalized_rider_name=normalize_rider_name(canonical_name),
        fantasy_name=rider.get("fantasy_name"),
        rider_url=match_result.get("rider_url"),
        rider_number=match_result.get("rider_number"),
        team_name=match_result.get("team_name"),
        age=match_result.get("age"),
        nationality=match_result.get("nationality"),
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
        # Classifications
        gc_analytics=gc_analytics,
        points_analytics=points_analytics,
        kom_analytics=kom_analytics,
        youth_analytics=youth_analytics,
        # Points
        total_stage_pcs_points=total_stage_pcs,
        total_stage_uci_points=total_stage_uci,
        total_classification_points={"pcs": total_stage_pcs, "uci": total_stage_uci},
        # Trends and analysis
        stage_position_trend=trends.get("stage_position_trend"),
        gc_position_trend=trends.get("gc_position_trend"),
        time_gap_trend=trends.get("time_gap_trend"),
        consistency_score=trends.get("consistency_score"),
        improvement_score=trends.get("improvement_score"),
        # Comparative analytics
        field_position_percentile=field_position_percentile,
        best_classification=best_classification,
        rider_type_classification=classify_rider_type(stage_results),
        # Fantasy metrics
        points_per_star=points_per_star,
        value_efficiency=points_per_star,  # Simple efficiency metric
    )


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
