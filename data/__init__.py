"""
Data package for Fantasy Cycling Stats.

This package provides a simplified, organized interface for loading and processing
fantasy cycling data with clear separation of concerns:

## Architecture:
- **loaders**: Pure data loading functions (no processing)
- **matching**: Unified rider matching across all data sources
- **analytics**: Pure analytics calculations (no loading)
- **pipeline**: Orchestrated data flow (load -> match -> analyze)
- **models**: Type definitions and data structures
- **sources**: External data fetching (fantasy JSON, PCS API, race API)

## Main public functions:
- **load_fantasy_data()**: Legacy compatibility - runs full pipeline and returns DataFrame
- **run_pipeline()**: New main interface - runs complete pipeline with full control
- **get_all_raw_data()**: Load raw data from all sources
- **match_all_data_sources()**: Match riders across data sources
- **calculate_enhanced_rider_analytics()**: Calculate analytics from matched data

## Migration guide:
- Old: `load_fantasy_data(race_key, use_enhanced_analytics=True)`
- New: `run_pipeline(race_key)["riders_df"]` (same result, better control)
"""

# =============================================================================
# Main Pipeline Interface (Recommended)
# =============================================================================

# Analytics calculations
from .analytics import (
    calculate_basic_rider_metrics,
    calculate_enhanced_rider_analytics,
    calculate_race_analytics_summary,
    calculate_race_computed_properties,
    calculate_race_specific_analytics,
)

# =============================================================================
# Individual Components (Advanced Usage)
# =============================================================================
# Raw data loading
from .loaders import (
    fetch_missing_pcs_data,
    get_all_raw_data,
    load_raw_fantasy_data,
    load_raw_pcs_cache,
    load_raw_race_data,
    load_raw_startlist_data,
)

# Rider matching
from .matching import (
    calculate_name_similarity,
    create_rider_matcher,
    match_all_data_sources,
    normalize_rider_name,
)

# =============================================================================
# Type Definitions
# =============================================================================
# Core models
from .models import ComputedRaceInfo, RaceData, RiderData, StageData

# Advanced analytics models
from .models.combined_analytics import (
    RaceAnalyticsSummary,
    RiderMatchingResult,
    RiderRaceAnalytics,
    StagePerformance,
)

# Unified pipeline models
from .models.unified import (
    AnalyticsDataSet,
    DataLoadResult,
    MatchedDataSet,
    PipelineConfig,
    PipelineState,
    RawDataSources,
)
from .pipeline import (
    create_default_config,
    get_pipeline_summary,
    run_pipeline,  # New main interface
)
from .sources.pcs_api import fetch_rider_pcs_data as fetch_pcs_data

# =============================================================================
# Cache Management
# =============================================================================
from .sources.pcs_api import refresh_pcs_cache, refresh_startlist_cache
from .sources.race_api import refresh_race_cache

# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # =============================================================================
    # MAIN INTERFACE (Recommended for new code)
    # =============================================================================
    # Pipeline functions
    "run_pipeline",  # Main interface - full pipeline control
    "create_default_config",  # Create pipeline configuration
    "get_pipeline_summary",  # Preview pipeline behavior
    # =============================================================================
    # INDIVIDUAL COMPONENTS (Advanced usage)
    # =============================================================================
    # Raw data loading
    "get_all_raw_data",  # Load all raw data sources
    "load_raw_fantasy_data",  # Load fantasy JSON
    "load_raw_pcs_cache",  # Load PCS cache
    "load_raw_startlist_data",  # Load race startlist
    "load_raw_race_data",  # Load race data
    "fetch_missing_pcs_data",  # Fetch missing PCS data
    # Rider matching
    "match_all_data_sources",  # Match riders across all sources
    "create_rider_matcher",  # Create matcher instance
    "normalize_rider_name",  # Normalize names for matching
    "calculate_name_similarity",  # Calculate name similarity
    # Analytics
    "calculate_basic_rider_metrics",  # Basic rider analytics
    "calculate_enhanced_rider_analytics",  # Enhanced rider analytics
    "calculate_race_computed_properties",  # Race computed properties
    "calculate_race_analytics_summary",  # Race summary analytics
    "calculate_race_specific_analytics",  # Individual rider race analytics
    # =============================================================================
    # TYPE DEFINITIONS
    # =============================================================================
    # Core models
    "RiderData",
    "StageData",
    "RaceData",
    "ComputedRaceInfo",
    # Pipeline models
    "DataLoadResult",
    "PipelineConfig",
    "PipelineState",
    "RawDataSources",
    "MatchedDataSet",
    "AnalyticsDataSet",
    # Analytics models
    "RiderRaceAnalytics",
    "RaceAnalyticsSummary",
    "RiderMatchingResult",
    "StagePerformance",
    # =============================================================================
    # UTILITIES
    # =============================================================================
    # Cache management
    "refresh_pcs_cache",
    "refresh_startlist_cache",
    "refresh_race_cache",
]
