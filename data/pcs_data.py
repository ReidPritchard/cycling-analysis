"""
ProCyclingStats data fetching and caching.
"""

from datetime import datetime
from difflib import SequenceMatcher as SM
import time

import pandas as pd
from procyclingstats import RaceStartlist, Rider
import streamlit as st

from config.settings import (
    PCS_CACHE_FILE,
    SUPPORTED_RACES,
)
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
    """ Fetch the startlist data for a race."""
    cached_startlist_data = load_startlist_cache(race_name)
    base_url = SUPPORTED_RACES[race_name]["url_path"]

    startlist_key = startlist_path(base_url)

    if cached_startlist_data and startlist_key in cached_startlist_data:
        st.toast("Using cached startlist data")
        startlist_riders = cached_startlist_data[startlist_key][
            "startlist"
        ]
    else:
        try:
            st.toast("🌐 Fetching fresh startlist data...")
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
            st.error(f"❌ Error fetching startlist: {e}")
            return []

    # return the startlist riders
    return startlist_riders


@st.cache_data
def fetch_pcs_data(riders_df):
    """
    Fetch ProCyclingStats data for each rider.
    First fetches the Tour de France 2022 startlist to get rider URLs,
    then matches fantasy riders with PCS riders and fetches their data.
    Uses caching to avoid repeat API calls.
    Returns updated dataframe with PCS data.
    """
    # Load existing caches
    cached_rider_data = load_pcs_cache()

    # Step 1: Get Tour de France 2025 startlist
    st.toast("📋 Loading Tour de France 2025 startlist...")
    # Convert dataframe to list of dictionaries for processing
    riders_list = riders_df.to_dict("records")
    updated_riders = []
    new_cache_data = cached_rider_data.copy()

    # Track progress
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Step 2: Match fantasy riders with PCS riders and fetch data
    for i, rider in enumerate(riders_list):
        full_name = rider.get("full_name", "")

        # Update progress
        progress = (i + 1) / len(riders_list)
        progress_bar.progress(progress)
        status_text.text(f"🔄 Processing rider {i+1}/{len(riders_list)}: {full_name}")

        # Try to find matching rider in startlist
        matched_pcs_rider = None
        for pcs_rider in startlist_riders:
            pcs_name = pcs_rider["rider_name"]
            rider_url = pcs_rider["rider_url"]

            # Use fuzzy matching to find the best match
            similarity = SM(None, full_name, pcs_name).ratio()
            if similarity > 0.9:  # Adjust threshold as needed
                matched_pcs_rider = pcs_rider
                break

        if not matched_pcs_rider:
            # If no match found, add empty PCS data
            st.toast(f"⚠️ No PCS match found for {full_name}")
            rider["pcs_data"] = {
                "error": "No matching rider found in TdF Femmes 2025 startlist",
                "fetched_at": datetime.now().isoformat(),
            }
            updated_riders.append(rider)
            continue

        rider_url = matched_pcs_rider["rider_url"]
        st.toast(f"✅ Matched {full_name} with {matched_pcs_rider['rider_name']}")

        # Check if we have cached data for this rider URL
        if rider_url in cached_rider_data:
            st.toast(f"Using cached data for {full_name}")
            rider["pcs_data"] = cached_rider_data[rider_url]
            rider["pcs_matched_name"] = matched_pcs_rider["rider_name"]
            rider["pcs_rider_url"] = rider_url
        else:
            # Fetch fresh data from ProCyclingStats
            try:
                st.toast(f"🌐 Fetching fresh data for {full_name}")
                rider_pcs = Rider(rider_url)
                pcs_data = rider_pcs.parse()

                # Add the PCS data to the rider
                rider["pcs_data"] = pcs_data
                rider["pcs_matched_name"] = matched_pcs_rider["rider_name"]
                rider["pcs_rider_url"] = rider_url

                # Update cache with rider URL as key
                new_cache_data[rider_url] = pcs_data

            except Exception as e:
                # FIXME: This is catching an "index out of range" error
                # I'm not sure why exactly, but it's happening a lot
                st.toast(
                    f"❌ Error fetching data for {matched_pcs_rider['rider_name']}: {e}"
                )
                # Add empty PCS data to avoid breaking the dataframe
                rider["pcs_data"] = {
                    "error": str(e),
                    "fetched_at": datetime.now().isoformat(),
                }
                rider["pcs_matched_name"] = matched_pcs_rider["rider_name"]
                rider["pcs_rider_url"] = rider_url

        updated_riders.append(rider)
        time.sleep(0.5)

    # Save updated cache
    if new_cache_data != cached_rider_data:
        save_pcs_cache(new_cache_data)

    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()

    # Convert back to dataframe
    return pd.DataFrame(updated_riders)
