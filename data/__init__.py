"""
Data package for Fantasy Cycling Stats.

This package provides a clean, organized interface for loading and processing
fantasy cycling data, ProCyclingStats data, and race information.

The package is organized into:
- models: Type definitions and data structures
- sources: External data fetching (fantasy JSON, PCS API, race API)
- processors: Data transformation and analytics
- loaders: High-level public API functions

Main public functions:
- load_fantasy_data(): Load fantasy riders with PCS data
- fetch_pcs_data(): Fetch fresh PCS data for riders
- load_race_data(): Load race data with computed analytics
"""

# Import main public API functions
from .loaders import load_fantasy_data, fetch_pcs_data, load_race_data

# Import type definitions for external use
from .models import RiderData, StageData, RaceData, ComputedRaceInfo

# Cache management functions for UI
from .sources.pcs_api import refresh_pcs_cache, refresh_startlist_cache
from .sources.race_api import refresh_race_cache

__all__ = [
    # Main loaders
    "load_fantasy_data",
    "fetch_pcs_data",
    "load_race_data",
    # Type definitions
    "RiderData",
    "StageData",
    "RaceData",
    "ComputedRaceInfo",
    # Cache management
    "refresh_pcs_cache",
    "refresh_startlist_cache",
    "refresh_race_cache",
]
