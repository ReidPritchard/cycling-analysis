"""
Team-focused analysis and comparison charts.
"""

import pandas as pd
import plotly.express as px
import streamlit as st


def create_team_analysis_charts(df: pd.DataFrame) -> None:
    """Create team-focused analysis charts"""
    col1, col2 = st.columns(2)

    with col1:
        # Team efficiency
        if df["total_pcs_points"].sum() > 0:
            team_stats = (
                df.groupby("team")
                .agg({"total_pcs_points": "sum", "stars": "sum", "full_name": "count"})
                .reset_index()
            )
            team_stats = team_stats[
                team_stats["full_name"] >= 2
            ]  # Teams with 2+ riders
            team_stats["team_efficiency"] = (
                team_stats["total_pcs_points"] / team_stats["stars"]
            )
            team_stats = team_stats.sort_values(
                "team_efficiency", ascending=False
            ).head(10)

            fig = px.bar(
                team_stats,
                x="team_efficiency",
                y="team",
                orientation="h",
                title="Most Efficient Teams (Points per Star)",
                labels={"team_efficiency": "PCS Points per Star", "team": "Team"},
                color="team_efficiency",
                color_continuous_scale="viridis",
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance data available for team efficiency")

    with col2:
        # Team depth analysis - showing impact of rider dropouts
        team_overview = (
            df.groupby("team")
            .agg(
                {
                    "stars": ["mean", "sum"],
                    "full_name": "count",
                    "total_pcs_points": "sum",
                }
            )
            .reset_index()
        )
        team_overview.columns = [
            "team",
            "avg_stars",
            "total_stars",
            "rider_count",
            "total_points",
        ]
        team_overview = team_overview[team_overview["rider_count"] >= 2]

        # Calculate dropouts (assuming teams start with 7 riders)
        team_overview["dropouts"] = 7 - team_overview["rider_count"]
        team_overview["roster_strength"] = (
            team_overview["rider_count"] / 7
        )  # Percentage of original roster

        # Create color mapping based on dropout severity
        team_overview["dropout_category"] = team_overview["dropouts"].apply(
            lambda x: "No Dropouts" if x == 0 else f"{x} Dropout{'s' if x > 1 else ''}"
        )

        fig = px.scatter(
            team_overview,
            x="avg_stars",
            y="total_points" if df["total_pcs_points"].sum() > 0 else "total_stars",
            color="dropout_category",
            hover_name="team",
            hover_data={
                "dropouts": True,
                "rider_count": True,
                "roster_strength": ":.1%",
            },
            title="Team Depth Analysis (Impact of Dropouts)",
            labels={
                "avg_stars": "Average Star Cost per Rider",
                "total_points": (
                    "Total PCS Points"
                    if df["total_pcs_points"].sum() > 0
                    else "Total Stars"
                ),
                "rider_count": "Current Roster Size",
                "dropout_category": "Dropout Status",
            },
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig, use_container_width=True)
