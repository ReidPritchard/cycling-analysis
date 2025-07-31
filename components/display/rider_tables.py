"""
Rider table display components.
"""

import streamlit as st
from ..common.calculations import calculate_percentiles, get_fantasy_value_tier
from ..common.pagination import paginate_dataframe
from ..filtering.controls import render_unified_controls
from ..filtering.filters import apply_filters


def display_rider_table(df, page_size=50):
    """Display riders in enhanced table format with unified controls and pagination."""
    # Calculate percentiles for value indicators
    percentiles = calculate_percentiles(df)

    # Render unified controls
    filters = render_unified_controls(df, "table")

    # Apply filters and sorting
    df_filtered = apply_filters(df, filters)

    if df_filtered.empty:
        st.warning(
            "🔍 No riders match your search criteria. Try adjusting your filters."
        )
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
    if "pcs_per_star" in df_with_value.columns:
        df_with_value["fantasy_value"] = df_with_value["pcs_per_star"].apply(
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
        "uci_per_star": "UCI/Star",
    }

    # Optional columns
    optional_mapping = {
        "age": "Age",
        "nationality": "Nationality",
        "season_results_count": "Results",
        "consistency_score": "Consistency",
        "trend_score": "Trend",
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
                width="medium",
            ),
            "Stars": st.column_config.NumberColumn(
                "Stars", format="⭐ %d", help="Fantasy star cost (1-30)"
            ),
            "PCS Points": st.column_config.NumberColumn(
                "PCS Points", help="Total ProCyclingStats points earned"
            ),
            "UCI Points": st.column_config.NumberColumn(
                "UCI Points", help="Total UCI WorldTour points earned"
            ),
            "PCS/Star": st.column_config.NumberColumn(
                "PCS/Star",
                format="%.1f",
                help="PCS points per star (higher = better value)",
                width="small",
            ),
            "UCI/Star": st.column_config.NumberColumn(
                "UCI/Star",
                format="%.1f",
                help="UCI points per star (higher = better value)",
            ),
            "Age": st.column_config.NumberColumn("Age", help="Rider age"),
            "Results": st.column_config.NumberColumn(
                "Results", help="Number of race results this season"
            ),
            "Consistency": st.column_config.NumberColumn(
                "Consistency",
                format="%.2f",
                help="Performance consistency (lower = more consistent)",
            ),
            "Trend": st.column_config.NumberColumn(
                "Trend",
                format="%.3f",
                help="Recent performance trend (negative = improving)",
            ),
        },
    )
