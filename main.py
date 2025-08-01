"""
Fantasy Cycling Stats Dashboard

A Streamlit application for analyzing fantasy cycling rider statistics
and Tour de France Femmes 2025 race data.
"""

import logging

import pandas as pd
import streamlit as st

from components.filtering.controls import render_unified_controls
from components.filtering.filters import apply_filters
from components.layout.sidebar import render_sidebar

# Import UI components
from components.layout.tabs import (
    show_analytics_tab,
    show_overview_tab,
    show_race_tab,
    show_riders_tab,
)

# Import configuration and styling
from config.settings import PAGE_CONFIG, SUPPORTED_RACES
from config.styling import FOOTER_HTML, MAIN_CSS

# Import data modules
from data.models.unified import PipelineConfig
from data.pipeline import run_pipeline

logger = logging.getLogger(__name__)


def main() -> None:
    """Main application logic."""
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    logger.info("Starting Fantasy Cycling Stats Dashboard")

    # Configure page
    st.set_page_config(**PAGE_CONFIG)

    # Apply custom CSS styling
    st.markdown(MAIN_CSS, unsafe_allow_html=True)

    # Main App Layout
    st.title("🚴‍♀️ Fantasy Cycling Stats Dashboard")

    # Display the header
    st.markdown(
        """
    Welcome to the Fantasy Cycling Stats Dashboard! This application provides insights into rider
    statistics.
    """
    )

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
        st.info("Please select a race to continue.")
        logger.warning("No race slected.")
        return

    progress_bar = st.progress(0.0, text="Loading data...")

    def display_loading_progress(progress: float, text: str) -> None:
        """Display loading progress in the sidebar."""
        logger.debug(f"Loading progress: {progress * 100:.2f}% - {text}")
        progress_bar.progress(progress, text=text)

    pipeline_config = PipelineConfig(
        {
            "race_key": selected_race_key,
            "use_cache": True,
            "force_refresh": False,
            "fuzzy_threshold": 0.9,
            "require_team_match": True,
            "include_debug_info": True,
            "verbose_logging": True,
            "use_enhanced_analytics": True,
            "include_comparisons": True,
            "calculate_trends": True,
            "parallel_processing": True,
        }
    )

    logger.info("Running data pipeline")

    result = run_pipeline(
        selected_race_key, config=pipeline_config, progress_callback=display_loading_progress
    )

    riders = result.get("riders_df", pd.DataFrame())
    summary = result.get("summary", {})
    race_data = result.get("raw_data", {}).get("race_data", {})
    warnings = result.get("warnings", None)
    errors = result.get("errors", None)

    # Display summary information
    # st.markdown("### Summary Statistics")
    # st.json(summary)

    if warnings:
        warning_notice = "⚠️ Warnings encountered during data loading:"
        for warning in warnings:
            warning_notice += f"\n- {warning}"
        st.warning(warning_notice)

    if errors:
        error_notice = "❌ Errors encountered during data loading:"
        for error in errors:
            error_notice += f"\n- {error}"
        st.error(error_notice)
        return

    # match_data = result.get("matched_data")
    # # st.json(match_data.get("race_data", pd.DataFrame()))
    # st.json(match_data.get("match_summary", pd.DataFrame()))
    # # st.json(match_data.get("riders", pd.DataFrame()))

    # return

    # Render the sidebar
    render_sidebar(selected_race_key)

    # Global filtering controls
    with st.expander("🔍 Global Filters", expanded=True):
        if not riders.empty:
            st.markdown("## 🔍 Global Filters")
            st.markdown("*These filters will apply across all tabs*")

            # Render unified controls for global filtering
            filters = render_unified_controls(riders, "global")

            # Apply filters globally
            filtered_riders = apply_filters(riders, filters)

            # Show filter results summary
            total_riders = len(riders)
            filtered_count = len(filtered_riders)

            if filtered_count != total_riders:
                st.info(f"🔍 Showing {filtered_count} of {total_riders} riders across all tabs")
            else:
                st.info(f"👥 Showing all {total_riders} riders")
        else:
            filtered_riders = riders.copy()

    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🏆 Riders", "📈 Analytics", "🏁 Race Data"])

    with tab1:
        show_overview_tab(filtered_riders)

    with tab2:
        show_riders_tab(filtered_riders)

    with tab3:
        show_analytics_tab(filtered_riders, race_data)

    with tab4:
        show_race_tab(race_data)

    # Footer
    st.divider()
    st.markdown(FOOTER_HTML, unsafe_allow_html=True)

    # Clear the progress bar
    progress_bar.empty()


if __name__ == "__main__":
    main()
