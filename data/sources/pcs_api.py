"""
ProCyclingStats API data fetching.
"""

import logging
from datetime import datetime

from procyclingstats import RaceStartlist, Rider

from config.settings import PCS_CACHE_FILE, SUPPORTED_RACES
from utils.cache_manager import load_cache, refresh_cache, save_cache
from utils.url_patterns import startlist_path


def load_pcs_cache():
    """Load PCS data from cache file if it exists and is not expired."""
    return load_cache(PCS_CACHE_FILE, "riders_data")


def save_pcs_cache(riders_data):
    """Save PCS data to cache file with timestamp."""
    save_cache(PCS_CACHE_FILE, riders_data, "riders_data")


def refresh_pcs_cache():
    """Force refresh of PCS cache by deleting the cache file."""
    refresh_cache(PCS_CACHE_FILE, "PCS")


def load_startlist_cache(race_name="TDF_FEMMES_2025"):
    """Load PCS startlist from cache file if it exists and is not expired."""
    if race_name not in SUPPORTED_RACES:
        # Throw error?
        return
    cache_path = SUPPORTED_RACES[race_name]["startlist_cache_path"]
    return load_cache(cache_path, "startlist_data")


def save_startlist_cache(race_name, startlist_data):
    """Save PCS startlist to cache file with timestamp."""
    if race_name not in SUPPORTED_RACES:
        # Throw error?
        return
    cache_path = SUPPORTED_RACES[race_name]["startlist_cache_path"]
    save_cache(cache_path, startlist_data, "startlist_data")


def refresh_startlist_cache(race_name="TDF_FEMMES_2025"):
    """Force refresh of PCS startlist cache by deleting the cache file."""
    if race_name not in SUPPORTED_RACES:
        # Throw error?
        return
    cache_path = SUPPORTED_RACES[race_name]["startlist_cache_path"]
    refresh_cache(cache_path, "Race Startlist")


def fetch_startlist_data(race_name="TDF_FEMMES_2025"):
    """Fetch the startlist data for a race."""
    cached_startlist_data = load_startlist_cache(race_name)
    base_url = SUPPORTED_RACES[race_name]["url_path"]

    startlist_key = startlist_path(base_url)

    if cached_startlist_data and startlist_key in cached_startlist_data:
        logging.info("Using cached startlist data")
        startlist_riders = cached_startlist_data[startlist_key]["startlist"]
    else:
        try:
            logging.info("🌐 Fetching fresh startlist data...")
            startlist = RaceStartlist(startlist_key)
            startlist_data = startlist.parse()
            startlist_riders = startlist_data["startlist"]

            # Cache the startlist
            new_startlist_cache = cached_startlist_data or {}
            new_startlist_cache[startlist_key] = {
                "startlist": startlist_riders,
                "fetched_at": datetime.now().isoformat(),
            }
            save_startlist_cache(race_name, new_startlist_cache)

        except Exception as e:
            logging.error(f"❌ Error fetching startlist: {e}")
            return []

    # return the startlist riders
    return startlist_riders


def fetch_rider_pcs_data(rider_url, rider_name):
    """
    Fetch PCS data for a single rider.

    Args:
        rider_url: PCS URL for the rider
        rider_name: Display name for logging

    Returns:
        dict: PCS data for the rider, or error dict if fetch fails
    """
    try:
        logging.info(f"🌐 Fetching fresh data for {rider_name}")
        rider_pcs = Rider(rider_url)
        return rider_pcs.parse(IndexError, True)
    except Exception as e:
        # FIXME: This is catching an "index out of range" error
        # I'm not sure why exactly, but it's happening a lot
        logging.error(f"❌ Error fetching data for {rider_name} ({rider_url}): {e}")
        return {
            "error": str(e),
            "fetched_at": datetime.now().isoformat(),
        }
