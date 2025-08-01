"""
Analysis of stage performance data.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from data.models.race import RaceData


def create_stage_performance_charts(df: pd.DataFrame, race_data: RaceData) -> None:
    """Create stage performance analysis charts"""
    st.subheader("🏁 Stage Performance Analysis")

    # Get completed stages with results
    stages = race_data.get("stages", [])
    completed_stages = [s for s in stages if s.get("results") is not None]

    if not completed_stages:
        st.info("📅 No completed stages with results yet. Check back after race stages finish!")
        return

    st.markdown(f"📊 Analysis based on **{len(completed_stages)}** completed stages")

    # Stage overview metrics
    _show_stage_overview_metrics(completed_stages)

    # Stage performance charts
    col1, col2 = st.columns(2)

    with col1:
        _create_stage_difficulty_vs_speed_chart(completed_stages)

    with col2:
        _create_stage_profile_distribution_chart(completed_stages)

    # Stage winners analysis
    _create_stage_winners_analysis(completed_stages, df)

    # # Fantasy performance insights
    # _create_fantasy_performance_insights(completed_stages, df)


def _show_stage_overview_metrics(completed_stages: list) -> None:
    """Display key metrics for completed stages"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_distance = sum(float(s.get("distance", 0)) for s in completed_stages) / len(
            completed_stages
        )
        st.metric("Avg Distance", f"{avg_distance:.1f} km")

    with col2:
        avg_speed = sum(s.get("avg_speed_winner", 0) or 0 for s in completed_stages) / len(
            completed_stages
        )
        st.metric("Avg Winner Speed", f"{avg_speed:.1f} km/h")

    with col3:
        total_elevation = sum(s.get("vertical_meters", 0) or 0 for s in completed_stages)
        st.metric("Total Elevation", f"{total_elevation:,}m")

    with col4:
        profile_types = [s.get("profile_icon", "p1") for s in completed_stages]
        mountain_stages = len([p for p in profile_types if p in ["p4", "p5"]])
        st.metric("Mountain Stages", mountain_stages)


def _create_stage_difficulty_vs_speed_chart(completed_stages: list) -> None:
    """Create scatter plot of stage difficulty vs winner speed"""
    st.markdown("#### Stage Difficulty vs Speed")

    # Prepare data
    stage_data = []
    profile_names = {
        "p1": "Flat",
        "p2": "Rolling",
        "p3": "Hilly",
        "p4": "Mountain",
        "p5": "High Mountain",
    }

    for i, stage in enumerate(completed_stages, 1):
        stage_data.append(
            {
                "stage": f"Stage {i}",
                "distance": float(stage.get("distance", 0)),
                "elevation": stage.get("vertical_meters", 0) or 0,
                "speed": stage.get("avg_speed_winner", 0) or 0,
                "profile": profile_names.get(stage.get("profile_icon", "p1"), "Unknown"),
                "route": f"{stage.get('departure', '')} → {stage.get('arrival', '')}",
            }
        )

    if stage_data:
        stage_df = pd.DataFrame(stage_data)

        fig = px.scatter(
            stage_df,
            x="elevation",
            y="speed",
            size="distance",
            color="profile",
            hover_name="stage",
            hover_data={"route": True, "distance": ":.1f"},
            title="Elevation vs Winner Speed (size = distance)",
            labels={
                "elevation": "Elevation Gain (m)",
                "speed": "Winner Avg Speed (km/h)",
                "profile": "Stage Profile",
            },
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


def _create_stage_profile_distribution_chart(completed_stages: list) -> None:
    """Create pie chart of stage profile distribution"""
    st.markdown("#### Stage Profile Distribution")

    profile_names = {
        "p1": "🏃 Flat",
        "p2": "🚴 Rolling",
        "p3": "🏔️ Hilly",
        "p4": "⛰️ Mountain",
        "p5": "🗻 High Mountain",
    }

    profile_counts = {}
    for stage in completed_stages:
        profile = stage.get("profile_icon", "p1")
        profile_name = profile_names.get(profile, "Unknown")
        profile_counts[profile_name] = profile_counts.get(profile_name, 0) + 1

    if profile_counts:
        fig = px.pie(
            values=list(profile_counts.values()),
            names=list(profile_counts.keys()),
            title="Completed Stages by Profile Type",
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


def _create_stage_winners_analysis(completed_stages: list, df: pd.DataFrame) -> None:
    """Analyze stage winners and their characteristics"""
    st.markdown("#### 🏆 Stage Winners Analysis")

    winners_data = []
    for i, stage in enumerate(completed_stages, 1):
        results = stage.get("results", [])
        if results:
            winner = results[0]  # First result is the winner
            winners_data.append(
                {
                    "stage": f"Stage {i}",
                    "rider_name": winner.get("rider_name", "Unknown"),
                    "team_name": winner.get("team_name", "Unknown"),
                    "nationality": winner.get("nationality", "Unknown"),
                    "age": winner.get("age", 0),
                    "pcs_points": winner.get("pcs_points", 0),
                    "profile": stage.get("profile_icon", "p1"),
                    "route": f"{stage.get('departure', '')} → {stage.get('arrival', '')}",
                }
            )

    if winners_data:
        winners_df = pd.DataFrame(winners_data)

        col1, col2 = st.columns(2)

        with col1:
            # Team wins distribution
            team_wins = winners_df["team_name"].value_counts()
            fig = px.bar(
                x=team_wins.values,
                y=team_wins.index,
                orientation="h",
                title="Stage Wins by Team",
                labels={"x": "Number of Wins", "y": "Team"},
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Winner age distribution
            fig = px.histogram(
                winners_df,
                x="age",
                title="Age Distribution of Stage Winners",
                nbins=10,
                labels={"age": "Age", "count": "Number of Wins"},
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        # Winners table
        st.markdown("##### Stage Winners Summary")
        display_columns = ["stage", "rider_name", "team_name", "nationality", "age", "pcs_points"]
        st.dataframe(winners_df[display_columns], hide_index=True)


def _create_fantasy_performance_insights(completed_stages: list, df: pd.DataFrame) -> None:
    """Analyze fantasy performance based on stage results"""
    st.markdown("#### 💰 Fantasy Performance Insights")

    # Extract all riders from completed stage results
    all_stage_riders = []
    for i, stage in enumerate(completed_stages, 1):
        results = stage.get("results", [])
        profile = stage.get("profile_icon", "p1")

        for result in results:
            rider_name = result.get("rider_name", "")
            # Try to match with fantasy riders
            fantasy_match = None
            for _, fantasy_rider in df.iterrows():
                if (
                    rider_name.lower() in fantasy_rider["full_name"].lower()
                    or fantasy_rider["full_name"].lower() in rider_name.lower()
                ):
                    fantasy_match = fantasy_rider
                    break

            all_stage_riders.append(
                {
                    "stage": f"Stage {i}",
                    "rider_name": rider_name,
                    "rank": result.get("rank", 999),
                    "pcs_points": result.get("pcs_points", 0),
                    "profile": profile,
                    "fantasy_stars": fantasy_match["stars"] if fantasy_match is not None else None,
                    "fantasy_position": fantasy_match["position"]
                    if fantasy_match is not None
                    else None,
                    "fantasy_team": fantasy_match["team"] if fantasy_match is not None else None,
                }
            )

    if all_stage_riders:
        stage_riders_df = pd.DataFrame(all_stage_riders)
        fantasy_riders = stage_riders_df[stage_riders_df["fantasy_stars"].notna()]

        if not fantasy_riders.empty:
            col1, col2 = st.columns(2)

            with col1:
                # Performance by star rating
                star_performance = (
                    fantasy_riders.groupby("fantasy_stars")
                    .agg({"pcs_points": ["mean", "sum", "count"], "rank": "mean"})
                    .round(2)
                )
                star_performance.columns = [
                    "Avg PCS Points",
                    "Total PCS Points",
                    "Stage Appearances",
                    "Avg Rank",
                ]

                fig = px.bar(
                    x=star_performance.index,
                    y=star_performance["Avg PCS Points"],
                    title="Average PCS Points by Fantasy Star Rating",
                    labels={"x": "Fantasy Stars", "y": "Average PCS Points"},
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Performance by position type and stage profile
                position_profile_perf = (
                    fantasy_riders.groupby(["fantasy_position", "profile"])
                    .agg({"pcs_points": "mean", "rank": "mean"})
                    .round(2)
                )

                if not position_profile_perf.empty:
                    fig = px.bar(
                        position_profile_perf.reset_index(),
                        x="fantasy_position",
                        y="pcs_points",
                        color="profile",
                        title="Performance by Position Type and Stage Profile",
                        labels={
                            "pcs_points": "Avg PCS Points",
                            "fantasy_position": "Fantasy Position",
                        },
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # Top fantasy performers summary
            st.markdown("##### 🌟 Top Fantasy Performers")
            top_performers = (
                fantasy_riders.groupby(["rider_name", "fantasy_stars", "fantasy_position"])
                .agg({"pcs_points": "sum", "rank": "mean", "stage": "count"})
                .round(2)
            )
            top_performers.columns = ["Total PCS Points", "Avg Rank", "Stages"]
            top_performers = top_performers.sort_values("Total PCS Points", ascending=False).head(
                10
            )

            st.dataframe(top_performers, use_container_width=True)
        else:
            st.info("No fantasy riders found in completed stage results yet.")
    else:
        st.info("No stage results available for analysis.")
