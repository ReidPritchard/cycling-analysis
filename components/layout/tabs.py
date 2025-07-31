"""
Tab content components for the Fantasy Cycling Stats app.
"""

from datetime import datetime
from typing import Any

import streamlit as st

from ..display.rider_cards import display_rider_cards
from ..display.rider_tables import display_rider_table
from ..display.summary_stats import display_summary_stats
from ..charts.overview import create_star_cost_distribution_chart, create_stats_overview
from ..analytics.main import show_detailed_analytics
from data import RaceData, refresh_race_cache


def show_overview_tab(filtered_riders):
    """Display the overview tab content"""
    st.subheader("📈 Key Statistics")
    create_stats_overview(filtered_riders)

    st.divider()

    # Quick stats
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏅 Position/Style Breakdown")
        position_counts = filtered_riders["position"].value_counts()
        for pos, count in position_counts.items():
            st.markdown(f"**{pos}:** {count} riders")

    with col2:
        st.subheader("⭐ Star Cost Distribution")
        create_star_cost_distribution_chart(filtered_riders)


def show_riders_tab(filtered_riders):
    """Display the riders tab content"""
    st.subheader(f"🏆 Riders ({len(filtered_riders)} found)")

    display_summary_stats(filtered_riders)

    # Display format options
    display_format = st.radio("Display as:", ["Cards", "Table"])

    if display_format == "Cards":
        display_rider_cards(filtered_riders)
    else:
        display_rider_table(filtered_riders)


def show_analytics_tab(filtered_riders):
    """Display the analytics tab content"""
    show_detailed_analytics(filtered_riders)


def show_race_tab(race_data: RaceData):
    """Enhanced TdF Femmes 2025 tab with comprehensive race insights"""
    st.header("🏁 Tour de France Femmes 2025")

    # Error handling
    if "error" in race_data:
        st.error(f"❌ Error loading race data: {race_data['error']}")
        if st.button("🔄 Refresh Race Data", use_container_width=True):
            refresh_race_cache()
            st.rerun()
        return

    # Enhanced header with race dates
    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        race_info = race_data.get("race_data", {})
        race_name = race_info.get("name", "Tour de France Femmes 2025")
        st.markdown(f"### {race_name}")

        # Add race dates prominently
        start_date = race_info.get("startdate", "")
        end_date = race_info.get("enddate", "")
        if start_date and end_date:
            st.caption(f"📅 {start_date} → {end_date}")

    with col2:
        if "fetched_at" in race_data:
            fetch_time = datetime.fromisoformat(race_data["fetched_at"])
            st.markdown(f"*Updated: {fetch_time.strftime('%m/%d %H:%M')}*")

    with col3:
        if st.button("🔄 Refresh", help="Refresh race data", use_container_width=True):
            refresh_race_cache()
            st.rerun()

    _ = st.divider()

    # Debug display race data
    with st.expander("Details"):
        st.json(race_data)

    # Main content tabs for better organization
    tab1, tab2, tab3 = st.tabs(
        ["📊 Race Overview", "🏁 Stage Analysis", "🎯 Fantasy Strategy"]
    )

    with tab1:
        _show_race_progress_overview(race_data)

    with tab2:
        _show_stage_difficulty_analysis(race_data)

    with tab3:
        # _show_fantasy_strategy_insights(race_data)
        _show_upcoming_stages_focus(race_data)


def _show_race_progress_overview(race_data: RaceData):
    """Display race progress with completion tracking and key insights"""
    computed_info = race_data.get("computed_race_info", {})

    if computed_info is None:
        _ = st.error("Failed to process the race data")
        return

    # Progress header with visual indicators
    _ = st.subheader("🏁 Race Progress")

    # Key progress metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        stages_completed = computed_info.get("stages_completed", 0)
        stages_incomplete = computed_info.get("stages_incomplete", 0)
        total_stages = stages_completed + stages_incomplete

        # Progress percentage calculation
        progress = stages_completed / total_stages if total_stages > 0 else 0

        st.metric(
            "Race Progress",
            f"{stages_completed}/{total_stages}",
            delta=f"{progress:.0%} Complete",
            help="Stages completed vs total stages",
        )

    with col2:
        total_distance = computed_info.get("total_distance", "N/A")
        completed_distance = computed_info.get("total_distance_completed", "0.0 km")

        st.metric(
            "Distance Progress",
            completed_distance,
            delta=f"of {total_distance}",
            help="Kilometers completed vs total race distance",
        )

    with col3:
        climbs_completed = computed_info.get("climbs_completed", 0)
        climbs_incomplete = computed_info.get("climbs_incomplete", 0)

        st.metric(
            "Climbs Remaining",
            climbs_incomplete,
            delta=f"{climbs_completed} completed",
            help="Critical climbs still to come in the race",
        )

    with col4:
        total_elevation = computed_info.get("total_vertical_meters", 0)
        if total_elevation > 0:
            st.metric(
                "Total Elevation",
                f"{total_elevation:,}m",
                help="Total vertical meters across all stages",
            )
        else:
            st.metric(
                "Elevation", "Loading...", help="Calculating total elevation gain"
            )

    # Visual progress bar
    if total_stages > 0:
        st.progress(progress, text=f"Race completion: {progress:.0%}")


def _show_stage_difficulty_analysis(race_data: RaceData):
    """Display stage-by-stage difficulty analysis for fantasy strategy"""
    _ = st.subheader("📊 Stage Analysis")

    stages = race_data.get("stages", [])
    computed_info = race_data.get("computed_race_info", {})

    if computed_info is None:
        _ = st.error("Failed to process race data for stage analysis")
        return

    if not stages:
        _ = st.info("Stage details will be available when race data loads.")
        return

    # Key stage insights
    col1, col2 = st.columns(2)

    with col1:
        # longest_stage = computed_info.get("longest_stage")
        # if longest_stage:
        #     _ = st.info(
        #         f"🎯 **Longest Stage**: {longest_stage.get('distance', 'N/A')} - "
        #         + f"{longest_stage.get('departure', '')} → {longest_stage.get('arrival', '')}"
        #     )

        avg_distance = computed_info.get("avg_stage_distance")
        if avg_distance:
            _ = st.metric("Average Stage Distance", f"{avg_distance} km")

    with col2:
        # shortest_stage = computed_info.get("shortest_stage")
        # if shortest_stage:
        #     _ = st.info(
        #         f"⚡ **Shortest Stage**: {shortest_stage.get('distance', 'N/A')} - "
        #         + f"{shortest_stage.get('departure', '')} → {shortest_stage.get('arrival', '')}"
        #     )

        avg_elevation = computed_info.get("avg_stage_vertical_meters")
        if avg_elevation:
            _ = st.metric("Average Elevation Gain", f"{avg_elevation:,.0f}m")

    # Stage timeline with difficulty indicators
    _show_stage_timeline(stages, computed_info)


def _show_stage_timeline(stages: list[dict[str, Any]], computed_info: dict[str, Any]):
    """Show visual timeline of stages with difficulty and completion status"""
    _ = st.markdown("#### Stage Timeline")

    # Profile icon mapping for visual indicators
    profile_icons = {
        "p1": {"emoji": "🏃", "difficulty": "Flat", "color": "green"},
        "p2": {"emoji": "🚴", "difficulty": "Rolling", "color": "blue"},
        "p3": {"emoji": "🏔️", "difficulty": "Hilly", "color": "orange"},
        "p4": {"emoji": "⛰️", "difficulty": "Mountain", "color": "red"},
        "p5": {"emoji": "🗻", "difficulty": "High Mountain", "color": "violet"},
    }

    today = datetime.now().date()

    for i, stage in enumerate(stages, 1):
        stage_date = stage.get("date")
        profile = stage.get("profile_icon", "p1")
        profile_info = profile_icons.get(profile, profile_icons["p1"])

        # Determine if stage is completed
        is_completed = False
        if stage_date:
            try:
                # Assuming date format is "MM-DD" for 2025
                stage_date_obj = datetime.strptime(
                    f"2025-{stage_date}", "%Y-%m-%d"
                ).date()
                is_completed = stage_date_obj <= today
            except:
                # Check for alternative completion indicators
                is_completed = (
                    stage.get("results") is not None
                    or stage.get("avg_speed_winner") is not None
                    or stage.get("won_how") is not None
                )

        # Stage card with completion status
        status_indicator = "✅" if is_completed else "⏳"
        distance = stage.get("distance", "N/A")
        vertical = stage.get("vertical_meters", 0)

        col1, col2, col3, col4 = st.columns([1, 4, 3, 3])

        with col1:
            st.markdown(f"**{status_indicator} {i}**")

        with col2:
            route = f"{stage.get('departure', '')} → {stage.get('arrival', '')}"
            st.markdown(f"{profile_info['emoji']} {route}")

        with col3:
            # FIXME: Support different distance units
            _ = st.markdown(
                f"**{distance} km** | :{profile_info['color']}-badge[{profile_info['difficulty']}]"
            )

        with col4:
            if vertical and vertical > 0:
                _ = st.markdown(
                    f"↗️ {vertical:,}m ({len(stage.get('climbs', []))} climbs)"
                )
            else:
                _ = st.markdown("↗️ Flat")

    # _ = st.divider()

    # Graph the stage difficulty?


def _show_fantasy_strategy_insights(race_data: RaceData):
    """Display fantasy cycling strategy recommendations based on race data"""
    st.subheader("🎯 Fantasy Strategy Insights")

    computed_info = race_data.get("computed_race_info", {})
    stages = race_data.get("stages", [])

    # Strategy recommendations based on race characteristics
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 💡 Key Opportunities")

        # Identify upcoming critical stages
        climbs_remaining = computed_info.get("climbs_incomplete", 0)
        if climbs_remaining > 3:
            st.success(
                f"🏔️ **{climbs_remaining} climbs remaining** - Consider climbers for upcoming stages"
            )

        # Check for sprint stages
        flat_stages = [s for s in stages if s.get("profile_icon") == "p1"]
        if len(flat_stages) > 2:
            st.success(
                f"🏃 **{len(flat_stages)} sprint stages** - Sprinters are valuable picks"
            )

        # Mountain stage analysis
        mountain_stages = [s for s in stages if s.get("profile_icon") in ["p4", "p5"]]
        if len(mountain_stages) > 1:
            st.warning(
                f"⛰️ **{len(mountain_stages)} mountain stages** - Essential to have strong climbers"
            )

    with col2:
        st.markdown("#### ⚠️ Risk Factors")

        # Long stages identification
        avg_distance = computed_info.get("avg_stage_distance", 0)
        if avg_distance > 120:
            st.warning(
                f"📏 **Long average stage** ({avg_distance:.1f}km) - Endurance riders favored"
            )

        # High elevation analysis
        avg_elevation = computed_info.get("avg_stage_vertical_meters", 0)
        if avg_elevation > 1500:
            st.error(
                f"🗻 **High elevation race** ({avg_elevation:,.0f}m avg) - Pure climbers essential"
            )

        # Weather or other risk factors could be added here
        st.info("💰 **Budget tip**: Balance star riders across different stage types")


def _show_upcoming_stages_focus(race_data: RaceData):
    """Highlight next 2-3 stages for immediate fantasy decisions"""
    st.markdown("#### 🔜 Next Critical Stages")

    stages = race_data.get("stages", [])
    today = datetime.now().date()

    upcoming_stages = []
    for stage in stages:
        stage_date = stage.get("date")
        is_completed = False

        # Check completion status
        if stage_date:
            try:
                stage_date_obj = datetime.strptime(
                    f"2025-{stage_date}", "%Y-%m-%d"
                ).date()
                is_completed = stage_date_obj <= today
            except:
                is_completed = (
                    stage.get("results") is not None
                    or stage.get("avg_speed_winner") is not None
                    or stage.get("won_how") is not None
                )

        if not is_completed:
            upcoming_stages.append(stage)
            if len(upcoming_stages) >= 3:  # Show next 3 stages
                break

    if upcoming_stages:
        for i, stage in enumerate(upcoming_stages, 1):
            stage_index = stages.index(stage) + 1 if stage in stages else i

            with st.expander(
                f"Stage {stage_index}: {stage.get('departure', '')} → {stage.get('arrival', '')}",
                expanded=(i == 1),
            ):  # Expand first upcoming stage
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Date**: {stage.get('date', 'TBD')}")
                    st.markdown(f"**Distance**: {stage.get('distance', 'N/A')}")

                with col2:
                    profile = stage.get("profile_icon", "p1")
                    difficulty_map = {
                        "p1": "Flat",
                        "p2": "Rolling",
                        "p3": "Hilly",
                        "p4": "Mountain",
                        "p5": "High Mountain",
                    }
                    st.markdown(
                        f"**Profile**: {difficulty_map.get(profile, 'Unknown')}"
                    )

                    vertical = stage.get("vertical_meters", 0)
                    if vertical > 0:
                        st.markdown(f"**Elevation**: {vertical:,}m")

                # Fantasy recommendations for this stage
                if profile in ["p1", "p2"]:
                    st.info("🏃 **Fantasy tip**: Favor sprinters and classics riders")
                elif profile in ["p4", "p5"]:
                    st.warning(
                        "🏔️ **Fantasy tip**: Essential to have climbers in your team"
                    )
                else:
                    st.info(
                        "🚴 **Fantasy tip**: All-rounders and puncheurs are good picks"
                    )
    else:
        st.info("All stages completed! Check results for final standings.")


def _show_race_info_tab(race_data: RaceData):
    """Display race information tab"""
    race_info = race_data.get("race_data", {})

    # Display key race metrics in a compact format
    if race_info:
        # Show key information if available
        col1, col2, col3 = st.columns(3)

        with col1:
            if "startdate" in race_info:
                st.metric("Start Date", race_info["startdate"])
            elif "date" in race_info:
                st.metric("Date", race_info["date"])

        with col2:
            if "enddate" in race_info:
                st.metric("End Date", race_info["enddate"])
            elif "year" in race_info:
                st.metric("Year", race_info["year"])

        with col3:
            if "distance" in race_info:
                st.metric("Total Distance", f"{race_info['distance']} km")

        # # Show expandable details
        # with st.expander("📄 Detailed Race Information"):
        #     st.json(race_info)
    else:
        _ = st.info(
            "ℹ️ Detailed race information will be available when the race data is loaded."
        )
