"""
Tab content components for the Fantasy Cycling Stats app.
"""

from datetime import datetime

import pandas as pd
import streamlit as st

from components.rider_display import (
    display_rider_cards,
    display_rider_table,
    display_summary_stats,
)
from components.visualizations import (
    create_star_cost_distribution_chart,
    create_stats_overview,
    show_detailed_analytics,
)
from data.race_data import (
    refresh_race_cache,
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

    # Check if race data has an error
    if "error" in race_data:
        st.error(f"❌ Error loading race data: {race_data['error']}")

        # Show refresh option for errors
        if st.button("🔄 Refresh Race Data", use_container_width=True):
            refresh_race_cache()
            st.rerun()
        return

    # Display race status and last updated info
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        race_info = race_data.get("race_data", {})
        race_name = race_info.get("name", "Tour de France Femmes 2025")
        st.markdown(f"**{race_name}**")

    with col2:
        if "fetched_at" in race_data:
            fetch_time = datetime.fromisoformat(race_data["fetched_at"])
            st.markdown(f"*Updated: {fetch_time.strftime('%m/%d %H:%M')}*")

    with col3:
        if st.button("🔄", help="Refresh race data", use_container_width=True):
            refresh_race_cache()
            st.rerun()

    # climbs = race_data.get("climbs", [])
    # if climbs:
    #     st.markdown(f"**🏔️ Climbs:** {len(climbs)} major climbs identified")

    #     st.dataframe(
    #         pd.DataFrame(climbs),
    #         use_container_width=True,
    #         hide_index=True,
    #         height=200,
    #     )

    _show_race_info_tab(race_data)

    st.caption("Work in progress")

    # # Create compact tabs for different race data views
    # race_tab1, race_tab2, race_tab3 = st.tabs(
    #     ["📋 Overview", "🏆 Classification", "🚩 Stages"]
    # )

    # with race_tab1:
    #     _show_race_info_tab(race_data)

    # with race_tab2:
    #     _show_gc_tab(race_data)

    # with race_tab3:
    #     _show_stages_tab(race_data)


def _show_race_info_tab(race_data):
    """Display race information tab"""
    if race_data.get("race_data"):
        race_info = race_data["race_data"]

        # Display key race metrics in a compact format
        if isinstance(race_info, dict) and race_info:
            # Show key information if available
            col1, col2, col3 = st.columns(3)

            with col1:
                if "startdate" in race_info:
                    st.metric("Start Date", race_info["startdate"])
                elif "date" in race_info:
                    st.metric("Date", race_info["date"])

            with col2:
                if "enddate" in race_info:
                    st.metric("End Date", race_info["enddate"])
                elif "year" in race_info:
                    st.metric("Year", race_info["year"])

            with col3:
                if "distance" in race_info:
                    st.metric("Total Distance", f"{race_info['distance']} km")

            # Show expandable details
            with st.expander("📄 Detailed Race Information"):
                st.json(race_info)
        else:
            st.info(
                "ℹ️ Detailed race information will be available when the race data is loaded."
            )
    else:
        st.info("ℹ️ No race information available yet.")


def _show_gc_tab(race_data):
    """Display general classification tab"""
    # Check multiple possible locations for GC data
    gc_data = race_data.get("gc") or race_data.get("race_data", {}).get("gc")

    if gc_data and len(gc_data) > 0:
        # Convert to DataFrame for better display
        if isinstance(gc_data, list) and len(gc_data) > 0:
            gc_df = pd.DataFrame(gc_data)
            st.dataframe(gc_df, use_container_width=True, height=400)
        else:
            with st.expander("📊 Classification Data"):
                st.json(gc_data)
    else:
        st.info("🏁 General Classification will appear here once the race begins.")

        # Show what to expect
        st.markdown("""
        **What you'll see here:**
        - Current race leader and yellow jersey holder
        - Time gaps between riders
        - Overall standings updated after each stage
        - Points and mountain classification leaders
        """)


def _show_stages_tab(race_data):
    """Display stages information tab"""
    stages_data = race_data.get("stages", [])

    if stages_data and len(stages_data) > 0:
        # Display stages in a more compact format
        if isinstance(stages_data, list):
            # Create a summary table first
            stage_summary = []
            for i, stage in enumerate(stages_data):
                if isinstance(stage, dict):
                    stage_summary.append(
                        {
                            "Stage": i + 1,
                            "Name": stage.get("name", f"Stage {i + 1}"),
                            "Date": stage.get("date", "TBD"),
                            "Distance": stage.get("distance", "N/A"),
                            "Type": stage.get("type", "N/A"),
                        }
                    )

            if stage_summary:
                st.subheader("📊 Stage Overview")
                stage_df = pd.DataFrame(stage_summary)
                st.dataframe(stage_df, use_container_width=True, hide_index=True)

            st.subheader("🚩 Stage Details")
            # Show stages in expandable sections
            for i, stage in enumerate(stages_data):
                if isinstance(stage, dict):
                    stage_name = stage.get("name", f"Stage {i + 1}")
                    stage_date = stage.get("date", "TBD")

                    with st.expander(f"Stage {i + 1}: {stage_name} ({stage_date})"):
                        # Display stage details in columns
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Distance", stage.get("distance", "N/A"))

                        with col2:
                            st.metric("Type", stage.get("type", "N/A"))

                        with col3:
                            st.metric("Profile", stage.get("profile", "N/A"))

                        # Show additional stage details if available
                        if len(stage) > 5:  # More than basic fields
                            with st.expander("📄 Additional Stage Details"):
                                st.json(stage)
                else:
                    with st.expander(f"Stage {i + 1}"):
                        st.json(stage)
        else:
            with st.expander("📊 Stages Data"):
                st.json(stages_data)
    else:
        st.info(
            "🚩 Stage information will be available when the race route is published."
        )

        # Show what to expect
        st.markdown("""
        **What you'll see here:**
        - Complete stage breakdown with distances and profiles
        - Stage types (flat, hilly, mountain, time trial)
        - Start/finish locations for each stage
        - Elevation profiles and key climbs
        """)
