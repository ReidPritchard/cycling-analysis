"""
Statistical insights and performance analysis.
"""

import pandas as pd
import streamlit as st
from .outliers import identify_performance_outliers, identify_value_picks


def show_performance_insights(df):
    """Show key performance insights and outliers"""
    col1, col2, col3 = st.columns(3)

    # Calculate outliers
    overperformers, underperformers = identify_performance_outliers(df)
    value_picks = identify_value_picks(df)

    with col1:
        if len(overperformers) > 0:
            st.metric(
                "🚀 Overperformers",
                len(overperformers),
                help="Riders performing significantly better than expected for their star cost",
            )
        else:
            st.metric("🚀 Overperformers", "0")

    with col2:
        if len(underperformers) > 0:
            st.metric(
                "📉 Underperformers",
                len(underperformers),
                help="Riders performing significantly worse than expected for their star cost",
            )
        else:
            st.metric("📉 Underperformers", "0")

    with col3:
        if len(value_picks) > 0:
            st.metric(
                "💎 Value Picks",
                len(value_picks),
                help="High-performing riders with low star costs",
            )
        else:
            st.metric("💎 Value Picks", "0")


def show_outlier_analysis(df):
    """Show detailed outlier analysis with actionable insights"""
    col1, col2, col3 = st.columns(3)

    # Get outliers and value picks
    overperformers, underperformers = identify_performance_outliers(df)
    value_picks = identify_value_picks(df)

    with col1:
        st.write("**🚀 Top Overperformers**")
        if len(overperformers) > 0:
            display_df = overperformers.nlargest(5, "z_score")[
                ["full_name", "stars", "total_pcs_points", "z_score"]
            ].copy()
            display_df.columns = ["Rider", "Stars", "PCS Points", "Z-Score"]
            display_df["Z-Score"] = display_df["Z-Score"].round(2)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No significant overperformers identified")

    with col2:
        st.write("**📉 Top Underperformers**")
        if len(underperformers) > 0:
            display_df = underperformers.nsmallest(5, "z_score")[
                ["full_name", "stars", "total_pcs_points", "z_score"]
            ].copy()
            display_df.columns = ["Rider", "Stars", "PCS Points", "Z-Score"]
            display_df["Z-Score"] = display_df["Z-Score"].round(2)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No significant underperformers identified")

    with col3:
        st.write("**💎 Best Value Picks**")
        if len(value_picks) > 0:
            display_df = value_picks[
                ["full_name", "stars", "total_pcs_points", "value_score"]
            ].copy()
            display_df.columns = ["Rider", "Stars", "PCS Points", "Value Score"]
            display_df["Value Score"] = display_df["Value Score"].round(2)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No value picks identified")


def show_statistical_insights(df):
    """Show statistical insights and correlations"""
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Performance Statistics**")
        if df["total_pcs_points"].sum() > 0:
            stats_data = {
                "Metric": [
                    "Total Riders with Points",
                    "Average PCS Points",
                    "Median PCS Points",
                    "Standard Deviation",
                    "Best Performance",
                    "Points per Star (Avg)",
                ],
                "Value": [
                    len(df[df["total_pcs_points"] > 0]),
                    f"{df[df['total_pcs_points'] > 0]['total_pcs_points'].mean():.1f}",
                    f"{df[df['total_pcs_points'] > 0]['total_pcs_points'].median():.1f}",
                    f"{df[df['total_pcs_points'] > 0]['total_pcs_points'].std():.1f}",
                    f"{df['total_pcs_points'].max():.0f} - ({df[df['total_pcs_points'] == df['total_pcs_points'].max()]['full_name'].values[0]})",
                    f"{df[df['total_pcs_points'] > 0]['pcs_per_star'].mean():.2f}",
                ],
            }
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        else:
            st.info("No performance data available")

    with col2:
        st.write("**Position Analysis**")
        if df["total_pcs_points"].sum() > 0:
            position_stats = (
                df[df["total_pcs_points"] > 0]
                .groupby("position")
                .agg(
                    {
                        "total_pcs_points": ["count", "mean", "std"],
                        "pcs_per_star": "mean",
                    }
                )
                .round(2)
            )

            position_stats.columns = ["Count", "Avg Points", "Std Dev", "Efficiency"]
            position_stats = position_stats.sort_values("Efficiency", ascending=False)
            st.dataframe(position_stats, use_container_width=True)
        else:
            st.info("No performance data available")
