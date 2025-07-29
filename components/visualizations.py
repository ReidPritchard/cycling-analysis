"""
Data visualization components for the Fantasy Cycling Stats app.
"""

import streamlit as st
import plotly.express as px
import pandas as pd


def create_stats_overview(df):
    """Create an overview of key statistics"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Riders", len(df), help="Total number of fantasy riders")

    with col2:
        avg_stars = df["stars"].mean()
        st.metric(
            "Average Star Cost",
            f"{avg_stars:.1f}",
            help="Average star rating across all riders",
        )

    with col3:
        total_teams = df["team"].nunique()
        st.metric("Teams", total_teams, help="Number of unique teams")

    with col4:
        positions = df["position"].nunique()
        st.metric(
            "Styles", positions, help="Number of different rider styles/positions"
        )


def create_star_cost_distribution_chart(df):
    """Create a chart of the star cost distribution"""
    star_counts = df["stars"].value_counts().sort_index(ascending=False)

    fig = px.bar(
        star_counts,
        x=star_counts.index,
        y=star_counts.values,
        labels={"x": "Star Cost", "y": "Number of Riders"},
    )

    st.plotly_chart(fig, use_container_width=True)


def create_visualizations(df):
    """Create interactive charts for the data"""
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Stars Distribution by Position")
        fig = px.box(
            df,
            x="position",
            y="stars",
            color="position",
            title="Star Rating Distribution by Position",
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

        # Graph to highlight
        st.subheader("📈 UCI Points Distribution by Star Cost")
        fig = px.scatter(
            df.sort_values("stars"),
            x="stars",
            y="total_uci_points",
            hover_data=["full_name", "team", "position", "uci_per_star"],
            title="UCI Points Distribution by Star Cost",
            color="position",
            trendline="ols",
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🏆 Top Teams by Average Stars")
        team_stats = df.groupby("team")["stars"].agg(["mean", "count"]).reset_index()
        team_stats = team_stats[team_stats["count"] >= 2]  # Only teams with 2+ riders
        team_stats = team_stats.sort_values("mean", ascending=False).head(10)

        fig = px.bar(
            team_stats,
            x="mean",
            y="team",
            orientation="h",
            title="Top Teams by Average Star Rating",
            labels={"mean": "Average Stars", "team": "Team"},
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


def show_detailed_analytics(filtered_riders):
    """Show detailed analytics section"""
    if len(filtered_riders) > 0:
        create_visualizations(filtered_riders)

        # Additional analytics
        st.subheader("📊 Detailed Analytics")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Top 10 Highest Rated Riders**")
            top_riders = filtered_riders.nlargest(10, "stars")[
                ["full_name", "stars", "position"]
            ]
            st.dataframe(top_riders, use_container_width=True)

        with col2:
            st.write("**Team Statistics**")
            team_stats = (
                filtered_riders.groupby("team")
                .agg({"stars": ["count", "mean", "max"], "full_name": "count"})
                .round(2)
            )
            team_stats.columns = ["Rider Count", "Avg Stars", "Max Stars", "Total"]
            team_stats = team_stats.sort_values("Avg Stars", ascending=False)
            st.dataframe(team_stats, use_container_width=True)
    else:
        st.info("No riders match the current filters. Please adjust your selection.")
