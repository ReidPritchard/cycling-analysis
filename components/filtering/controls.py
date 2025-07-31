"""
Filter control UI components.
"""

import streamlit as st

from .search import get_sort_options


def render_unified_controls(df, view_key_prefix=""):
    """Render unified control interface for all display modes."""
    st.markdown("### 🔍 Rider Search & Filters")

    # Search and filter row
    search_col, sort_col, order_col = st.columns([2, 2, 1])

    with search_col:
        search_term = st.text_input(
            "Search riders",
            placeholder="Enter name, team, position, or nationality...",
            key=f"{view_key_prefix}_search",
            help="Search across rider names, teams, positions, and nationalities",
        )

    with sort_col:
        sort_options = get_sort_options()
        sort_by_label = st.selectbox(
            "Sort by",
            list(sort_options.keys()),
            key=f"{view_key_prefix}_sort",
            help="Choose how to order the riders",
        )
        sort_by_column = sort_options[sort_by_label]

    with order_col:
        # Smart default: ascending for consistency (lower is better), descending for others
        default_ascending = sort_by_column in [
            "consistency_score",
            "full_name",
            "team",
            "position",
        ]
        ascending = st.checkbox(
            "Ascending",
            value=default_ascending,
            key=f"{view_key_prefix}_ascending",
            help="Sort order: checked = A to Z / low to high, unchecked = Z to A / high to low",
        )

    # Quick filter buttons
    st.markdown("**Quick Filters:**")
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        show_high_value = st.checkbox(
            "💰 High Value Only",
            key=f"{view_key_prefix}_high_value",
            help="Show only riders with above-average points per star",
        )
        show_with_points = st.checkbox(
            "🏆 Has Points Only",
            key=f"{view_key_prefix}_has_points",
            help="Show only riders who have earned points this season",
        )

    with filter_col2:
        # Team filter
        teams = ["All"] + sorted(df["team"].unique().tolist())
        selected_team = st.selectbox("Team", teams)

    with filter_col3:
        position_filter = st.selectbox(
            "Position",
            options=["All"] + sorted(df["position"].unique().tolist()),
            key=f"{view_key_prefix}_position",
            help="Filter by rider position",
        )

    with filter_col4:
        min_stars, max_stars = st.slider(
            "Star Cost Range",
            min_value=int(df["stars"].min()),
            max_value=int(df["stars"].max()),
            value=(int(df["stars"].min()), int(df["stars"].max())),
        )

    return {
        "search_term": search_term,
        "sort_by_column": sort_by_column,
        "ascending": ascending,
        "show_high_value": show_high_value,
        "show_with_points": show_with_points,
        "min_stars": min_stars,
        "max_stars": max_stars,
        "team": selected_team if selected_team != "All" else None,
        "position_filter": position_filter,
    }
