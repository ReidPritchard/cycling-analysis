"""
Rider data processing and analytics calculations.
"""

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from ..models.race import RaceData
from .combined_rider_analytics import calculate_race_specific_analytics


def process_season_results(
    pcs_data: dict[str, Any] | None,
) -> tuple[pd.DataFrame, int, int, float, float]:
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

    # Sort by date (most recent first) and limit to 10 results
    df_results = df_results.sort_values(by="date", ascending=False).head(10)

    # Calculate totals
    total_pcs_points = int(df_results["pcs_points"].sum()) if not df_results.empty else 0
    total_uci_points = int(df_results["uci_points"].sum()) if not df_results.empty else 0

    # Calculate consistency and trend metrics
    consistency_score = 0.0
    trend_score = 0.0

    if not df_results.empty and len(df_results) >= 2:
        # Consistency: coefficient of variation of results (lower is more consistent)
        results_positions = pd.to_numeric(df_results["gc_position"], errors="coerce").dropna()
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
            df_trend["result_numeric"] = pd.to_numeric(df_trend["gc_position"], errors="coerce")
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


def calculate_rider_demographics(pcs_data: dict[str, Any] | None) -> dict[str, Any]:
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


def calculate_rider_metrics(
    df: pd.DataFrame,
    race_data: RaceData | None = None,
    race_key: str | None = None,
    use_combined_analytics: bool = True,
) -> pd.DataFrame:
    """Add calculated fields to the rider dataframe.

    Args:
        df: Rider dataframe
        race_data: Optional race data for enhanced analytics
        race_key: Race identifier for enhanced analytics
        use_combined_analytics: Whether to use combined race analytics
    """
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

    # Enhanced analytics columns (when combined analytics available)
    df["stage_analytics_available"] = False
    df["avg_stage_position"] = None
    df["best_stage_position"] = None
    df["stage_wins"] = 0
    df["gc_current_rank"] = None
    df["gc_best_rank"] = None
    df["rider_type"] = None
    df["data_completeness_score"] = 0.0

    # Process each rider
    for idx, row in df.iterrows():
        pcs_data = row.get("pcs_data", {})

        # Use combined analytics if available, otherwise fall back to season results
        if use_combined_analytics and race_data and race_key:
            try:
                # Calculate enhanced analytics using race stage data
                combined_analytics = calculate_race_specific_analytics(
                    row.to_dict(), race_data, race_key
                )

                # Extract enhanced metrics
                df.at[idx, "stage_analytics_available"] = combined_analytics.get(
                    "has_stage_data", False
                )
                df.at[idx, "data_completeness_score"] = combined_analytics.get(
                    "data_completeness_score", 0.0
                )

                # Use stage-based point totals (more accurate than season results)
                total_pcs = combined_analytics.get("total_stage_pcs_points", 0)
                total_uci = combined_analytics.get("total_stage_uci_points", 0)

                # Enhanced stage performance metrics
                df.at[idx, "avg_stage_position"] = combined_analytics.get("avg_stage_position")
                df.at[idx, "best_stage_position"] = combined_analytics.get("best_stage_position")
                df.at[idx, "stage_wins"] = combined_analytics.get("stage_wins", 0)

                # GC analytics
                gc_analytics = combined_analytics.get("gc_analytics")
                if gc_analytics:
                    df.at[idx, "gc_current_rank"] = gc_analytics.get("current_rank")
                    df.at[idx, "gc_best_rank"] = gc_analytics.get("best_rank")

                # Rider classification
                df.at[idx, "rider_type"] = combined_analytics.get("rider_type_classification")

                # Use combined consistency score if available
                consistency = combined_analytics.get("consistency_score")
                trend = combined_analytics.get("stage_position_trend")

                # Get season results for display (still useful for historical context)
                season_results, _, _, fallback_consistency, fallback_trend = (
                    process_season_results(pcs_data)
                )
                if season_results is not None:
                    df.at[idx, "season_results"] = season_results

                # Use combined metrics if available, otherwise fall back
                df.at[idx, "consistency_score"] = (
                    consistency if consistency is not None else fallback_consistency
                )
                df.at[idx, "trend_score"] = trend if trend is not None else fallback_trend

            except Exception as e:
                # Fall back to season results if combined analytics fail
                print(
                    f"Warning: Combined analytics failed for {row.get('fantasy_name', 'unknown')}: {e}"
                )
                season_results, total_pcs, total_uci, consistency, trend = process_season_results(
                    pcs_data
                )
                df.at[idx, "season_results"] = season_results
                df.at[idx, "consistency_score"] = consistency
                df.at[idx, "trend_score"] = trend
        else:
            # Fall back to original season results processing
            season_results, total_pcs, total_uci, consistency, trend = process_season_results(
                pcs_data
            )
            df.at[idx, "season_results"] = season_results
            df.at[idx, "consistency_score"] = consistency
            df.at[idx, "trend_score"] = trend

        # Set point totals
        df.at[idx, "total_pcs_points"] = total_pcs
        df.at[idx, "total_uci_points"] = total_uci

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
