"""
Performance and results display components.
"""

import pandas as pd
import streamlit as st

from ..common.calculations import (
    get_consistency_interpretation,
    get_trend_interpretation,
)


def render_season_results(rider):
    """Render season results table with better organization."""
    # st.dataframe(rider, use_container_width=True, hide_index=True)
    # return

    pcs_data = rider.get("pcs_data", {})
    if not pcs_data or "error" in pcs_data:
        st.info("🔍 No PCS data available - rider may not be in startlist")
        return

    season_results = rider.get("season_results", pd.DataFrame())

    if season_results.empty:
        st.info("📊 No recent season results available")
        return

    # Show results count and context
    results_count = len(season_results)
    st.markdown(f"**Recent Results** ({results_count} race{'s' if results_count != 1 else ''})")

    st.dataframe(
        season_results,
        column_order=[
            "Date",
            "Name",
            "Result",
            "GC Position",
            "PCS Points",
            "UCI Points",
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date": st.column_config.DateColumn("Date", width="small", help="Race date"),
            "Name": st.column_config.TextColumn(
                "Race", pinned=True, width="medium", help="Race name"
            ),
            "Result": st.column_config.NumberColumn(
                "Finish", width="small", help="Stage finish position"
            ),
            "GC Position": st.column_config.NumberColumn(
                "GC", width="small", help="General Classification position"
            ),
            "PCS Points": st.column_config.NumberColumn(
                "PCS", width="small", help="ProCyclingStats points earned"
            ),
            "UCI Points": st.column_config.NumberColumn(
                "UCI", width="small", help="UCI WorldTour points earned"
            ),
        },
    )


def render_compact_performance_summary(rider):
    """Render performance data in a compact, organized format."""
    total_pcs = rider.get("total_pcs_points", 0)
    total_uci = rider.get("total_uci_points", 0)
    consistency_score = rider.get("consistency_score", 0.0)
    trend_score = rider.get("trend_score", 0.0)

    # Only show section if there's meaningful data
    if total_pcs == 0 and total_uci == 0 and consistency_score == 0 and trend_score == 0:
        st.caption("📊 No performance data available")
        return

    st.markdown("**Performance Summary**")

    # Compact points display in columns
    if total_pcs > 0 or total_uci > 0:
        col1, col2 = st.columns(2)

        with col1:
            if total_pcs > 0:
                st.caption(f"🏆 **PCS:** {total_pcs} pts")

        with col2:
            if total_uci > 0:
                st.caption(f"🌍 **UCI:** {total_uci} pts")

    # Compact analysis display
    analysis_items = []

    if consistency_score > 0:
        consistency_label, _, _ = get_consistency_interpretation(consistency_score)
        analysis_items.append(f"📊 **Consistency:** {consistency_label} ({consistency_score:.2f})")

    if trend_score != 0.0:
        trend_label, _, trend_icon, _ = get_trend_interpretation(trend_score)
        analysis_items.append(f"{trend_icon} **Trend:** {trend_label} ({-trend_score:.3f})")

    # Display analysis items compactly
    for item in analysis_items:
        st.caption(item)
