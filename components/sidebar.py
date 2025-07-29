"""
Sidebar components for the Fantasy Cycling Stats app.
"""

import streamlit as st
from config.settings import PCS_CACHE_FILE, RACE_CACHE_FILE, PCS_STARTLIST_CACHE_FILE
from utils.cache_manager import get_cache_info
from data.pcs_data import fetch_pcs_data, refresh_pcs_cache, refresh_startlist_cache
from data.race_data import fetch_tdf_femmes_2025_data, refresh_race_cache
from data.fantasy_data import load_fantasy_data


def render_sidebar_controls(riders):
    """Render all sidebar controls and return filter values"""
    with st.sidebar:
        st.header("🎛️ Controls")

        # Cache management
        st.subheader("Cache Management")
        if st.button("🌐 Fetch PCS Data", use_container_width=True):
            with st.spinner("Fetching ProCyclingStats data..."):
                riders = fetch_pcs_data(load_fantasy_data())
                st.success("✅ PCS data fetched successfully!")

        if st.button("🗑️ Clear Cache", use_container_width=True):
            refresh_pcs_cache()
            refresh_startlist_cache()

        # Race data management
        st.subheader("🚴‍♀️ TdF Femmes 2025")
        if st.button("🏁 Fetch Race Data", use_container_width=True):
            with st.spinner("Fetching Tour de France Femmes 2025 data..."):
                race_data = fetch_tdf_femmes_2025_data()
                if "error" not in race_data:
                    st.success("✅ Race data fetched successfully!")
                else:
                    st.error("❌ Failed to fetch race data")

        if st.button("🗑️ Clear Race Cache", use_container_width=True):
            refresh_race_cache()

        # Display cache info
        _display_cache_info()

        st.divider()

        # Filters
        st.subheader("🔍 Filters")

    return _render_filters(riders)


def _display_cache_info():
    """Display cache information in the sidebar"""
    # PCS cache info
    pcs_cache_info = get_cache_info(PCS_CACHE_FILE)
    if pcs_cache_info:
        st.markdown(
            f"""
        <div class="cache-info">
            <strong>📅 PCS Rider Cache</strong><br>
            Last updated: {pcs_cache_info['last_updated']}<br>
            Riders cached: {pcs_cache_info['data_count']}
        </div>
        """,
            unsafe_allow_html=True,
        )

    # PCS startlist cache info
    startlist_cache_info = get_cache_info(PCS_STARTLIST_CACHE_FILE)
    if startlist_cache_info:
        st.markdown(
            f"""
        <div class="cache-info">
            <strong>📋 PCS Startlist Cache</strong><br>
            Last updated: {startlist_cache_info['last_updated']}<br>
            Startlists cached: {startlist_cache_info['data_count']}
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Race cache info
    race_cache_info = get_cache_info(RACE_CACHE_FILE)
    if race_cache_info:
        st.markdown(
            f"""
        <div class="cache-info">
            <strong>🏁 Race Cache Info</strong><br>
            Last updated: {race_cache_info['last_updated']}<br>
            Races cached: {race_cache_info['data_count']}
        </div>
        """,
            unsafe_allow_html=True,
        )


def _render_filters(riders):
    """Render filter controls and return selected values"""
    with st.sidebar:
        # Position filter
        positions = ["All"] + sorted(riders["position"].unique().tolist())
        selected_position = st.selectbox("Position", positions)

        # Team filter
        teams = ["All"] + sorted(riders["team"].unique().tolist())
        selected_team = st.selectbox("Team", teams)

        # Star rating filter
        min_stars, max_stars = st.slider(
            "Star Rating Range",
            min_value=int(riders["stars"].min()),
            max_value=int(riders["stars"].max()),
            value=(int(riders["stars"].min()), int(riders["stars"].max())),
        )

        # Search by name
        search_term = st.text_input("🔍 Search by name")

    return {
        "position": selected_position,
        "team": selected_team,
        "min_stars": min_stars,
        "max_stars": max_stars,
        "search_term": search_term,
    }
