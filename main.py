"""
Fantasy Cycling Stats Dashboard

A Streamlit application for analyzing fantasy cycling rider statistics
and Tour de France Femmes 2025 race data.
"""

from typing import Any

import pandas as pd
import streamlit as st

# Import UI components
from components.layout.sidebar import render_sidebar
from components.layout.tabs import (
    show_analytics_tab,
    show_overview_tab,
    show_race_tab,
    show_riders_tab,
)

# Import configuration and styling
from config.settings import SUPPORTED_RACES
from config.styling import FOOTER_HTML, MAIN_CSS

# Import data modules
from data import load_fantasy_data, load_race_data

# Configure page
# st.set_page_config(**PAGE_CONFIG)

# Apply custom CSS styling
st.markdown(MAIN_CSS, unsafe_allow_html=True)


def apply_filters(riders: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
    """Apply filters to the riders dataframe."""
    filtered_riders = riders.copy()

    if filters["position"] != "All":
        filtered_riders = filtered_riders[filtered_riders["position"] == filters["position"]]

    if filters["team"] != "All":
        filtered_riders = filtered_riders[filtered_riders["team"] == filters["team"]]

    filtered_riders = filtered_riders[
        (filtered_riders["stars"] >= filters["min_stars"])
        & (filtered_riders["stars"] <= filters["max_stars"])
    ]

    if filters["search_term"]:
        mask = (
            filtered_riders["full_name"].str.contains(filters["search_term"], case=False, na=False)
            | filtered_riders["fantasy_name"].str.contains(
                filters["search_term"], case=False, na=False
            )
            | filtered_riders["team"].str.contains(filters["search_term"], case=False, na=False)
        )
        filtered_riders = filtered_riders[mask]

    return filtered_riders


def main() -> None:
    """Main application logic."""
    # Main App Layout
    st.title("🚴‍♀️ Fantasy Cycling Stats Dashboard")

    # Display the header
    st.markdown("""
    Welcome to the Fantasy Cycling Stats Dashboard! This application provides insights into rider
    statistics.
    """)

    # Race selection
    selected_race_name = st.selectbox(
        "Race:",
        [race["name"] for race in SUPPORTED_RACES.values()],
    )
    # Find the selected race in supported races
    selected_race_key = next(
        (key for key, value in SUPPORTED_RACES.items() if value["name"] == selected_race_name),
        None,
    )

    if selected_race_key is None:
        st.info("Plese select a race to continue.")
        return

    # Load rider data
    # We should only do this once
    riders = load_fantasy_data()

    # Load race data (also only once)
    race_data = load_race_data(selected_race_key)

    # Render sidebar and get filter values
    filters = render_sidebar(riders)

    # Load and filter data
    filtered_riders = apply_filters(riders, filters)

    # Main content area
    # TODO: Add support for other races?
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🏆 Riders", "📈 Analytics", "🏁 Race Data"])

    with tab1:
        show_overview_tab(filtered_riders)

    with tab2:
        show_riders_tab(filtered_riders)

    with tab3:
        show_analytics_tab(filtered_riders)

    with tab4:
        show_race_tab(race_data)

    # Footer
    st.divider()
    st.markdown(FOOTER_HTML, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
