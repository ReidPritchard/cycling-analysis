"""
Fantasy data loading and processing.
"""

import json
import logging
from datetime import datetime
from typing import Any, TypedDict

import numpy as np
import pandas as pd

from config.settings import (
    FANTASY_DATA_FILE,
    PCS_CACHE_FILE,
    SUPPORTED_RACES,
)
from utils.cache_manager import load_cache
from utils.name_utils import match_rider_names
from utils.url_patterns import startlist_path

# =============================================================================
# Types
# =============================================================================


class RiderData(TypedDict):
    """TypedDict for rider data structure."""

    full_name: str
    fantasy_name: str
    team: str
    stars: int
    pcs_data: dict[str, Any] | None
    pcs_matched_name: str | None
    pcs_rider_url: str | None
    matched_startlist_rider: dict[str, Any] | None


# =============================================================================
# DATA PROCESSING FUNCTIONS
# =============================================================================


def process_season_results(pcs_data):
    """Process and clean season results from PCS data."""
    if not pcs_data or "season_results" not in pcs_data:
        return pd.DataFrame(), 0, 0, 0.0, 0.0

    season_results = pcs_data.get("season_results", [])

    if not season_results:
        return pd.DataFrame(), 0, 0, 0.0, 0.0

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

    # Calculate consistency and trend metrics
    consistency_score = 0.0
    trend_score = 0.0

    if not df_results.empty and len(df_results) >= 2:
        # Consistency: coefficient of variation of results (lower is more consistent)
        results_positions = pd.to_numeric(
            df_results["gc_position"], errors="coerce"
        ).dropna()
        if len(results_positions) >= 2:
            consistency_score = (
                results_positions.std() / results_positions.mean()
                if results_positions.mean() > 0
                else 0
            )

        # Trend: linear regression slope of results over time (negative = improving)
        if len(results_positions) >= 2:
            # Sort by date ascending for trend calculation
            df_trend = df_results.copy()
            df_trend["result_numeric"] = pd.to_numeric(
                df_trend["gc_position"], errors="coerce"
            )
            df_trend = df_trend.dropna(subset=["result_numeric"]).sort_values("date")

            if len(df_trend) >= 2:
                x_days = (df_trend["date"] - df_trend["date"].min()).dt.days.values
                y_results = df_trend["result_numeric"].values
                trend_score = np.polyfit(x_days, y_results, 1)[0]  # slope

    # Clean up for display
    if not df_results.empty:
        # Only drop columns that exist
        columns_to_drop = ["stage_url", "distance"]
        df_results = df_results.drop(columns=columns_to_drop)

        df_results.columns = [
            "Name",
            "Date",
            "Result",
            "GC Position",
            "PCS Points",
            "UCI Points",
        ]

    return (
        df_results,
        total_pcs_points,
        total_uci_points,
        consistency_score,
        trend_score,
    )


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
    df["consistency_score"] = 0.0
    df["trend_score"] = 0.0

    # Process each rider
    for idx, row in df.iterrows():
        pcs_data = row.get("pcs_data", {})

        # Process season results
        season_results, total_pcs, total_uci, consistency, trend = (
            process_season_results(pcs_data)
        )
        df.at[idx, "total_pcs_points"] = total_pcs
        df.at[idx, "total_uci_points"] = total_uci
        df.at[idx, "consistency_score"] = consistency
        df.at[idx, "trend_score"] = trend
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


# @st.cache_data(show_spinner=True, ttl=60 * 60 * 24, max_entries=10)
def load_fantasy_data():
    """
    Load the riders fantasy data into a pandas dataframe and merge with
    cached PCS data
    """
    # Load basic fantasy data
    with open(FANTASY_DATA_FILE) as f:
        riders = json.load(f)

    # TODO: Get info for the selected race (remove hardcoded)
    race_info = SUPPORTED_RACES["TDF_FEMMES_2025"]
    startlist_cache_path = race_info["startlist_cache_path"]
    startlist_cache_key = startlist_path(race_info["url_path"])

    # Load cached PCS data
    cached_rider_data = load_cache(PCS_CACHE_FILE, "riders_data")
    cached_startlist_data = load_cache(startlist_cache_path, "startlist_data")

    # Get startlist for race (if available)
    startlist_riders = []
    if startlist_cache_key in cached_startlist_data:
        startlist_riders = cached_startlist_data[startlist_cache_key]["startlist"]

    # Log a little bit about the cached data
    # st.write(f"Cached PCS data: {len(cached_rider_data)} riders")
    # st.write(f"Cached startlist data: {len(startlist_riders)} riders")

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
            rider["pcs_matched_name"] = matched_startlist_rider.get(
                "pcs_matched_name", ""
            )
            rider["pcs_rider_url"] = matched_startlist_rider.get("pcs_rider_url", "")
            # Check if the cached PCS data exists for this rider
            if matched_startlist_rider.get("pcs_rider_url") in cached_rider_data:
                rider["pcs_data"] = cached_rider_data[
                    matched_startlist_rider["pcs_rider_url"]
                ]

    # Log matching results
    if matched_pcs_rider_count > 0:
        logging.info(f"✅ Matched {matched_pcs_rider_count} riders")
    else:
        logging.warning("❌ No riders matched")

    riders_df = pd.DataFrame(riders)

    # Process the rider's data
    riders_df = prepare_rider_data(riders_df)

    return riders_df
