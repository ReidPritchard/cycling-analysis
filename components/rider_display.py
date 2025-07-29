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


def render_fantasy_value_indicator(rider, percentiles):
    """Render fantasy value assessment for the rider in compact form."""
    pcs_per_star = rider.get('pcs_per_star', 0)
    uci_per_star = rider.get('uci_per_star', 0)
    tier_name, tier_color, tier_help = get_fantasy_value_tier(pcs_per_star, percentiles)
    
    # Compact value display
    st.markdown(f"**Fantasy Value:** {tier_name}")
    
    # Show efficiency in a compact format
    efficiency_parts = []
    if pcs_per_star > 0:
        efficiency_parts.append(f"PCS: {pcs_per_star:.1f}/⭐")
    if uci_per_star > 0:
        efficiency_parts.append(f"UCI: {uci_per_star:.1f}/⭐")
    
    if efficiency_parts:
        st.caption(" | ".join(efficiency_parts))
    else:
        st.caption("No efficiency data available")


def render_rider_info(rider, percentiles=None):
    """Render basic rider information and demographics with better hierarchy."""
    # Primary information - most prominent
    st.markdown(f"### {rider['full_name']}")
    
    # Star cost with visual emphasis
    star_count = int(rider['stars'])
    st.markdown(f"#### ⭐ {star_count} {'star' if star_count == 1 else 'stars'}")
    
    # Fantasy value indicator
    if percentiles:
        render_fantasy_value_indicator(rider, percentiles)
    
    # Secondary information - team and position
    col1, col2 = st.columns(2)
    with col1:
        icon = POSITION_ICONS.get(rider["position"], "🚴")
        st.markdown(f"**Position:** {icon} {rider['position']}")
    
    with col2:
        st.markdown(f"**Team:** 🏢 {rider['team']}")

    # Tertiary information - demographics in expandable section
    demographics_available = any([
        rider.get("age"), rider.get("nationality"), rider.get("birthplace"),
        rider.get("weight_kg"), rider.get("height_m")
    ])
    
    if demographics_available:
        with st.expander("👤 Rider Details", expanded=False):
            if rider.get("age"):
                st.caption(
                    f"**Age:** {rider['age']} | **Born:** {rider.get('birthdate', 'N/A')}"
                )

            if rider.get("nationality"):
                flag = emoji_flag(rider['nationality'])
                st.caption(
                    f"**Nationality:** {flag} {rider['nationality']}"
                )

            if rider.get("birthplace"):
                st.caption(f"**Birthplace:** {rider['birthplace']}")

            if rider.get("weight_kg") and rider.get("height_m"):
                st.caption(
                    f"**Physical:** {rider['height_m']}m ({rider['height_ft']:.1f}ft), "
                    f"{rider['weight_kg']}kg ({rider['weight_lbs']:.1f}lbs)"
                )
            elif rider.get("weight_kg"):
                st.caption(
                    f"**Weight:** {rider['weight_kg']} kg ({rider['weight_lbs']:.1f} lbs)"
                )
            elif rider.get("height_m"):
                st.caption(
                    f"**Height:** {rider['height_m']} m ({rider['height_ft']:.1f} ft)"
                )


def render_season_results(rider):
    """Render season results table with better organization."""
    pcs_data = rider.get("pcs_data", {})
    if not pcs_data or "error" in pcs_data:
        st.info("🔍 No PCS data available - rider may not be in startlist")
        return

    season_results = rider.get("season_results", pd.DataFrame())

    if season_results.empty:
        st.info("📊 No recent season results available")
        return

    # Show results count and context
    results_count = len(season_results)
    st.markdown(f"**Recent Results** ({results_count} race{'s' if results_count != 1 else ''})")
    
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
            "Date": st.column_config.DateColumn(
                "Date", 
                width="small",
                help="Race date"
            ),
            "Name": st.column_config.TextColumn(
                "Race", 
                pinned=True, 
                width="medium",
                help="Race name"
            ),
            "Result": st.column_config.NumberColumn(
                "Finish", 
                width="small",
                help="Stage finish position"
            ),
            "GC Position": st.column_config.NumberColumn(
                "GC", 
                width="small",
                help="General Classification position"
            ),
            "PCS Points": st.column_config.NumberColumn(
                "PCS", 
                width="small",
                help="ProCyclingStats points earned"
            ),
            "UCI Points": st.column_config.NumberColumn(
                "UCI", 
                width="small",
                help="UCI WorldTour points earned"
            ),
        },
    )


def get_consistency_interpretation(score):
    """Interpret consistency score with proper logic (lower is better)."""
    if score < 0.3:
        return "Excellent", "green", "Very consistent performance"
    elif score < 0.7:
        return "Good", "blue", "Reasonably consistent performance"
    elif score < 1.0:
        return "Variable", "orange", "Inconsistent performance"
    else:
        return "Unpredictable", "red", "Highly variable performance"


def get_trend_interpretation(score):
    """Interpret trend score (negative = improving, positive = declining)."""
    if score < -0.5:
        return "Improving", "green", "📈", "Strong upward trend in performance"
    elif score < -0.1:
        return "Slight Upturn", "blue", "📈", "Moderate improvement in recent results"
    elif score > 0.5:
        return "Declining", "red", "📉", "Performance trending downward"
    elif score > 0.1:
        return "Slight Decline", "orange", "📉", "Minor decline in recent performance"
    else:
        return "Stable", "gray", "➡️", "Consistent performance level"


def render_compact_performance_summary(rider):
    """Render performance data in a compact, organized format."""
    total_pcs = rider.get("total_pcs_points", 0)
    total_uci = rider.get("total_uci_points", 0)
    consistency_score = rider.get("consistency_score", 0.0)
    trend_score = rider.get("trend_score", 0.0)

    # Only show section if there's meaningful data
    if total_pcs == 0 and total_uci == 0 and consistency_score == 0 and trend_score == 0:
        st.caption("📊 No performance data available")
        return

    st.markdown("**Performance Summary**")
    
    # Compact points display in columns
    if total_pcs > 0 or total_uci > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            if total_pcs > 0:
                st.caption(f"🏆 **PCS:** {total_pcs} pts")
        
        with col2:
            if total_uci > 0:
                st.caption(f"🌍 **UCI:** {total_uci} pts")
    
    # Compact analysis display
    analysis_items = []
    
    if consistency_score > 0:
        consistency_label, _, _ = get_consistency_interpretation(consistency_score)
        analysis_items.append(f"📊 **Consistency:** {consistency_label} ({consistency_score:.2f})")
    
    if trend_score != 0.0:
        trend_label, _, trend_icon, _ = get_trend_interpretation(trend_score)
        analysis_items.append(f"{trend_icon} **Trend:** {trend_label} ({-trend_score:.3f})")
    
    # Display analysis items compactly
    for item in analysis_items:
        st.caption(item)


def render_single_rider_card(rider, percentiles=None):
    """Render a single rider card with improved layout."""
    with st.container(border=True):
        # Better 2-column layout for improved readability
        info_col, stats_col = st.columns([1, 1])

        with info_col:
            render_rider_info(rider, percentiles)
            # Add compact performance summary
            render_compact_performance_summary(rider)

        with stats_col:
            render_season_results(rider)
        
        st.markdown("---")  # Subtle separator instead of heavy divider


# =============================================================================
# MAIN DISPLAY FUNCTIONS  
# =============================================================================


def get_sort_options():
    """Get available sorting options."""
    return {
        "Best Value (PCS/Star)": "pcs_per_star",
        "Best Value (UCI/Star)": "uci_per_star", 
        "Most Points (PCS)": "total_pcs_points",
        "Most Points (UCI)": "total_uci_points",
        "Star Cost": "stars",
        "Most Consistent": "consistency_score",
        "Recent Form": "trend_score",
        "Rider Name": "full_name",
        "Team": "team",
        "Position": "position",
        "Age": "age",
        "Results Count": "season_results_count",
    }


def filter_riders_by_search(df, search_term):
    """Filter riders based on search term."""
    if not search_term:
        return df
    
    search_term = search_term.lower().strip()
    
    # Search across multiple fields
    mask = (
        df['full_name'].str.lower().str.contains(search_term, na=False) |
        df['team'].str.lower().str.contains(search_term, na=False) |
        df['position'].str.lower().str.contains(search_term, na=False) |
        df.get('nationality', pd.Series(dtype='object')).str.lower().str.contains(search_term, na=False)
    )
    
    return df[mask]


def render_unified_controls(df, view_key_prefix=""):
    """Render unified control interface for all display modes."""
    st.markdown("### 🔍 Rider Search & Filters")
    
    # Search and filter row
    search_col, sort_col, order_col = st.columns([2, 2, 1])
    
    with search_col:
        search_term = st.text_input(
            "Search riders", 
            placeholder="Enter name, team, position, or nationality...",
            key=f"{view_key_prefix}_search",
            help="Search across rider names, teams, positions, and nationalities"
        )
    
    with sort_col:
        sort_options = get_sort_options()
        sort_by_label = st.selectbox(
            "Sort by", 
            list(sort_options.keys()),
            key=f"{view_key_prefix}_sort",
            help="Choose how to order the riders"
        )
        sort_by_column = sort_options[sort_by_label]
    
    with order_col:
        # Smart default: ascending for consistency (lower is better), descending for others
        default_ascending = sort_by_column in ['consistency_score', 'full_name', 'team', 'position']
        ascending = st.checkbox(
            "Ascending", 
            value=default_ascending,
            key=f"{view_key_prefix}_ascending",
            help="Sort order: checked = A to Z / low to high, unchecked = Z to A / high to low"
        )
    
    # Quick filter buttons
    st.markdown("**Quick Filters:**")
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    
    with filter_col1:
        show_high_value = st.checkbox(
            "💰 High Value Only",
            key=f"{view_key_prefix}_high_value",
            help="Show only riders with above-average points per star"
        )
        show_with_points = st.checkbox(
            "🏆 Has Points Only",
            key=f"{view_key_prefix}_has_points",
            help="Show only riders who have earned points this season"
        )

    
    with filter_col2:
        # Team filter
        teams = ["All"] + sorted(df["team"].unique().tolist())
        selected_team = st.selectbox("Team", teams)
    
    with filter_col3:
        position_filter = st.selectbox(
            "Position",
            options=["All"] + sorted(df['position'].unique().tolist()),
            key=f"{view_key_prefix}_position",
            help="Filter by rider position"
        )
    
    with filter_col4:
        min_stars, max_stars = st.slider(
            "Star Cost Range",
            min_value=int(df["stars"].min()),
            max_value=int(df["stars"].max()),
            value=(int(df["stars"].min()), int(df["stars"].max())),
        )
    
    return {
        'search_term': search_term,
        'sort_by_column': sort_by_column,
        'ascending': ascending,
        'show_high_value': show_high_value,
        'show_with_points': show_with_points,
        'min_stars': min_stars,
        'max_stars': max_stars,
        'team': selected_team if selected_team != "All" else None,
        'position_filter': position_filter
    }


def get_fantasy_value_tier(pcs_per_star, percentiles):
    """Determine fantasy value tier based on PCS efficiency."""
    if pcs_per_star >= percentiles['90th']:
        return "🔥 Exceptional Value", "green", "Top 10% efficiency - excellent fantasy pick"
    elif pcs_per_star >= percentiles['75th']:
        return "⭐ Great Value", "blue", "Top 25% efficiency - strong fantasy option"
    elif pcs_per_star >= percentiles['50th']:
        return "💰 Good Value", "orange", "Above average efficiency"
    elif pcs_per_star > 0:
        return "🔵 Standard", "gray", "Below average efficiency"
    else:
        return "❓ No Data", "red", "No points earned this season"


def calculate_percentiles(df):
    """Calculate performance percentiles for value assessment."""
    riders_with_points = df[df['pcs_per_star'] > 0]
    if riders_with_points.empty:
        return {'90th': 0, '75th': 0, '50th': 0, '25th': 0}
    
    return {
        '90th': riders_with_points['pcs_per_star'].quantile(0.9),
        '75th': riders_with_points['pcs_per_star'].quantile(0.75), 
        '50th': riders_with_points['pcs_per_star'].quantile(0.5),
        '25th': riders_with_points['pcs_per_star'].quantile(0.25)
    }


def apply_filters(df, filters):
    """Apply all filters to the dataframe."""
    filtered_df = df.copy()
    
    # Apply search filter
    filtered_df = filter_riders_by_search(filtered_df, filters['search_term'])
    
    # Apply quick filters
    if filters['show_high_value']:
        # Show riders with above-average efficiency
        avg_pcs_per_star = filtered_df['pcs_per_star'].mean()
        filtered_df = filtered_df[filtered_df['pcs_per_star'] >= avg_pcs_per_star]
    
    if filters['show_with_points']:
        filtered_df = filtered_df[
            (filtered_df['total_pcs_points'] > 0) | (filtered_df['total_uci_points'] > 0)
        ]
    
    if filters['min_stars'] > 0:
        filtered_df = filtered_df[filtered_df['stars'] >= filters['min_stars']]
    if filters['max_stars'] < df['stars'].max():
        filtered_df = filtered_df[filtered_df['stars'] <= filters['max_stars']]
    
    if filters['position_filter'] != "All":
        filtered_df = filtered_df[filtered_df['position'] == filters['position_filter']]

    if filters['team'] != "All" and filters['team'] is not None:
        filtered_df = filtered_df[filtered_df['team'] == filters['team']]

    
    # Apply sorting
    if not filtered_df.empty:
        filtered_df = filtered_df.sort_values(
            filters['sort_by_column'], 
            ascending=filters['ascending']
        )
    
    return filtered_df


def paginate_dataframe(df, page_size=20, page_key="page"):
    """Paginate dataframe for better performance."""
    if df.empty:
        return df, 1, 1
    
    total_pages = len(df) // page_size + (1 if len(df) % page_size else 0)
    
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            page = st.selectbox(
                f"Page (showing {page_size} riders per page)",
                range(1, total_pages + 1),
                format_func=lambda x: f"Page {x} of {total_pages}",
                key=page_key,
                help=f"Navigate through {len(df)} riders"
            )
    else:
        page = 1
    
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, len(df))
    
    return df.iloc[start_idx:end_idx], page, total_pages


def display_rider_cards(df, page_size=10):
    """Display riders in card format with unified controls and pagination."""
    # Calculate percentiles for fantasy value assessment
    percentiles = calculate_percentiles(df)
    
    # Render unified controls
    filters = render_unified_controls(df, "cards")
    
    # Apply filters and sorting
    df_filtered = apply_filters(df, filters)
    
    # Show results summary
    total_riders = len(df)
    filtered_count = len(df_filtered)
    
    if df_filtered.empty:
        st.warning("🔍 No riders match your search criteria. Try adjusting your filters.")
        return
    
    # Pagination
    df_page, current_page, total_pages = paginate_dataframe(
        df_filtered, page_size, "cards_page"
    )
    
    # Results summary with pagination info
    if total_pages > 1:
        start_idx = (current_page - 1) * page_size + 1
        end_idx = min(current_page * page_size, filtered_count)
        st.info(
            f"👥 Showing riders {start_idx}-{end_idx} of {filtered_count} "
            f"({'filtered from ' + str(total_riders) + ' total' if filtered_count != total_riders else 'total'})"
        )
    else:
        if filtered_count != total_riders:
            st.info(f"🔍 Showing {filtered_count} of {total_riders} riders")
        else:
            st.info(f"👥 Showing all {total_riders} riders")
    
    # Display cards
    for _, rider in df_page.iterrows():
        render_single_rider_card(rider, percentiles)


def display_rider_table(df, page_size=50):
    """Display riders in enhanced table format with unified controls and pagination."""
    # Calculate percentiles for value indicators
    percentiles = calculate_percentiles(df)
    
    # Render unified controls
    filters = render_unified_controls(df, "table")
    
    # Apply filters and sorting
    df_filtered = apply_filters(df, filters)
    
    if df_filtered.empty:
        st.warning("🔍 No riders match your search criteria. Try adjusting your filters.")
        return
    
    # Pagination for large datasets
    df_page, current_page, total_pages = paginate_dataframe(
        df_filtered, page_size, "table_page"
    )
    
    # Show results summary with pagination info
    total_riders = len(df)
    filtered_count = len(df_filtered)
    
    if total_pages > 1:
        start_idx = (current_page - 1) * page_size + 1
        end_idx = min(current_page * page_size, filtered_count)
        st.info(
            f"📊 Showing riders {start_idx}-{end_idx} of {filtered_count} "
            f"({'filtered from ' + str(total_riders) + ' total' if filtered_count != total_riders else 'total'})"
        )
    else:
        if filtered_count != total_riders:
            st.info(f"🔍 Showing {filtered_count} of {total_riders} riders")
        else:
            st.info(f"👥 Showing all {total_riders} riders")
    
    # Add fantasy value indicators to the dataframe
    df_with_value = df_page.copy()
    if 'pcs_per_star' in df_with_value.columns:
        df_with_value['fantasy_value'] = df_with_value['pcs_per_star'].apply(
            lambda x: get_fantasy_value_tier(x, percentiles)[0]
        )
    
    # Select columns for display (handle missing columns gracefully)
    available_columns = df_with_value.columns.tolist()
    display_columns = []
    column_labels = []
    
    # Core columns that should always be available
    core_mapping = {
        "full_name": "Full Name",
        "fantasy_value": "Value Tier",
        "team": "Team", 
        "position": "Position",
        "stars": "Stars",
        "total_pcs_points": "PCS Points",
        "total_uci_points": "UCI Points",
        "pcs_per_star": "PCS/Star",
        "uci_per_star": "UCI/Star"
    }
    
    # Optional columns
    optional_mapping = {
        "age": "Age",
        "nationality": "Nationality", 
        "season_results_count": "Results",
        "consistency_score": "Consistency",
        "trend_score": "Trend"
    }
    
    # Add available core columns
    for col, label in core_mapping.items():
        if col in available_columns:
            display_columns.append(col)
            column_labels.append(label)
    
    # Add available optional columns
    for col, label in optional_mapping.items():
        if col in available_columns:
            display_columns.append(col)
            column_labels.append(label)
    
    # Create display dataframe
    display_df = df_with_value[display_columns].copy()
    display_df.columns = column_labels

    # Enhanced table display with better formatting
    st.dataframe(
        display_df,
        use_container_width=True,
        height=600,
        column_config={
            "Value Tier": st.column_config.TextColumn(
                "Value Tier",
                help="Fantasy value assessment based on points per star efficiency",
                width="medium"
            ),
            "Stars": st.column_config.NumberColumn(
                "Stars", 
                format="⭐ %d",
                help="Fantasy star cost (1-30)"
            ),
            "PCS Points": st.column_config.NumberColumn(
                "PCS Points",
                help="Total ProCyclingStats points earned"
            ),
            "UCI Points": st.column_config.NumberColumn(
                "UCI Points",
                help="Total UCI WorldTour points earned"
            ),
            "PCS/Star": st.column_config.NumberColumn(
                "PCS/Star", 
                format="%.1f",
                help="PCS points per star (higher = better value)",
                width="small"
            ),
            "UCI/Star": st.column_config.NumberColumn(
                "UCI/Star", 
                format="%.1f",
                help="UCI points per star (higher = better value)"
            ),
            "Age": st.column_config.NumberColumn(
                "Age",
                help="Rider age"
            ),
            "Results": st.column_config.NumberColumn(
                "Results",
                help="Number of race results this season"
            ),
            "Consistency": st.column_config.NumberColumn(
                "Consistency",
                format="%.2f",
                help="Performance consistency (lower = more consistent)"
            ),
            "Trend": st.column_config.NumberColumn(
                "Trend",
                format="%.3f", 
                help="Recent performance trend (negative = improving)"
            ),
        },
    )


# =============================================================================
# SUMMARY STATISTICS
# =============================================================================


def display_summary_stats(df):
    """Display enhanced summary statistics for the rider data."""
    if df.empty:
        st.warning("No data available for summary statistics.")
        return
        
    st.markdown("### 📊 Summary Statistics")
    
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Riders", 
            len(df),
            help="Total number of riders in the dataset"
        )
        if 'stars' in df.columns:
            avg_stars = df['stars'].mean()
            st.metric(
                "Avg Stars", 
                f"{avg_stars:.1f}",
                help="Average fantasy star cost across all riders"
            )

    with col2:
        if 'total_pcs_points' in df.columns:
            total_pcs = df["total_pcs_points"].sum()
            st.metric(
                "Total PCS Points", 
                f"{total_pcs:,}",
                help="Sum of all PCS points earned by riders"
            )
            if len(df) > 0:
                st.metric(
                    "Avg PCS/Rider", 
                    f"{total_pcs / len(df):.1f}",
                    help="Average PCS points per rider"
                )

    with col3:
        if 'total_uci_points' in df.columns:
            total_uci = df["total_uci_points"].sum()
            st.metric(
                "Total UCI Points", 
                f"{total_uci:,}",
                help="Sum of all UCI points earned by riders"
            )
            if len(df) > 0:
                st.metric(
                    "Avg UCI/Rider", 
                    f"{total_uci / len(df):.1f}",
                    help="Average UCI points per rider"
                )

    with col4:
        if 'total_pcs_points' in df.columns:
            riders_with_points = len(df[df["total_pcs_points"] > 0])
            st.metric(
                "Riders with Points", 
                riders_with_points,
                help="Number of riders who have earned points this season"
            )
            if len(df) > 0:
                percentage = riders_with_points / len(df) * 100
                st.metric(
                    "% with Points", 
                    f"{percentage:.1f}%",
                    help="Percentage of riders who have earned points"
                )

