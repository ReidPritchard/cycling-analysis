"""
Pure data loading functions that only fetch and cache raw data.

This module provides clean separation between data loading and data processing.
No analytics or matching logic is performed here - only raw data retrieval.
"""

import logging
from typing import Any

from config.settings import SUPPORTED_RACES
from data.models.race import RaceData
from data.models.unified import RawDataSources
from data.sources.fantasy import load_fantasy_json
from data.sources.pcs_api import (
    fetch_rider_pcs_data,
    fetch_startlist_data,
    load_pcs_cache,
    load_startlist_cache,
    save_pcs_cache,
)
from data.sources.race_api import fetch_race_data, load_race_cache, save_race_cache


def load_raw_fantasy_data() -> list[dict[str, Any]]:
    """
    Load raw fantasy data from JSON file.

    Returns:
        List of raw fantasy rider dictionaries
    """
    return load_fantasy_json()


def load_raw_pcs_cache() -> dict[str, Any]:
    """
    Load cached PCS rider data.

    Returns:
        Dict mapping rider URLs to cached PCS data
    """
    return load_pcs_cache()


def load_raw_startlist_data(race_key: str) -> list[dict[str, Any]]:
    """
    Load race startlist data from cache or API.

    Args:
        race_key: Race identifier from SUPPORTED_RACES

    Returns:
        List of startlist rider dictionaries
    """
    if race_key not in SUPPORTED_RACES:
        logging.error(f"❌ Unsupported race key: {race_key}")
        return []

    # Check cache first
    cached_data = load_startlist_cache(race_key)
    race_info = SUPPORTED_RACES[race_key]

    # Use utils.url_patterns to get the correct key
    from utils.url_patterns import startlist_path

    startlist_key = startlist_path(race_info["url_path"])

    if cached_data and startlist_key in cached_data:
        logging.info(f"📋 Using cached startlist data for {race_key}")
        return cached_data[startlist_key]["startlist"]

    # Fetch fresh data if not in cache
    return fetch_startlist_data(race_key)


def load_raw_race_data(race_key: str) -> RaceData:
    """
    Load raw race data (stages, climbs, etc.) from cache or API.

    Args:
        race_key: Race identifier from SUPPORTED_RACES

    Returns:
        Raw RaceData without computed properties
    """
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
        return cached_data[race_info_key]

    # Fetch fresh data if not in cache
    race_result = fetch_race_data(race_key)

    # Update cache with fetched data (no processing here)
    new_cache_data = cached_data.copy()
    new_cache_data[race_info_key] = race_result
    save_race_cache(new_cache_data)

    return race_result


def fetch_missing_pcs_data(
    rider_urls: list[str], existing_cache: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Fetch PCS data for riders not in cache.

    Args:
        rider_urls: List of PCS rider URLs to fetch
        existing_cache: Existing cache to check against

    Returns:
        Dict mapping rider URLs to PCS data (new fetches only)
    """
    if existing_cache is None:
        existing_cache = load_pcs_cache()

    new_data = {}

    for rider_url in rider_urls:
        if rider_url not in existing_cache:
            # Extract rider name from URL for logging
            rider_name = rider_url.split("/")[-1].replace("-", " ").title()
            pcs_data = fetch_rider_pcs_data(rider_url, rider_name)
            new_data[rider_url] = pcs_data

            # Small delay to avoid overwhelming the API
            import time

            time.sleep(0.5)

    # Update cache if we fetched new data
    if new_data:
        updated_cache = existing_cache.copy()
        updated_cache.update(new_data)
        save_pcs_cache(updated_cache)

    return new_data


def get_all_raw_data(race_key: str) -> RawDataSources:
    """
    Load all raw data sources for a race.

    Args:
        race_key: Race identifier from SUPPORTED_RACES

    Returns:
        Dict containing all raw data sources
    """
    return {
        "fantasy_riders": load_raw_fantasy_data(),
        "startlist_riders": load_raw_startlist_data(race_key),
        "pcs_cache": load_raw_pcs_cache(),
        "race_data": load_raw_race_data(race_key),
    }
