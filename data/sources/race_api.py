"""
Race data fetching from ProCyclingStats API.
"""

import logging
from datetime import datetime
from typing import Any

from procyclingstats import Race, RaceClimbs, Stage

from config.settings import RACE_CACHE_FILE, SUPPORTED_RACES
from data.models.race import RaceData, StageData
from utils.cache_manager import load_cache, refresh_cache, save_cache
from utils.url_patterns import race_climbs_path


def load_race_cache() -> dict[str, Any]:
    """Load race data from cache file if it exists and is not expired."""
    return load_cache(RACE_CACHE_FILE, "race_data")


def save_race_cache(race_data: dict[str, Any]) -> None:
    """Save race data to cache file with timestamp."""
    save_cache(RACE_CACHE_FILE, race_data, "race_data")


def refresh_race_cache() -> None:
    """Force refresh of race cache by deleting the cache file."""
    refresh_cache(RACE_CACHE_FILE, "Race")


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
        stage_data["avg_speed_winner"] = _safe_stage_attribute(
            stage_obj, "avg_speed_winner", default=None
        )
        stage_data["results"] = _safe_stage_attribute(
            stage_obj, "results", default=None
        )
        stage_data["general_classification"] = _safe_stage_attribute(
            stage_obj, "gc", default=None
        )
        stage_data["points_classification"] = _safe_stage_attribute(
            stage_obj, "points", default=None
        )
        stage_data["kom_classification"] = _safe_stage_attribute(
            stage_obj, "kom", default=None
        )
        stage_data["youth_classification"] = _safe_stage_attribute(
            stage_obj, "youth", default=None
        )
        stage_data["team_classification"] = _safe_stage_attribute(
            stage_obj, "teams", default=None
        )

        return stage_data

    except Exception as e:
        logging.warning(f"Could not fetch stage data for {stage_url}: {e}")
        return {"stage_url": stage_url, "climbs": []}


def fetch_race_data(race_key: str) -> RaceData:
    """
    Fetch race data for the specified race key from PCS API.

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
            "stages": [],
            "climbs": [],
        }

    race_info = SUPPORTED_RACES[race_key]
    race_info_key = race_info["url_path"]

    # Fetch fresh data from PCS API
    try:
        logging.info(f"🌐 Fetching fresh race data for {race_key}...")

        # Create Race object and parse basic race data
        race = Race(race_info_key)
        race_data = race.parse()

        # Initialize race result with basic data
        race_result: RaceData = {
            "race_data": race_data,
            "fetched_at": datetime.now().isoformat(),
            "stages": [],
            "climbs": [],
        }

        # Try to get stages overview and detailed stage data
        try:
            stages_overview = race.stages()

            # Fetch detailed data for each stage
            stages: list[StageData] = []
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

        logging.info(f"✅ Successfully fetched race data for {race_key}")
        return race_result

    except Exception as e:
        logging.error(f"❌ Error fetching race data for {race_key}: {e}")
        return {
            "error": str(e),
            "fetched_at": datetime.now().isoformat(),
            "race_data": {},
            "stages": [],
            "climbs": [],
        }
