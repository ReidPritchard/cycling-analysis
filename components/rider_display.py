"""
Refactored rider display components for the Fantasy Cycling Stats app.
"""

import re
import pandas as pd
import streamlit as st
from config.settings import POSITION_ICONS


# =============================================================================
# DISPLAY HELPER FUNCTIONS
# =============================================================================


def emoji_flag(country_code):
    cc = country_code.upper()
    if not re.match(r"^[A-Z]{2}$", cc):
        return ""

    return "".join(chr(c + 127397) for c in cc.encode("utf-8"))


def render_rider_info(rider):
    """Render basic rider information and demographics."""
    st.markdown(f"### {rider['full_name']} ({int(rider['stars'])} ⭐)")

    # Position with icon
    icon = POSITION_ICONS.get(rider["position"], "🚴")
    st.markdown(f"{icon} {rider['position']}")
    st.markdown(f"🏢 {rider['team']}")

    # Demographics
    if rider.get("age"):
        st.caption(
            f"**Age:** {rider['age']} | Birthdate: {rider.get('birthdate', 'N/A')}"
        )

    if rider.get("nationality"):
        st.caption(
            f"**Nationality:** {emoji_flag(rider['nationality'])} {rider['nationality']}"
        )

    if rider.get("birthplace"):
        st.caption(f"**Birthplace:** {rider['birthplace']}")

    if rider.get("weight_kg"):
        st.caption(
            f"**Weight:** {rider['weight_kg']} kg | {rider['weight_lbs']:.1f} lbs"
        )

    if rider.get("height_m"):
        st.caption(f"**Height:** {rider['height_m']} m | {rider['height_ft']:.1f} ft")


def render_season_results(rider):
    """Render season results table."""
    st.markdown("**Season Results**")

    pcs_data = rider.get("pcs_data", {})
    if not pcs_data or "error" in pcs_data:
        st.markdown("No PCS data available")
        return

    season_results = rider.get("season_results", pd.DataFrame())

    if season_results.empty:
        st.markdown("No season results available")
        return

    st.dataframe(
        season_results,
        column_order=[
            "Date",
            "Name",
            "Result",
            "GC Position",
            "PCS Points",
            "UCI Points",
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date": st.column_config.DateColumn("Date", width="small"),
            "Name": st.column_config.TextColumn("Name", pinned=True, width="medium"),
            "Result": st.column_config.NumberColumn("Result", width="small"),
            "GC Position": st.column_config.NumberColumn("GC Position", width="small"),
            "PCS Points": st.column_config.NumberColumn("PCS Points", width="small"),
            "UCI Points": st.column_config.NumberColumn("UCI Points", width="small"),
        },
    )


def render_rider_totals(rider):
    """Render calculated totals and ratios."""
    total_pcs = rider.get("total_pcs_points", 0)
    total_uci = rider.get("total_uci_points", 0)

    pcs_per_star = rider.get("pcs_per_star", 0)
    uci_per_star = rider.get("uci_per_star", 0)

    if total_pcs > 0 or total_uci > 0:
        st.markdown("#### Totals")

        if total_pcs > 0:
            st.markdown(f" - PCS Points: {total_pcs}")
            st.markdown(f" - **PCS/Star Cost:** {pcs_per_star:.2f}")

        if total_uci > 0:
            st.markdown(f" - UCI Points: {total_uci}")
            st.markdown(f" - **UCI/Star Cost:** {uci_per_star:.2f}")
    else:
        st.markdown("No points data available")


def render_single_rider_card(rider):
    """Render a single rider card."""
    with st.container():
        info_col, season_stats_col, totals_col = st.columns([2, 3, 1])

        with info_col:
            render_rider_info(rider)

        with season_stats_col:
            render_season_results(rider)

        with totals_col:
            render_rider_totals(rider)

        st.divider()


# =============================================================================
# MAIN DISPLAY FUNCTIONS
# =============================================================================


def get_sort_options():
    """Get available sorting options."""
    return {
        "Stars": "stars",
        "Total PCS Points": "total_pcs_points",
        "Total UCI Points": "total_uci_points",
        "PCS Points per Star": "pcs_per_star",
        "UCI Points per Star": "uci_per_star",
        "Age": "age",
        "Season Results Count": "season_results_count",
        "Full Name": "full_name",
        "Team": "team",
        "Position": "position",
    }


def display_rider_cards(df):
    """Display riders in card format with enhanced sorting."""
    # Prepare data with calculated fields
    df_prepared = df

    # Enhanced sorting selector
    sort_options = get_sort_options()
    sort_by_label = st.selectbox("Sort by", list(sort_options.keys()))
    sort_by_column = sort_options[sort_by_label]

    # Sort order selector
    ascending = st.checkbox("Sort ascending", value=False)

    # Sort the dataframe
    df_sorted = df_prepared.sort_values(sort_by_column, ascending=ascending)

    # Display cards
    for _, rider in df_sorted.iterrows():
        render_single_rider_card(rider)


def display_rider_table(df):
    """Display riders in enhanced table format with calculated fields."""
    # Prepare data with calculated fields
    df_prepared = df

    # Enhanced sorting selector
    sort_options = get_sort_options()
    sort_by_label = st.selectbox("Sort by", list(sort_options.keys()), key="table_sort")
    sort_by_column = sort_options[sort_by_label]

    # Sort order selector
    ascending = st.checkbox("Sort ascending", value=False, key="table_ascending")

    # Sort the dataframe
    df_sorted = df_prepared.sort_values(sort_by_column, ascending=ascending)

    # Select columns for display
    display_columns = [
        "fantasy_name",
        "full_name",
        "team",
        "position",
        "stars",
        "total_pcs_points",
        "total_uci_points",
        "pcs_per_star",
        "uci_per_star",
        "age",
        "nationality",
        "season_results_count",
    ]

    # Create display dataframe
    display_df = df_sorted[display_columns].copy()
    display_df.columns = [
        "Fantasy Name",
        "Full Name",
        "Team",
        "Position",
        "Stars",
        "Total PCS Points",
        "Total UCI Points",
        "PCS/Star",
        "UCI/Star",
        "Age",
        "Nationality",
        "Results Count",
    ]

    # Enhanced table display
    st.dataframe(
        display_df,
        use_container_width=True,
        height=600,
        column_config={
            "Stars": st.column_config.NumberColumn("Stars", format="⭐ %d"),
            "Total PCS Points": st.column_config.NumberColumn("Total PCS Points"),
            "Total UCI Points": st.column_config.NumberColumn("Total UCI Points"),
            "PCS/Star": st.column_config.NumberColumn("PCS/Star", format="%.2f"),
            "UCI/Star": st.column_config.NumberColumn("UCI/Star", format="%.2f"),
            "Age": st.column_config.NumberColumn("Age"),
            "Results Count": st.column_config.NumberColumn("Results Count"),
        },
    )


# =============================================================================
# SUMMARY STATISTICS
# =============================================================================


def display_summary_stats(df):
    """Display summary statistics for the rider data."""
    df_prepared = df

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Riders", len(df_prepared))
        st.metric("Avg Stars", f"{df_prepared['stars'].mean():.1f}")

    with col2:
        total_pcs = df_prepared["total_pcs_points"].sum()
        st.metric("Total PCS Points", total_pcs)
        st.metric("Avg PCS/Rider", f"{total_pcs / len(df_prepared):.1f}")

    with col3:
        total_uci = df_prepared["total_uci_points"].sum()
        st.metric("Total UCI Points", total_uci)
        st.metric("Avg UCI/Rider", f"{total_uci / len(df_prepared):.1f}")

    with col4:
        riders_with_points = len(df_prepared[df_prepared["total_pcs_points"] > 0])
        st.metric("Riders with Points", riders_with_points)
        st.metric(
            "% with Points", f"{riders_with_points / len(df_prepared) * 100:.1f}%"
        )
