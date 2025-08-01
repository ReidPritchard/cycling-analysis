"""
Main analytics orchestration and display.
"""

import pandas as pd
import streamlit as st

from data.models.race import RaceData

from ..charts.performance import create_performance_distribution_charts
from ..charts.stage_performance import create_stage_performance_charts
from ..charts.team_analysis import create_team_analysis_charts
from ..charts.value_analysis import create_value_analysis_charts
from .insights import show_outlier_analysis, show_statistical_insights


def create_visualizations(df: pd.DataFrame) -> None:
    """Create reorganized interactive charts with outlier highlighting"""

    # Section 1: Value Analysis - Most Important Charts
    st.subheader("💰 Value Analysis")
    create_value_analysis_charts(df)

    st.divider()

    # Section 2: Performance Distribution
    st.subheader("📊 Performance Distribution")
    create_performance_distribution_charts(df)

    st.divider()

    # Section 3: Team Analysis
    st.subheader("🏆 Team Analysis")
    create_team_analysis_charts(df)


def show_detailed_analytics(filtered_riders: pd.DataFrame, race_data: RaceData) -> None:
    """Show enhanced detailed analytics section"""
    if len(filtered_riders) > 0:
        create_visualizations(filtered_riders)

        # Section 4: Stage Performance
        st.subheader("🚴 Stage Performance")
        st.markdown("""
        Analyze how riders perform across different stage types and conditions.
        Which riders excel in mountain stages, flat sprints, or time trials?
        This section provides insights into rider adaptability and specialization.
        """)
        create_stage_performance_charts(filtered_riders, race_data)

        # Outlier Analysis Section
        st.subheader("🎯 Outlier Analysis")
        show_outlier_analysis(filtered_riders)

        st.divider()

        # Statistical Summary
        st.subheader("📊 Statistical Insights")
        show_statistical_insights(filtered_riders)

    else:
        st.info("No riders match the current filters. Please adjust your selection.")
