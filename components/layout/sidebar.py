"""
Sidebar components for the Fantasy Cycling Stats app.
"""

import streamlit as st

from config.settings import PCS_CACHE_FILE, RACE_CACHE_FILE, SUPPORTED_RACES
from data import refresh_pcs_cache
from utils.cache_manager import get_cache_info


def _render_sidebar_controls() -> None:
    """Render sidebar controls and return filter values"""
    st.header("🎛️ Controls")

    # Cache management
    st.subheader("Cache Management")
    if st.button("🌐 Fetch PCS Data", use_container_width=True):
        with st.spinner("Fetching ProCyclingStats data..."):
            # FIXME: Use the race from the selectbox
            refresh_pcs_cache()
            st.error("❗️ PCS data fetch is not implemented yet!")
            # fetch_pcs_data("TDF_FEMMES_2025", )
            st.success("✅ PCS data fetched successfully!")


def render_sidebar(race_key: str) -> None:
    """Render all sidebar controls and return filter values"""
    with st.sidebar:
        _render_sidebar_controls()
        # Display cache info
        _display_cache_info(race_key)


def _display_cache_info(race_key: str) -> None:
    """Display cache information in the sidebar"""
    # PCS cache info
    pcs_cache_info = get_cache_info(PCS_CACHE_FILE)
    if pcs_cache_info:
        st.markdown(
            f"""
        <div class="cache-info">
            <strong>📅 PCS Rider Cache</strong><br>
            Last updated: {pcs_cache_info["last_updated"]}<br>
            Riders cached: {pcs_cache_info["data_count"]}
        </div>
        """,
            unsafe_allow_html=True,
        )

    # PCS startlist cache info
    startlist_cache_info = get_cache_info(SUPPORTED_RACES[race_key]["startlist_cache_path"])
    if startlist_cache_info:
        st.markdown(
            f"""
        <div class="cache-info">
            <strong>📋 PCS Startlist Cache</strong><br>
            Last updated: {startlist_cache_info["last_updated"]}<br>
            Startlists cached: {startlist_cache_info["data_count"]}
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Race cache info
    # FIXME: Make dynamic based on race selection
    race_cache_info = get_cache_info(RACE_CACHE_FILE)
    if race_cache_info:
        st.markdown(
            f"""
        <div class="cache-info">
            <strong>🏁 Race Cache Info</strong><br>
            Last updated: {race_cache_info["last_updated"]}<br>
            Races cached: {race_cache_info["data_count"]}
        </div>
        """,
            unsafe_allow_html=True,
        )
