"""
Race data fetching and caching for Tour de France Femmes.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from procyclingstats import Race, RaceClimbs, Stage

from config.settings import RACE_CACHE_FILE, SUPPORTED_RACES
from utils.cache_manager import load_cache, refresh_cache, save_cache
from utils.url_patterns import race_climbs_path

# Type definitions


class StageData(TypedDict, total=False):
    """Type definition for stage data structure."""

    stage_url: str
    distance: Optional[str]
    profile_icon: Optional[str]
    stage_type: Optional[str]
    vertical_meters: Optional[int]
    avg_temperature: Optional[float]
    date: Optional[str]
    departure: Optional[str]
    arrival: Optional[str]
    won_how: Optional[str]
    race_startlist_quality_score: Optional[float]
    profile_score: Optional[float]
    pcs_points_scale: Optional[str]
    uci_points_scale: Optional[str]
    avg_speed_winner: Optional[float]
    start_time: Optional[str]
    climbs: List[Dict[str, Any]]
    results: Optional[List[Dict[str, Any]]]


class ComputedRaceInfo(TypedDict, total=False):
    """Type definition for computed properties of a race."""

    # FIXME: Add more computed properties based on
    # what information provides insights for the user

    total_distance: Optional[str]
    total_distance_completed: Optional[str]
    total_distance_incomplete: Optional[str]
    total_vertical_meters: Optional[int]

    stages_completed: Optional[int]
    stages_incomplete: Optional[int]
    shortest_stage: Optional[Dict[str, Any]]
    longest_stage: Optional[Dict[str, Any]]
    avg_stage_distance: Optional[float]
    avg_stage_vertical_meters: Optional[float]
    # most_common_win_type:

    climbs_completed: Optional[int]
    climbs_incomplete: Optional[int]


class RaceData(TypedDict, total=False):
    """Type definition for race data structure."""

    race_data: Dict[str, Any]
    computed_race_info: Optional[ComputedRaceInfo]
    stages_overview: List[Dict[str, Any]]
    stages: List[StageData]
    climbs: List[Dict[str, Any]]
    fetched_at: str
    error: Optional[str]


def load_race_cache() -> Dict[str, Any]:
    """Load race data from cache file if it exists and is not expired."""
    return load_cache(RACE_CACHE_FILE, "race_data")


def save_race_cache(race_data: Dict[str, Any]) -> None:
    """Save race data to cache file with timestamp."""
    save_cache(RACE_CACHE_FILE, race_data, "race_data")


def refresh_race_cache() -> None:
    """Force refresh of race cache by deleting the cache file."""
    refresh_cache(RACE_CACHE_FILE, "Race")


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
    except:
        # Check for alternative completion indicators
        is_completed = (
            stage.get("results") is not None
            or stage.get("avg_speed_winner") is not None
            or stage.get("won_how") is not None
        )

    return is_completed


def _calculate_stage_stats(stages: List[StageData]) -> Dict[str, Any]:
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
        "avg_vertical_meters": sum(vertical_meters) / len(vertical_meters)
        if vertical_meters
        else None,
        "shortest_stage": shortest_stage,
        "longest_stage": longest_stage,
        "completed_count": len(completed_stages),
        "incomplete_count": len(incomplete_stages),
        "completed_distance": sum(
            stage.get("distance", 0.0) for stage in completed_stages
        )
        if completed_stages
        else None,
        "incomplete_distance": sum(
            stage.get("distance", 0.0) for stage in incomplete_stages
        )
        if incomplete_stages
        else None,
    }


def _calculate_climb_stats(stages: List[StageData]) -> Dict[str, Any]:
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
    stage_stats = _calculate_stage_stats(stages)

    # Calculate climb statistics
    climb_stats = _calculate_climb_stats(stages)

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


def _safe_stage_attribute(stage_obj: Stage, attribute: str, default: Any = None) -> Any:
    """Safely fetch a stage attribute, returning default value if it fails."""
    try:
        attribute = getattr(stage_obj, attribute)()
        if attribute is None or attribute == "-":
            return default
        return attribute
    except Exception as e:
        logging.debug(f"Could not fetch {attribute} for stage: {e}")
        return default


def _fetch_stage_data(stage_url: str) -> StageData:
    """
    Safely fetch comprehensive stage data with error handling.

    Args:
        stage_url: The URL path for the stage

    Returns:
        StageData dictionary with all available stage information
    """
    if not stage_url or not isinstance(stage_url, str):
        logging.warning(f"Invalid stage URL: {stage_url}")
        return {"stage_url": stage_url or "", "climbs": []}

    try:
        stage_obj = Stage(stage_url)

        # Build stage data with safe attribute fetching
        stage_data: StageData = {
            "stage_url": stage_url,
            "distance": _safe_stage_attribute(stage_obj, "distance"),
            "profile_icon": _safe_stage_attribute(stage_obj, "profile_icon"),
            "stage_type": _safe_stage_attribute(stage_obj, "stage_type"),
            "vertical_meters": _safe_stage_attribute(stage_obj, "vertical_meters"),
            "avg_temperature": _safe_stage_attribute(stage_obj, "avg_temperature"),
            "date": _safe_stage_attribute(stage_obj, "date"),
            "departure": _safe_stage_attribute(stage_obj, "departure"),
            "arrival": _safe_stage_attribute(stage_obj, "arrival"),
            "won_how": _safe_stage_attribute(stage_obj, "won_how"),
            "race_startlist_quality_score": _safe_stage_attribute(
                stage_obj, "race_startlist_quality_score"
            ),
            "profile_score": _safe_stage_attribute(stage_obj, "profile_score"),
            "pcs_points_scale": _safe_stage_attribute(stage_obj, "pcs_points_scale"),
            "uci_points_scale": _safe_stage_attribute(stage_obj, "uci_points_scale"),
            "start_time": _safe_stage_attribute(stage_obj, "start_time"),
            "climbs": _safe_stage_attribute(stage_obj, "climbs", []),
        }

        # These attributes may not be available for future/incomplete stages
        # Only fetch them if the stage has been completed
        stage_data["avg_speed_winner"] = _safe_stage_attribute(
            stage_obj, "avg_speed_winner", default=None
        )

        stage_data["results"] = _safe_stage_attribute(
            stage_obj, "results", default=None
        )

        return stage_data

    except Exception as e:
        logging.warning(f"Could not fetch stage data for {stage_url}: {e}")
        return {"stage_url": stage_url, "climbs": []}


def load_race_data(race_key: str) -> RaceData:
    """
    Load race data for the specified race key from cache or fetch fresh data.

    Handles both completed and incomplete stage data gracefully, with comprehensive
    error handling for data that may not be available yet.

    Args:
        race_key: The race key from SUPPORTED_RACES

    Returns:
        RaceData dictionary with race information, stages, climbs, etc.
    """
    # Check if race_key is supported
    if race_key not in SUPPORTED_RACES:
        logging.error(f"❌ Unsupported race key: {race_key}")
        return {
            "error": f"Unsupported race key: {race_key}",
            "fetched_at": datetime.now().isoformat(),
            "race_data": {},
            "stages_overview": [],
            "stages": [],
            "climbs": [],
        }

    # Load cached race data
    cached_data = load_race_cache()
    race_info = SUPPORTED_RACES[race_key]
    race_info_key = race_info["url_path"]

    # Return cached data if available
    if race_info_key in cached_data:
        logging.info(f"📋 Using cached race data for {race_key}")
        cached_race_data = cached_data[race_info_key]

        # # Ensure cached data has computed properties
        # if "computed_race_info" not in cached_race_data:
        #     cached_race_data = prepare_race_data(cached_race_data)
        # For development, always re-compute computed properties
        updated_race_data = prepare_race_data(cached_race_data)

        return updated_race_data

    # Fetch fresh data if not in cache
    try:
        logging.info(f"🌐 Fetching fresh race data for {race_key}...")

        # Create Race object and parse basic race data
        race = Race(race_info_key)
        race_data = race.parse()

        # Initialize race result with basic data
        race_result: RaceData = {
            "race_data": race_data,
            "fetched_at": datetime.now().isoformat(),
            "stages_overview": [],
            "stages": [],
            "climbs": [],
        }

        # Try to get stages overview and detailed stage data
        try:
            stages_overview = race.stages()
            race_result["stages_overview"] = stages_overview

            # Fetch detailed data for each stage
            stages: List[StageData] = []
            for stage_overview in stages_overview:
                stage_url = stage_overview.get("stage_url", "")
                if stage_url:
                    stage_data = _fetch_stage_data(stage_url)
                    stages.append(stage_data)
                else:
                    logging.warning(
                        f"Stage overview missing stage_url: {stage_overview}"
                    )

            race_result["stages"] = stages

        except Exception as e:
            logging.warning(f"Could not fetch stages data: {e}")
            race_result["stages_overview"] = []
            race_result["stages"] = []
            if "stages" not in race_result["race_data"]:
                race_result["race_data"]["stages"] = []

        # Try to get race climbs data
        try:
            race_climbs = RaceClimbs(race_climbs_path(race_info_key))
            race_result["climbs"] = race_climbs.climbs()
        except Exception as e:
            logging.warning(f"Could not fetch climbs data: {e}")
            race_result["climbs"] = []

        # Calculate computed properties
        race_result = prepare_race_data(race_result)

        # Update cache with fetched data
        new_cache_data = cached_data.copy()
        new_cache_data[race_info_key] = race_result
        save_race_cache(new_cache_data)

        logging.info(f"✅ Successfully fetched race data for {race_key}")
        return race_result

    except Exception as e:
        logging.error(f"❌ Error fetching race data for {race_key}: {e}")
        return {
            "error": str(e),
            "fetched_at": datetime.now().isoformat(),
            "race_data": {},
            "stages_overview": [],
            "stages": [],
            "climbs": [],
        }
