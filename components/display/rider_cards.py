"""
Rider card display components.
"""

import streamlit as st

from ..common.calculations import calculate_percentiles
from ..common.pagination import paginate_dataframe
from ..filtering.controls import render_unified_controls
from ..filtering.filters import apply_filters
from .performance import render_compact_performance_summary, render_season_results
from .rider_info import render_rider_info


def render_single_rider_card(rider, percentiles=None):
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


def display_rider_cards(df, page_size=10):
    """Display riders in card format with unified controls and pagination."""
    # Calculate percentiles for fantasy value assessment
    percentiles = calculate_percentiles(df)

    # Render unified controls
    filters = render_unified_controls(df, "cards")

    # Apply filters and sorting
    df_filtered = apply_filters(df, filters)

    # Show results summary
    total_riders = len(df)
    filtered_count = len(df_filtered)

    if df_filtered.empty:
        st.warning(
            "🔍 No riders match your search criteria. Try adjusting your filters."
        )
        return

    # Pagination
    df_page, current_page, total_pages = paginate_dataframe(
        df_filtered, page_size, "cards_page"
    )

    # Results summary with pagination info
    if total_pages > 1:
        start_idx = (current_page - 1) * page_size + 1
        end_idx = min(current_page * page_size, filtered_count)
        st.info(
            f"👥 Showing riders {start_idx}-{end_idx} of {filtered_count} "
            f"({'filtered from ' + str(total_riders) + ' total' if filtered_count != total_riders else 'total'})"
        )
    else:
        if filtered_count != total_riders:
            st.info(f"🔍 Showing {filtered_count} of {total_riders} riders")
        else:
            st.info(f"👥 Showing all {total_riders} riders")

    # Display cards
    for _, rider in df_page.iterrows():
        render_single_rider_card(rider, percentiles)
