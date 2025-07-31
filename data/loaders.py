"""
High-level data loading functions that combine fetching, processing, and caching.

This module provides the main public API for loading data in the application.
"""

import logging
import time
from collections.abc import Callable

import pandas as pd

from config.settings import SUPPORTED_RACES
from data.models.race import RaceData
from data.processors.matching import match_rider_names
from data.processors.race_analytics import prepare_race_data
from data.processors.rider_analytics import calculate_rider_metrics
from data.sources.fantasy import load_fantasy_json
from data.sources.pcs_api import (
    fetch_rider_pcs_data,
    fetch_startlist_data,
    load_pcs_cache,
    save_pcs_cache,
)
from data.sources.race_api import fetch_race_data, load_race_cache, save_race_cache
from utils.url_patterns import startlist_path


def load_fantasy_data() -> pd.DataFrame:
    """
    Load the riders fantasy data into a pandas dataframe and merge with
    cached PCS data
    """
    # Load basic fantasy data
    riders = load_fantasy_json()

    # TODO: Get info for the selected race (remove hardcoded)
    race_info = SUPPORTED_RACES["TDF_FEMMES_2025"]
    race_info["startlist_cache_path"]
    startlist_cache_key = startlist_path(race_info["url_path"])

    # Load cached PCS data
    cached_rider_data = load_pcs_cache()

    # Load startlist cache
    from data.sources.pcs_api import load_startlist_cache

    cached_startlist_data = load_startlist_cache("TDF_FEMMES_2025")

    # Get startlist for race (if available)
    startlist_riders = []
    if cached_startlist_data and startlist_cache_key in cached_startlist_data:
        startlist_riders = cached_startlist_data[startlist_cache_key]["startlist"]

    # Create the name mappings
    rider_mappings = match_rider_names(riders, startlist_riders)

    matched_pcs_rider_count = 0

    # Process each rider to add cached PCS data if available
    for rider in riders:
        full_name = rider.get("full_name", "")

        # Initialize PCS data fields
        rider["pcs_data"] = None
        rider["pcs_matched_name"] = None
        rider["pcs_rider_url"] = None

        # Try to find matching rider in startlist
        matched_startlist_rider = None
        if full_name in rider_mappings:
            matched_pcs_rider_count += 1
            matched_startlist_rider = rider_mappings[full_name]
            # Save the matched startlist data
            rider["matched_startlist_rider"] = matched_startlist_rider.get(
                "matched_startlist_rider", {}
            )
            rider["pcs_matched_name"] = matched_startlist_rider.get("pcs_matched_name", "")
            rider["pcs_rider_url"] = matched_startlist_rider.get("pcs_rider_url", "")
            # Check if the cached PCS data exists for this rider
            if matched_startlist_rider.get("pcs_rider_url") in cached_rider_data:
                rider["pcs_data"] = cached_rider_data[matched_startlist_rider["pcs_rider_url"]]

    # Log matching results
    if matched_pcs_rider_count > 0:
        logging.info(f"✅ Matched {matched_pcs_rider_count} riders")
    else:
        logging.warning("❌ No riders matched")

    riders_df = pd.DataFrame(riders)

    # Process the rider's data
    riders_df = calculate_rider_metrics(riders_df)

    return riders_df


def fetch_pcs_data(
    race_name: str, 
    riders_df: pd.DataFrame, 
    progress_callback: Callable[[float, str], None] | None = None
) -> pd.DataFrame:
    """
    Fetch ProCyclingStats data for each rider.
    First fetches the Tour de France 2025 startlist to get rider URLs,
    then matches fantasy riders with PCS riders and fetches their data.
    Uses caching to avoid repeat API calls.
    Returns updated dataframe with PCS data.
    """
    # Load existing caches
    cached_rider_data = load_pcs_cache()

    # Step 1: Get Tour de France 2025 startlist
    logging.info("📋 Loading Tour de France 2025 startlist...")
    startlist_riders = fetch_startlist_data(race_name)
    # Convert dataframe to list of dictionaries for processing
    riders_list = riders_df.to_dict("records")

    # Create the name mappings
    rider_mappings = match_rider_names(riders_df, startlist_riders)

    updated_riders = []
    new_cache_data = cached_rider_data.copy()

    # Track progress
    total_riders = len(riders_list)

    # Step 2: Match fantasy riders with PCS riders and fetch data
    for i, rider in enumerate(riders_list):
        full_name = rider.get("full_name", "")

        # Update progress
        progress = (i + 1) / total_riders
        current_status = f"🔄 Processing rider {i + 1}/{total_riders}: {full_name}"
        logging.info(current_status)
        if progress_callback:
            progress_callback(progress, current_status)

        rider_url = None
        # Try to find matching rider in startlist
        matched_pcs_rider = None
        if full_name in rider_mappings:
            matched_pcs_rider = rider_mappings[full_name]

            rider_url = matched_pcs_rider.get("pcs_rider_url", None)
            logging.info(f"✅ Matched {full_name} with {matched_pcs_rider['pcs_matched_name']}")

        # Check if we have cached data for this rider URL
        if rider_url in cached_rider_data and matched_pcs_rider:
            logging.info(f"Using cached data for {full_name}")
            rider["pcs_data"] = cached_rider_data[rider_url]
            rider["pcs_matched_name"] = matched_pcs_rider["pcs_matched_name"]
            rider["pcs_rider_url"] = rider_url
        elif rider_url and matched_pcs_rider:
            # Fetch fresh data from ProCyclingStats
            pcs_data = fetch_rider_pcs_data(rider_url, full_name)

            # Add the PCS data to the rider
            rider["pcs_data"] = pcs_data
            rider["pcs_matched_name"] = matched_pcs_rider.get("pcs_matched_name", "")
            rider["pcs_rider_url"] = rider_url

            # Update cache with rider URL as key
            new_cache_data[rider_url] = pcs_data

        updated_riders.append(rider)
        time.sleep(0.5)

    # Save updated cache
    if new_cache_data != cached_rider_data:
        save_pcs_cache(new_cache_data)

    # Log completion
    logging.info(f"Completed processing {total_riders} riders")

    # Convert back to dataframe
    return pd.DataFrame(updated_riders)


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
            "fetched_at": "",
            "race_data": {},
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

        # For development, always re-compute computed properties
        updated_race_data = prepare_race_data(cached_race_data)
        return updated_race_data

    # Fetch fresh data if not in cache
    race_result = fetch_race_data(race_key)

    # Calculate computed properties
    race_result = prepare_race_data(race_result)

    # Update cache with fetched data
    new_cache_data = cached_data.copy()
    new_cache_data[race_info_key] = race_result
    save_race_cache(new_cache_data)

    return race_result
