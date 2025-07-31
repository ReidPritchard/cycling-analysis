"""
Analysis of stage performance data.
"""

import plotly.express as px
import streamlit as st


def create_stage_performance_charts(df):
    """Create stage performance analysis charts"""
    st.subheader("🚴 Stage Performance Analysis")

    # Stage Type Performance
    stage_type_performance = (
        df.groupby("stage_type")
        .agg({"total_pcs_points": "sum", "full_name": "count"})
        .reset_index()
    )
    stage_type_performance = stage_type_performance.sort_values(
        "total_pcs_points", ascending=False
    )

    fig = px.bar(
        stage_type_performance,
        x="stage_type",
        y="total_pcs_points",
        title="Total PCS Points by Stage Type",
        labels={"total_pcs_points": "Total PCS Points", "stage_type": "Stage Type"},
        color="total_pcs_points",
        color_continuous_scale="Blues",
    )
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Rider Performance by Stage Type
    rider_stage_performance = (
        df.groupby(["full_name", "stage_type"]).agg({"total_pcs_points": "sum"}).reset_index()
    )

    fig = px.bar(
        rider_stage_performance,
        x="full_name",
        y="total_pcs_points",
        color="stage_type",
        title="Rider Performance by Stage Type",
        labels={"total_pcs_points": "Total PCS Points", "full_name": "Rider"},
        barmode="group",
    )
    fig.update_layout(height=400, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
