"""
Combined rider and race analytics data models.

These models support combining rider season results with detailed race stage data
to provide more accurate and nuanced performance analytics.
"""

from typing import Any, TypedDict


class ClassificationAnalytics(TypedDict, total=False):
    """Analytics for a specific classification (GC, Points, KOM, etc.)."""

    current_rank: int | None
    best_rank: int | None
    worst_rank: int | None
    stages_in_top_10: int
    stages_in_top_5: int
    rank_changes: list[int]  # Track rank progression stage by stage
    points_earned: int
    average_rank: float
    rank_volatility: float  # Standard deviation of ranks


class StagePerformance(TypedDict, total=False):
    """Individual stage performance data."""

    stage_number: int
    stage_url: str | None
    date: str | None
    stage_type: str | None
    distance: str | None
    profile_icon: str | None

    # Stage results
    stage_rank: int | None
    time: str | None
    time_behind_winner: str | None
    time_behind_leader: str | None
    bonus_time: str | None
    status: str | None  # DF (finished), DNF, etc.

    # Classification positions after this stage
    gc_rank: int | None
    gc_time: str | None
    points_rank: int | None
    kom_rank: int | None
    youth_rank: int | None

    # Points earned on this stage
    stage_pcs_points: int
    stage_uci_points: int
    classification_points: dict[str, int]  # Points earned in each classification

    # Performance metrics
    percentile_finish: float | None  # Percentile position in field
    time_gap_to_winner_seconds: float | None
    time_gap_to_leader_seconds: float | None


class RiderRaceAnalytics(TypedDict, total=False):
    """Combined analytics for a rider's performance in a specific race."""

    # Rider identification and matching
    rider_name: str
    normalized_rider_name: str  # For matching
    fantasy_name: str | None
    rider_url: str | None
    rider_number: int | None
    team_name: str | None
    age: int | None
    nationality: str | None

    # Data source tracking
    has_pcs_data: bool
    has_stage_data: bool
    data_completeness_score: float  # 0.0 to 1.0

    # Stage-by-stage performance
    stage_results: list[StagePerformance]
    completed_stages: int
    total_stages: int

    # Aggregated stage statistics
    avg_stage_position: float | None
    median_stage_position: float | None
    best_stage_position: int | None
    worst_stage_position: int | None
    top_10_stage_finishes: int
    top_5_stage_finishes: int
    stage_wins: int

    # Classification performance
    gc_analytics: ClassificationAnalytics | None
    points_analytics: ClassificationAnalytics | None
    kom_analytics: ClassificationAnalytics | None
    youth_analytics: ClassificationAnalytics | None

    # Point totals (stage-by-stage aggregation)
    total_stage_pcs_points: int
    total_stage_uci_points: int
    total_classification_points: dict[str, int]

    # Performance trends and consistency
    stage_position_trend: float | None  # Linear trend of stage positions
    gc_position_trend: float | None  # Linear trend of GC positions
    time_gap_trend: float | None  # Trend of time gap to leader
    consistency_score: float | None  # Coefficient of variation
    improvement_score: float | None  # How much rider improved over race

    # Comparative analytics
    field_position_percentile: float | None  # Average percentile in field
    best_classification: str | None  # Classification where rider performs best
    rider_type_classification: str | None  # Sprinter, Climber, GC, All-rounder

    # Fantasy-specific metrics
    points_per_star: float | None
    value_efficiency: float | None  # Performance relative to fantasy cost


class RaceAnalyticsSummary(TypedDict, total=False):
    """Summary analytics for the entire race."""

    race_key: str
    total_stages: int
    completed_stages: int
    total_riders: int
    active_riders: int  # Still in race

    # Stage statistics
    avg_stage_distance: float | None
    total_distance_completed: float | None
    stage_types_distribution: dict[str, int]

    # Classification leaders
    current_leaders: dict[str, dict[str, Any]]  # Current leader in each classification

    # Field analytics
    avg_field_size_per_stage: float | None
    dropout_rate: float | None
    competitive_balance: float | None  # How spread out the field is


class RiderMatchingResult(TypedDict, total=False):
    """Result of matching a rider across data sources."""

    fantasy_name: str | None
    pcs_name: str | None
    stage_name: str | None
    rider_url: str | None

    match_confidence: float  # 0.0 to 1.0
    match_method: str  # "exact", "fuzzy", "manual"
    ambiguous_matches: list[str]  # Other possible matches

    # Unified rider data
    canonical_name: str
    team_name: str | None
    rider_number: int | None
    nationality: str | None
    age: int | None
