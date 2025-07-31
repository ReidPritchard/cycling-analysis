"""
Value analysis and outlier identification charts.
"""

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..analytics.outliers import identify_performance_outliers


def create_value_analysis_charts(df):
    """Create charts focused on value and outlier identification"""
    col1, col2 = st.columns(2)

    with col1:
        # Enhanced scatter plot with outlier highlighting
        create_outlier_scatter_plot(df)

    with col2:
        # Performance efficiency chart
        create_efficiency_chart(df)


def create_outlier_scatter_plot(df):
    """Create scatter plot highlighting overperformers and underperformers"""
    if len(df) == 0 or df["total_pcs_points"].sum() == 0:
        st.info("No performance data available for scatter plot")
        return

    # Get outliers
    overperformers, underperformers = identify_performance_outliers(df)

    # Create scatter plot
    fig = go.Figure()

    # Add all riders as base layer
    fig.add_trace(
        go.Scatter(
            x=df["stars"],
            y=df["total_pcs_points"],
            mode="markers",
            name="All Riders",
            marker=dict(size=8, color="lightgray", opacity=0.6),
            text=df["full_name"] + "<br>" + df["team"] + "<br>" + df["position"],
            hovertemplate="<b>%{text}</b><br>Stars: %{x}<br>PCS Points: %{y}<extra></extra>",
        )
    )

    # Highlight overperformers
    if len(overperformers) > 0:
        fig.add_trace(
            go.Scatter(
                x=overperformers["stars"],
                y=overperformers["total_pcs_points"],
                mode="markers",
                name="🚀 Overperformers",
                marker=dict(
                    size=12,
                    color="green",
                    symbol="star",
                    line=dict(width=2, color="darkgreen"),
                ),
                text=overperformers["full_name"]
                + "<br>"
                + overperformers["team"]
                + "<br>Z-score: "
                + overperformers["z_score"].round(2).astype(str),
                hovertemplate="<b>%{text}</b><br>Stars: %{x}<br>PCS Points: %{y}<extra></extra>",
            )
        )

    # Highlight underperformers
    if len(underperformers) > 0:
        fig.add_trace(
            go.Scatter(
                x=underperformers["stars"],
                y=underperformers["total_pcs_points"],
                mode="markers",
                name="📉 Underperformers",
                marker=dict(
                    size=12,
                    color="red",
                    symbol="x",
                    line=dict(width=2, color="darkred"),
                ),
                text=underperformers["full_name"]
                + "<br>"
                + underperformers["team"]
                + "<br>Z-score: "
                + underperformers["z_score"].round(2).astype(str),
                hovertemplate="<b>%{text}</b><br>Stars: %{x}<br>PCS Points: %{y}<extra></extra>",
            )
        )

    # Add trend line if we have enough data
    if len(df[df["total_pcs_points"] > 0]) > 5:
        x_data = df[df["total_pcs_points"] > 0]["stars"]
        y_data = df[df["total_pcs_points"] > 0]["total_pcs_points"]

        # Calculate trend line
        z = np.polyfit(x_data, y_data, 1)
        p = np.poly1d(z)

        fig.add_trace(
            go.Scatter(
                x=sorted(x_data),
                y=p(sorted(x_data)),
                mode="lines",
                name="Expected Performance",
                line=dict(dash="dash", color="orange", width=2),
            )
        )

    fig.update_layout(
        title="Performance vs Star Cost (Outliers Highlighted)",
        xaxis_title="Star Cost",
        yaxis_title="Total PCS Points",
        height=500,
        hovermode="closest",
    )

    st.plotly_chart(fig, use_container_width=True)


def create_efficiency_chart(df):
    """Create efficiency chart showing points per star by position"""
    if len(df) == 0 or df["total_pcs_points"].sum() == 0:
        st.info("No performance data available for efficiency chart")
        return

    # Calculate efficiency by position
    df_with_points = df[df["total_pcs_points"] > 0].copy()

    fig = px.box(
        df_with_points,
        x="position",
        y="pcs_per_star",
        color="position",
        title="Efficiency by Position (PCS Points per Star)",
        hover_data=["full_name", "team", "stars", "total_pcs_points"],
        points="outliers",  # Show outlier points
    )

    fig.update_layout(
        showlegend=False,
        height=500,
        xaxis_title="Rider Position/Style",
        yaxis_title="PCS Points per Star",
    )

    st.plotly_chart(fig, use_container_width=True)
