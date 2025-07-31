"""
Filter application logic for rider data.
"""

from typing import Any

import pandas as pd

from .search import filter_riders_by_search


def apply_filters(df: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
    """Apply all filters to the dataframe."""
    filtered_df = df.copy()

    # Apply search filter
    filtered_df = filter_riders_by_search(filtered_df, filters["search_term"])

    # Apply quick filters
    if filters["show_high_value"]:
        # Show riders with above-average efficiency
        avg_pcs_per_star = filtered_df["pcs_per_star"].mean()
        filtered_df = filtered_df[filtered_df["pcs_per_star"] >= avg_pcs_per_star]

    if filters["show_with_points"]:
        filtered_df = filtered_df[
            (filtered_df["total_pcs_points"] > 0)
            | (filtered_df["total_uci_points"] > 0)
        ]

    if filters["min_stars"] > 0:
        filtered_df = filtered_df[filtered_df["stars"] >= filters["min_stars"]]
    if filters["max_stars"] < df["stars"].max():
        filtered_df = filtered_df[filtered_df["stars"] <= filters["max_stars"]]

    if filters["position_filter"] != "All":
        filtered_df = filtered_df[filtered_df["position"] == filters["position_filter"]]

    if filters["team"] != "All" and filters["team"] is not None:
        filtered_df = filtered_df[filtered_df["team"] == filters["team"]]

    # Apply sorting
    if not filtered_df.empty:
        filtered_df = filtered_df.sort_values(
            filters["sort_by_column"], ascending=filters["ascending"]
        )

    return filtered_df
