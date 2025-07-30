"""
Fantasy Cycling Stats Dashboard

A Streamlit application for analyzing fantasy cycling rider statistics
and Tour de France Femmes 2025 race data.
"""

import streamlit as st

# Import UI components
from components.sidebar import render_sidebar_controls
from components.tabs import (
    show_analytics_tab,
    show_overview_tab,
    show_riders_tab,
)

# Import configuration and styling
from config.settings import PAGE_CONFIG
from config.styling import FOOTER_HTML, MAIN_CSS

# Import data modules
from data.fantasy_data import load_fantasy_data
from data.race_data import load_race_data

# Configure page
st.set_page_config(**PAGE_CONFIG)

# Apply custom CSS styling
st.markdown(MAIN_CSS, unsafe_allow_html=True)


def apply_filters(riders, filters):
    """Apply filters to the riders dataframe."""
    filtered_riders = riders.copy()

    if filters["position"] != "All":
        filtered_riders = filtered_riders[
            filtered_riders["position"] == filters["position"]
        ]

    if filters["team"] != "All":
        filtered_riders = filtered_riders[filtered_riders["team"] == filters["team"]]

    filtered_riders = filtered_riders[
        (filtered_riders["stars"] >= filters["min_stars"])
        & (filtered_riders["stars"] <= filters["max_stars"])
    ]

    if filters["search_term"]:
        mask = (
            filtered_riders["full_name"].str.contains(
                filters["search_term"], case=False, na=False
            )
            | filtered_riders["fantasy_name"].str.contains(
                filters["search_term"], case=False, na=False
            )
            | filtered_riders["team"].str.contains(
                filters["search_term"], case=False, na=False
            )
        )
        filtered_riders = filtered_riders[mask]

    return filtered_riders


def main():
    """Main application logic."""
    # Main App Layout
    st.title("🚴‍♀️ Fantasy Cycling Stats Dashboard")

    # Load rider data
    # We should only do this once
    riders = load_fantasy_data()

    # Load race data (also only once)
    race_data = load_race_data("tdf_femmes_2025")

    # Render sidebar and get filter values
    filters = render_sidebar_controls(riders)

    # Load and filter data
    filtered_riders = apply_filters(riders, filters)

    # Main content area
    # TODO: Add support for other races?
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Overview", "🏆 Riders", "📈 Analytics", "🏁 Race Data"]
    )

    with tab1:
        show_overview_tab(filtered_riders)

    with tab2:
        show_riders_tab(filtered_riders)

    with tab3:
        show_analytics_tab(filtered_riders)

    with tab4:
        st.header("🏁 Coming Soon!")
        # show_race_tab(race_data)

    # Footer
    st.divider()
    st.markdown(FOOTER_HTML, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
