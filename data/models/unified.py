"""
Unified data models for the simplified data pipeline.

This module defines clear data structures for each stage of the pipeline:
1. Raw data (as loaded from sources)
2. Matched data (after rider matching)
3. Analytics data (after calculations)

These models provide type safety and clear contracts between pipeline stages.
"""

from typing import Any, TypedDict

import pandas as pd

from .combined_analytics import RiderMatchingResult, RiderRaceAnalytics
from .race import RaceData

# =============================================================================
# Raw Data Models
# =============================================================================


class RawDataSources(TypedDict, total=False):
    """Container for all raw data sources."""

    fantasy_riders: list[dict[str, Any]]
    startlist_riders: list[dict[str, Any]]
    pcs_cache: dict[str, Any]  # URL -> PCS data
    race_data: RaceData


# =============================================================================
# Matched Data Models
# =============================================================================


class RiderMatchInfo(TypedDict, total=False):
    """Complete matching information for a single rider."""

    fantasy_rider: dict[str, Any]  # Original fantasy rider data
    startlist_match: dict[str, Any] | None  # Matched startlist data
    race_match: RiderMatchingResult  # Race matching result
    has_pcs_data: bool
    has_race_data: bool
    canonical_name: str  # Best name to use for this rider


class MatchedDataSet(TypedDict, total=False):
    """Container for all matched data."""

    riders: dict[str, RiderMatchInfo]  # fantasy_name -> match info
    race_data: RaceData  # Race data (unchanged from raw)
    match_summary: dict[str, Any]  # Summary statistics about matching


# =============================================================================
# Analytics Data Models
# =============================================================================


class RiderAnalyticsData(TypedDict, total=False):
    """Complete analytics for a single rider."""

    # Basic information
    fantasy_name: str
    canonical_name: str
    match_info: RiderMatchInfo

    # Basic metrics (always available)
    basic_metrics: dict[str, Any]

    # Enhanced analytics (only if race data available)
    race_analytics: RiderRaceAnalytics | None

    # Computed flags
    has_enhanced_analytics: bool
    data_quality_score: float  # 0.0 to 1.0


class AnalyticsDataSet(TypedDict, total=False):
    """Container for all analytics data."""

    # Individual rider analytics
    riders: dict[str, RiderAnalyticsData]  # fantasy_name -> analytics

    # Aggregated DataFrames for easy consumption
    basic_metrics_df: pd.DataFrame
    enhanced_metrics_df: pd.DataFrame | None

    # Race-level analytics
    race_summary: dict[str, Any]
    computed_race_info: dict[str, Any]

    # Pipeline metadata
    pipeline_info: dict[str, Any]


# =============================================================================
# Pipeline State Models
# =============================================================================


class PipelineStage(TypedDict, total=False):
    """Metadata about a pipeline stage."""

    stage_name: str
    start_time: str
    end_time: str | None
    success: bool
    error_message: str | None
    items_processed: int
    items_succeeded: int


class PipelineState(TypedDict, total=False):
    """Complete state of the data pipeline."""

    # Configuration
    race_key: str
    use_enhanced_analytics: bool
    fuzzy_threshold: float

    # Stage tracking
    pipeline_stages: list[PipelineStage]
    current_stage: str | None
    overall_success: bool

    # Data at each stage
    raw_data: RawDataSources | None
    matched_data: MatchedDataSet | None
    analytics_data: AnalyticsDataSet | None

    # Summary metrics
    total_fantasy_riders: int
    matched_riders_count: int
    enhanced_analytics_count: int
    data_quality_distribution: dict[str, int]


# =============================================================================
# Result Models for Public API
# =============================================================================


class DataLoadResult(TypedDict, total=False):
    """Result of loading data through the pipeline."""

    # Main result
    riders_df: pd.DataFrame  # Final DataFrame for UI consumption

    # Additional data for advanced use cases
    pipeline_state: PipelineState
    raw_data: RawDataSources
    matched_data: MatchedDataSet
    analytics_data: AnalyticsDataSet

    # Summary information
    summary: dict[str, Any]
    warnings: list[str]
    errors: list[str]


class AnalyticsResult(TypedDict, total=False):
    """Result of analytics calculations."""

    # DataFrames
    basic_df: pd.DataFrame
    enhanced_df: pd.DataFrame | None

    # Individual rider analytics
    rider_analytics: dict[str, RiderAnalyticsData]

    # Race analytics
    race_summary: dict[str, Any]

    # Metadata
    analytics_info: dict[str, Any]


# =============================================================================
# Configuration Models
# =============================================================================


class PipelineConfig(TypedDict, total=False):
    """Configuration for the data pipeline."""

    # Data sources
    race_key: str
    use_cache: bool
    force_refresh: bool

    # Matching configuration
    fuzzy_threshold: float
    require_team_match: bool

    # Analytics configuration
    use_enhanced_analytics: bool
    calculate_trends: bool
    include_comparisons: bool

    # Performance options
    parallel_processing: bool
    batch_size: int
    api_delay: float

    # Output options
    include_debug_info: bool
    verbose_logging: bool


# =============================================================================
# Error Models
# =============================================================================


class DataError(TypedDict, total=False):
    """Structured error information."""

    error_type: str  # "loading", "matching", "analytics", "validation"
    error_code: str
    message: str
    details: dict[str, Any]
    stage: str
    affected_items: list[str]
    severity: str  # "warning", "error", "critical"


class ValidationResult(TypedDict, total=False):
    """Result of data validation."""

    is_valid: bool
    errors: list[DataError]
    warnings: list[DataError]
    summary: dict[str, Any]
