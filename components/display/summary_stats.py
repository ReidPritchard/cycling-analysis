"""
Summary statistics display components.
"""

import streamlit as st


def display_summary_stats(df):
    """Display enhanced summary statistics for the rider data."""
    if df.empty:
        st.warning("No data available for summary statistics.")
        return

    st.markdown("### 📊 Summary Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Riders", len(df), help="Total number of riders in the dataset")
        if "stars" in df.columns:
            avg_stars = df["stars"].mean()
            st.metric(
                "Avg Stars",
                f"{avg_stars:.1f}",
                help="Average fantasy star cost across all riders",
            )

    with col2:
        if "total_pcs_points" in df.columns:
            total_pcs = df["total_pcs_points"].sum()
            st.metric(
                "Total PCS Points",
                f"{total_pcs:,}",
                help="Sum of all PCS points earned by riders",
            )
            if len(df) > 0:
                st.metric(
                    "Avg PCS/Rider",
                    f"{total_pcs / len(df):.1f}",
                    help="Average PCS points per rider",
                )

    with col3:
        if "total_uci_points" in df.columns:
            total_uci = df["total_uci_points"].sum()
            st.metric(
                "Total UCI Points",
                f"{total_uci:,}",
                help="Sum of all UCI points earned by riders",
            )
            if len(df) > 0:
                st.metric(
                    "Avg UCI/Rider",
                    f"{total_uci / len(df):.1f}",
                    help="Average UCI points per rider",
                )

    with col4:
        if "total_pcs_points" in df.columns:
            riders_with_points = len(df[df["total_pcs_points"] > 0])
            st.metric(
                "Riders with Points",
                riders_with_points,
                help="Number of riders who have earned points this season",
            )
            if len(df) > 0:
                percentage = riders_with_points / len(df) * 100
                st.metric(
                    "% with Points",
                    f"{percentage:.1f}%",
                    help="Percentage of riders who have earned points",
                )
