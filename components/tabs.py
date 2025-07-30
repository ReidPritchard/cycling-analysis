"""
Tab content components for the Fantasy Cycling Stats app.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from components.visualizations import (
    create_stats_overview,
    show_detailed_analytics,
    create_star_cost_distribution_chart,
)
from components.rider_display import (
    display_rider_cards,
    display_rider_table,
    display_summary_stats,
)
from data.race_data import (
    fetch_tdf_femmes_2025_data,
    refresh_race_cache,
    get_stage_results,
)


def show_overview_tab(filtered_riders):
    """Display the overview tab content"""
    st.subheader("📈 Key Statistics")
    create_stats_overview(filtered_riders)

    st.divider()

    # Quick stats
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏅 Position/Style Breakdown")
        position_counts = filtered_riders["position"].value_counts()
        for pos, count in position_counts.items():
            st.markdown(f"**{pos}:** {count} riders")

    with col2:
        st.subheader("⭐ Star Cost Distribution")
        create_star_cost_distribution_chart(filtered_riders)


def show_riders_tab(filtered_riders):
    """Display the riders tab content"""
    st.subheader(f"🏆 Riders ({len(filtered_riders)} found)")

    display_summary_stats(filtered_riders)

    # Display format options
    display_format = st.radio("Display as:", ["Cards", "Table"])

    if display_format == "Cards":
        display_rider_cards(filtered_riders)
    else:
        display_rider_table(filtered_riders)


def show_analytics_tab(filtered_riders):
    """Display the analytics tab content"""
    show_detailed_analytics(filtered_riders)


def show_race_tab(race_data):
    """Display the TdF Femmes 2025 tab content"""
    st.header("🏁 Tour de France Femmes 2025")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("📥 Load Race Data", use_container_width=True):
            with st.spinner("Loading Tour de France Femmes 2025 data..."):
                race_data = fetch_tdf_femmes_2025_data()
                st.session_state.race_data = race_data

    with col2:
        if st.button("🔄 Refresh Race Data", use_container_width=True):
            refresh_race_cache()
            with st.spinner("Refreshing Tour de France Femmes 2025 data..."):
                race_data = fetch_tdf_femmes_2025_data()
                st.session_state.race_data = race_data

    # Display race data if available
    if "race_data" in st.session_state:
        race_data = st.session_state.race_data

        if "error" in race_data:
            st.error(f"❌ Error loading race data: {race_data['error']}")
        else:
            st.success("✅ Race data loaded successfully!")

            # Create sub-tabs for different race data views
            race_tab1, race_tab2, race_tab3 = st.tabs(
                ["📋 Race Info", "🏆 General Classification", "🚩 Stages"]
            )

            with race_tab1:
                _show_race_info_tab(race_data)

            with race_tab2:
                _show_gc_tab(race_data)

            with race_tab3:
                _show_stages_tab(race_data)
    else:
        _show_race_info_placeholder()


def _show_race_info_tab(race_data):
    """Display race information tab"""
    st.subheader("📋 Race Information")

    if race_data.get("race_data"):
        race_info = race_data["race_data"]

        # Display basic race info
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Race", race_info.get("name", "Tour de France Femmes"))

        with col2:
            st.metric("Year", race_info.get("year", "2025"))

        with col3:
            if "fetched_at" in race_data:
                fetch_time = datetime.fromisoformat(race_data["fetched_at"])
                st.metric("Last Updated", fetch_time.strftime("%m/%d %H:%M"))

        # Display additional race details if available
        if isinstance(race_info, dict):
            st.json(race_info)
    else:
        st.info("ℹ️ No detailed race information available yet.")


def _show_gc_tab(race_data):
    """Display general classification tab"""
    st.subheader("🏆 General Classification")

    if race_data.get("gc") and len(race_data["gc"]) > 0:
        gc_data = race_data["gc"]

        # Convert to DataFrame for better display
        if isinstance(gc_data, list) and len(gc_data) > 0:
            gc_df = pd.DataFrame(gc_data)
            st.dataframe(gc_df, use_container_width=True)
        else:
            st.json(gc_data)
    else:
        st.info(
            "ℹ️ General Classification data not available yet. The race may not have started."
        )


def _show_stages_tab(race_data):
    """Display stages information tab"""
    st.subheader("🚩 Stage Information")

    if race_data.get("stages") and len(race_data["stages"]) > 0:
        stages_data = race_data["stages"]

        # Display stages information
        if isinstance(stages_data, list):
            for i, stage in enumerate(stages_data):
                with st.expander(f"Stage {i+1}: {stage.get('name', f'Stage {i+1}')}"):
                    if isinstance(stage, dict):
                        # Display stage details
                        stage_col1, stage_col2 = st.columns(2)

                        with stage_col1:
                            st.write(f"**Distance:** {stage.get('distance', 'N/A')}")
                            st.write(f"**Type:** {stage.get('type', 'N/A')}")

                        with stage_col2:
                            st.write(f"**Date:** {stage.get('date', 'N/A')}")
                            st.write(f"**Profile:** {stage.get('profile', 'N/A')}")

                        # Option to get stage results
                        if st.button(f"Get Stage {i+1} Results", key=f"stage_{i+1}"):
                            with st.spinner(f"Fetching Stage {i+1} results..."):
                                stage_results = get_stage_results(i + 1)
                                if stage_results:
                                    st.json(stage_results)
                                else:
                                    st.info("No results available for this stage yet.")
                    else:
                        st.json(stage)
        else:
            st.json(stages_data)
    else:
        st.info("ℹ️ Stage information not available yet.")


def _show_race_info_placeholder():
    """Show placeholder information when race data is not loaded"""
    st.info(
        "👆 Click 'Load Race Data' to fetch Tour de France Femmes 2025 information."
    )

    # Show some helpful information about what data will be available
    st.markdown(
        """
    ### 📊 What data will be available?
    
    - **Race Information**: Basic details about the race
    - **General Classification**: Overall standings and time gaps  
    - **Stage Information**: Details about each stage including distance, profile, and type
    - **Stage Results**: Individual stage winners and results (when available)
    
    ### 🔄 Data Updates
    
    - Data is cached for 7 days to improve performance
    - Use 'Refresh Race Data' to get the latest information
    - Stage results will be available as the race progresses
    """
    )
