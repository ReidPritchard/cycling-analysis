"""
Search functionality for filtering riders.
"""

import pandas as pd


def get_sort_options():
    """Get available sorting options."""
    return {
        "Best Value (PCS/Star)": "pcs_per_star",
        "Best Value (UCI/Star)": "uci_per_star",
        "Most Points (PCS)": "total_pcs_points",
        "Most Points (UCI)": "total_uci_points",
        "Star Cost": "stars",
        "Most Consistent": "consistency_score",
        "Recent Form": "trend_score",
        "Rider Name": "full_name",
        "Team": "team",
        "Position": "position",
        "Age": "age",
        "Results Count": "season_results_count",
    }


def filter_riders_by_search(df, search_term):
    """Filter riders based on search term."""
    if not search_term:
        return df

    search_term = search_term.lower().strip()

    # Search across multiple fields
    mask = (
        df["full_name"].str.lower().str.contains(search_term, na=False)
        | df["team"].str.lower().str.contains(search_term, na=False)
        | df["position"].str.lower().str.contains(search_term, na=False)
        | df.get("nationality", pd.Series(dtype="object"))
        .str.lower()
        .str.contains(search_term, na=False)
    )

    return df[mask]
