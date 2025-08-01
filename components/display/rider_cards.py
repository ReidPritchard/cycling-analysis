"""
Rider card display components.
"""

from typing import Any

import pandas as pd
import streamlit as st

from ..common.calculations import calculate_percentiles
from ..common.pagination import paginate_dataframe
from .performance import render_compact_performance_summary, render_season_results
from .rider_info import render_rider_info


def render_single_rider_card(rider: pd.Series, percentiles: dict[str, Any] | None = None) -> None:
    """Render a single rider card with improved layout."""
    with st.container(border=True):
        # Better 2-column layout for improved readability
        info_col, stats_col = st.columns([1, 1])

        with info_col:
            render_rider_info(rider, percentiles)
            # Add compact performance summary
            render_compact_performance_summary(rider)

        with stats_col:
            render_season_results(rider)

        st.markdown("---")  # Subtle separator instead of heavy divider


def display_rider_cards(df: pd.DataFrame, page_size: int = 10) -> None:
    """Display riders in card format with pagination."""
    # Calculate percentiles for fantasy value assessment
    percentiles = calculate_percentiles(df)

    # Handle empty dataframe (after global filtering)
    if df.empty:
        st.warning(
            "🔍 No riders match the current filters. Try adjusting the global filters above."
        )
        return

    # Pagination (no local filtering since it's now handled globally)
    df_page, current_page, total_pages = paginate_dataframe(df, page_size, "cards_page")

    # Results summary with pagination info
    total_riders = len(df)
    if total_pages > 1:
        start_idx = (current_page - 1) * page_size + 1
        end_idx = min(current_page * page_size, total_riders)
        st.info(f"👥 Showing riders {start_idx}-{end_idx} of {total_riders}")
    else:
        st.info(f"👥 Showing all {total_riders} riders")

    # Display cards
    for _, rider in df_page.iterrows():
        render_single_rider_card(rider, percentiles)
