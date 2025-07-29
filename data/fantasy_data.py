"""
Fantasy data loading and processing.
"""

from datetime import datetime
import json
import pandas as pd
import streamlit as st
from difflib import SequenceMatcher as SM

from config.settings import (
    PCS_CACHE_FILE,
    SUPPORTED_RACES,
)
from utils.cache_manager import load_cache
from utils.url_patterns import startlist_path
from utils.name_utils import match_rider_names


# =============================================================================
# DATA PROCESSING FUNCTIONS
# =============================================================================


def process_season_results(pcs_data):
    """Process and clean season results from PCS data."""
    if not pcs_data or "season_results" not in pcs_data:
        return pd.DataFrame(), 0, 0

    season_results = pcs_data.get("season_results", [])

    if not season_results:
        return pd.DataFrame(), 0, 0

    # Convert to DataFrame and process
    df_results = pd.DataFrame(season_results)

    # Make date a datetime object
    df_results["date"] = pd.to_datetime(df_results["date"])

    # Filter for Tour de France Femmes 2025 only
    df_results = df_results[
        df_results["stage_url"].str.startswith("race/tour-de-france-femmes/2025/")
    ]

    # Sort by date (most recent first) and limit to 5 results
    df_results = df_results.sort_values(by="date", ascending=False).head(5)

    # Calculate totals
    total_pcs_points = (
        int(df_results["pcs_points"].sum()) if not df_results.empty else 0
    )
    total_uci_points = (
        int(df_results["uci_points"].sum()) if not df_results.empty else 0
    )

    # Clean up for display
    if not df_results.empty:
        df_results = df_results.drop(columns=["stage_url", "distance"])
        df_results.columns = [
            "Name",
            "Date",
            "Result",
            "GC Position",
            "PCS Points",
            "UCI Points",
        ]

    return df_results, total_pcs_points, total_uci_points


def calculate_rider_demographics(pcs_data):
    """Calculate demographic information from PCS data."""
    demographics = {}

    if not pcs_data or "error" in pcs_data:
        return demographics

    # Calculate age from birthdate
    if pcs_data.get("birthdate"):
        try:
            datetime_birthday = datetime.strptime(pcs_data["birthdate"], "%Y-%m-%d")
            demographics["age"] = datetime.now().year - datetime_birthday.year
            demographics["birthdate"] = datetime_birthday.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Add other demographic info
    demographics["nationality"] = pcs_data.get("nationality", "")
    demographics["birthplace"] = pcs_data.get("birthplace", "")

    # Convert weight and height
    if pcs_data.get("weight"):
        demographics["weight_kg"] = pcs_data["weight"]
        demographics["weight_lbs"] = pcs_data["weight"] * 2.20462

    if pcs_data.get("height"):
        demographics["height_m"] = pcs_data["height"]
        demographics["height_ft"] = pcs_data["height"] * 3.28084

    return demographics


def calculate_rider_metrics(df):
    """Add calculated fields to the rider dataframe."""
    df = df.copy()

    # Initialize calculated columns
    df["total_pcs_points"] = 0
    df["total_uci_points"] = 0
    df["pcs_per_star"] = 0.0
    df["uci_per_star"] = 0.0
    df["age"] = None
    df["nationality"] = ""
    df["season_results_count"] = 0
    df["season_results"] = None

    # Process each rider
    for idx, row in df.iterrows():
        pcs_data = row.get("pcs_data", {})

        # Process season results
        season_results, total_pcs, total_uci = process_season_results(pcs_data)
        df.at[idx, "total_pcs_points"] = total_pcs
        df.at[idx, "total_uci_points"] = total_uci
        if season_results is not None:
            df.at[idx, "season_results"] = season_results

        # Calculate per-star ratios
        stars = row["stars"]
        if stars > 0:
            df.at[idx, "pcs_per_star"] = total_pcs / stars
            df.at[idx, "uci_per_star"] = total_uci / stars

        # Add demographics
        demographics = calculate_rider_demographics(pcs_data)
        for key, value in demographics.items():
            if key in df.columns:
                df.at[idx, key] = value

        # Count season results
        if pcs_data and "season_results" in pcs_data:
            df.at[idx, "season_results_count"] = len(pcs_data["season_results"])

    return df


def prepare_rider_data(df):
    """Main data preparation function."""
    return calculate_rider_metrics(df)


def load_fantasy_data():
    """
        Load the riders fantasy data into a pandas dataframe and merge with
        cached PCS data
    """
    # Load basic fantasy data
    with open("fantasy-data.json", "r") as f:
        riders = json.load(f)


    race_info = SUPPORTED_RACES["TDF_FEMMES_2025"]
    startlist_cache_path = race_info["startlist_cache_path"]
    startlist_cache_key = startlist_path(race_info["url_path"])

    # Load cached PCS data
    cached_rider_data = load_cache(PCS_CACHE_FILE, "riders_data")
    cached_startlist_data = load_cache(
        startlist_cache_path, "startlist_data"
    )

    # Get startlist for matching if available
    startlist_riders = []
    if startlist_cache_key in cached_startlist_data:
        startlist_riders = cached_startlist_data[startlist_cache_key][
            "startlist"
        ]

    # Log a little bit about the cached data
    st.write(f"Cached PCS data: {len(cached_rider_data)} riders")
    st.write(f"Cached startlist data: {len(startlist_riders)} riders")

    # Create the name mappings
    rider_mappings = match_rider_names(
        riders, startlist_riders
    )

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
            rider["matched_startlist_rider"] = matched_startlist_rider.get("matched_startlist_rider", {})
            rider["pcs_matched_name"] = matched_startlist_rider.get("pcs_matched_name", "")
            rider["pcs_rider_url"] = matched_startlist_rider.get("pcs_rider_url", "")
            # Check if the cached PCS data exists for this rider
            if matched_startlist_rider.get("pcs_rider_url") in cached_rider_data:
                rider["pcs_data"] = cached_rider_data[matched_startlist_rider["pcs_rider_url"]]

    # If we were able to match any riders, render a toast
    if matched_pcs_rider_count > 0:
        st.toast(f"✅ Matched {matched_pcs_rider_count} riders")
    else:
        st.toast("❌ No riders matched")

    riders_df = pd.DataFrame(riders)

    # Process the rider's data
    riders_df = prepare_rider_data(riders_df)

    return riders_df
