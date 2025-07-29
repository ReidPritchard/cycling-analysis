"""
Race data fetching and caching for Tour de France Femmes.
"""

import streamlit as st
from datetime import datetime
from procyclingstats import Race, RaceClimbs, Stage

from config.settings import RACE_CACHE_FILE, TDF_FEMMES_2025_PATH
from utils.cache_manager import load_cache, save_cache, refresh_cache


def load_race_cache():
    """Load race data from cache file if it exists and is not expired."""
    return load_cache(RACE_CACHE_FILE, "race_data")


def save_race_cache(race_data):
    """Save race data to cache file with timestamp."""
    save_cache(RACE_CACHE_FILE, race_data, "race_data")


def refresh_race_cache():
    """Force refresh of race cache by deleting the cache file."""
    refresh_cache(RACE_CACHE_FILE, "Race")


@st.cache_data
def fetch_tdf_femmes_2025_data():
    """
    Fetch Tour de France Femmes 2025 race data.
    Returns comprehensive race data including overall classifications and stage results.
    """
    # Check cache first
    cached_data = load_race_cache()

    if TDF_FEMMES_2025_PATH in cached_data:
        st.toast("📋 Using cached Tour de France Femmes 2025 data")
        return cached_data[TDF_FEMMES_2025_PATH]

    try:
        st.toast("🌐 Fetching fresh Tour de France Femmes 2025 data...")

        # Create Race object
        race = Race(TDF_FEMMES_2025_PATH)

        # Parse race data
        race_data = race.parse()

        # Get additional data if available
        race_info = {"race_data": race_data, "fetched_at": datetime.now().isoformat()}

        # Try to get stages data
        try:
            stages = race.stages()
            race_info["stages"] = stages
        except Exception as e:
            st.toast(f"Could not fetch stages data: {e}")
            race_info["stages"] = []

        # Try to get race climbs
        try:
            climbs = RaceClimbs(f"{TDF_FEMMES_2025_PATH}/route/climbs")
            race_info["climbs"] = climbs
            # Add the climbs to each stage
            stages_climbs = {}
            for stage_info in stages:
                stage = Stage(stage_info["stage_url"])
                stage_climbs = [climbs[s["climb_url"]] for s in stage.climbs()]
                stages_climbs[stage_info["stage_url"]] = stage_climbs
            race_info["stages_climbs"] = stages_climbs
        except Exception as e:
            st.toast(f"Could not fetch climbs data: {e}")
            race_info["climbs"] = []

        # Update cache
        new_cache_data = cached_data.copy()
        new_cache_data[TDF_FEMMES_2025_PATH] = race_info
        save_race_cache(new_cache_data)

        return race_info

    except Exception as e:
        st.error(f"❌ Error fetching Tour de France Femmes 2025 data: {e}")
        return {
            "error": str(e),
            "fetched_at": datetime.now().isoformat(),
            "race_data": {},
            "stages": [],
            "climbs": [],
            "stages_climbs": {},
        }


def get_stage_results(stage_number):
    """
    Get results for a specific stage of TdF Femmes 2025.

    Args:
        stage_number (int): The stage number to fetch results for

    Returns:
        dict: Stage results data
    """
    try:
        race = Race(TDF_FEMMES_2025_PATH)
        stage_results = race.stage_results(stage_number)
        return stage_results
    except Exception as e:
        st.error(f"❌ Error fetching stage {stage_number} results: {e}")
        return {}
