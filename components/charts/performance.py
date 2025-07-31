"""
Performance distribution and analysis charts.
"""

import pandas as pd
import plotly.express as px
import streamlit as st


def create_performance_distribution_charts(df: pd.DataFrame) -> None:
    """Create charts showing performance distributions"""
    col1, col2 = st.columns(2)

    with col1:
        # Stars distribution by position
        fig = px.violin(
            df,
            x="position",
            y="stars",
            color="position",
            title="Star Cost Distribution by Position",
            hover_data=["full_name", "team"],
            box=True,
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Performance tiers visualization
        if df["total_pcs_points"].sum() > 0:
            create_performance_tiers_chart(df)
        else:
            st.info("No performance data available")


def create_performance_tiers_chart(df: pd.DataFrame) -> None:
    """Create a clearer performance visualization using tiers and rankings"""
    df_with_points = df[df["total_pcs_points"] > 0].copy()

    if len(df_with_points) == 0:
        st.info("No performance data available")
        return

    # Calculate performance tiers based on quartiles
    points_data = df_with_points["total_pcs_points"]
    q25 = points_data.quantile(0.25)
    q50 = points_data.quantile(0.50)  # median
    q75 = points_data.quantile(0.75)

    # Assign performance tiers
    def assign_tier(points: float) -> str:
        if points >= q75:
            return "Elite (Top 25%)"
        elif points >= q50:
            return "Strong (25-50%)"
        elif points >= q25:
            return "Average (50-75%)"
        else:
            return "Struggling (Bottom 25%)"

    df_with_points["performance_tier"] = df_with_points["total_pcs_points"].apply(
        assign_tier
    )

    # Create a stacked bar chart showing position distribution within each tier
    tier_position_counts = (
        df_with_points.groupby(["performance_tier", "position"])
        .size()
        .reset_index(name="count")
    )

    # Define tier order for proper display
    tier_order = [
        "Elite (Top 25%)",
        "Strong (25-50%)",
        "Average (50-75%)",
        "Struggling (Bottom 25%)",
    ]
    tier_position_counts["performance_tier"] = pd.Categorical(
        tier_position_counts["performance_tier"], categories=tier_order, ordered=True
    )
    tier_position_counts = tier_position_counts.sort_values("performance_tier")

    # Create the visualization
    fig = px.bar(
        tier_position_counts,
        x="performance_tier",
        y="count",
        color="position",
        title="Performance Tiers of Rider's with Points by Position",
        labels={
            "performance_tier": "Performance Tier",
            "count": "Number of Riders",
            "position": "Rider Position",
        },
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    # Add tier threshold annotations
    fig.add_hline(
        y=0,
        annotation_text=f"Thresholds: Elite ≥{q75:.0f} | Strong ≥{q50:.0f} | Average ≥{q25:.0f} pts",
        annotation_position="top right",
        line_width=0,
    )

    fig.update_layout(
        height=400,
        xaxis_tickangle=-45,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Add summary stats below the chart
    col1, col2, col3, col4 = st.columns(4)

    tier_counts = df_with_points["performance_tier"].value_counts()

    with col1:
        elite_count = tier_counts.get("Elite (Top 25%)", 0)
        st.metric("🏆 Elite", elite_count, help=f"≥{q75:.0f} PCS points")

    with col2:
        strong_count = tier_counts.get("Strong (25-50%)", 0)
        st.metric("💪 Strong", strong_count, help=f"{q50:.0f}-{q75:.0f} PCS points")

    with col3:
        average_count = tier_counts.get("Average (50-75%)", 0)
        st.metric("📊 Average", average_count, help=f"{q25:.0f}-{q50:.0f} PCS points")

    with col4:
        struggling_count = tier_counts.get("Struggling (Bottom 25%)", 0)
        st.metric("📉 Struggling", struggling_count, help=f"<{q25:.0f} PCS points")
