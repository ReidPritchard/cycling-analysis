"""
Overview charts and basic statistics visualizations.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


def create_stats_overview(df: pd.DataFrame) -> None:
    """Create an enhanced overview of key statistics with outlier insights"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Riders", len(df), help="Total number of fantasy riders")

    with col2:
        avg_stars = df["stars"].mean()
        st.metric(
            "Average Star Cost",
            f"{avg_stars:.1f}",
            help="Average star cost across all riders",
        )

    with col3:
        total_teams = df["team"].nunique()
        st.metric("Teams", total_teams, help="Number of unique teams")

    with col4:
        positions = df["position"].nunique()
        st.metric("Styles", positions, help="Number of different rider styles/positions")

    # Add performance insights
    if len(df) > 0 and df["total_pcs_points"].sum() > 0:
        st.divider()
        from ..analytics.insights import show_performance_insights

        show_performance_insights(df)


def create_star_cost_distribution_chart(df: pd.DataFrame) -> None:
    """Create an enhanced chart of the star cost distribution with performance overlay"""
    star_counts = df["stars"].value_counts().sort_index(ascending=False)

    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add bar chart for rider counts
    fig.add_trace(
        go.Bar(
            x=star_counts.index,
            y=star_counts.values,
            name="Rider Count",
            marker_color="lightblue",
            opacity=0.7,
        ),
        secondary_y=False,
    )

    # Add line chart for average performance by star cost
    if df["total_pcs_points"].sum() > 0:
        avg_performance = df.groupby("stars")["total_pcs_points"].mean()
        fig.add_trace(
            go.Scatter(
                x=avg_performance.index,
                y=avg_performance.values,
                mode="lines+markers",
                name="Avg PCS Points",
                line=dict(color="red", width=3),
                marker=dict(size=8),
            ),
            secondary_y=True,
        )

    # Update layout
    fig.update_xaxes(title_text="Star Cost")
    fig.update_yaxes(title_text="Number of Riders", secondary_y=False)
    fig.update_yaxes(title_text="Average PCS Points", secondary_y=True)
    fig.update_layout(title="Star Cost Distribution vs Performance", height=400, showlegend=True)

    st.plotly_chart(fig, use_container_width=True)
