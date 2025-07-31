# UI components package - improved organization

# Display components
from .analytics.insights import (
    show_outlier_analysis,
    show_performance_insights,
    show_statistical_insights,
)

# Analytics
from .analytics.main import create_visualizations, show_detailed_analytics
from .analytics.outliers import identify_performance_outliers, identify_value_picks

# Chart components
from .charts.overview import create_star_cost_distribution_chart, create_stats_overview
from .charts.performance import create_performance_distribution_charts
from .charts.team_analysis import create_team_analysis_charts
from .charts.value_analysis import create_value_analysis_charts
from .common.calculations import (
    calculate_percentiles,
    get_consistency_interpretation,
    get_fantasy_value_tier,
    get_trend_interpretation,
)

# Common utilities
from .common.formatting import emoji_flag
from .common.pagination import paginate_dataframe
from .display.performance import (
    render_compact_performance_summary,
    render_season_results,
)
from .display.rider_cards import display_rider_cards, render_single_rider_card
from .display.rider_info import render_fantasy_value_indicator, render_rider_info
from .display.rider_tables import display_rider_table
from .display.summary_stats import display_summary_stats

# Filtering
from .filtering.controls import render_unified_controls
from .filtering.filters import apply_filters
from .filtering.search import filter_riders_by_search, get_sort_options
from .layout.sidebar import render_sidebar

# Layout
from .layout.tabs import (
    show_analytics_tab,
    show_overview_tab,
    show_race_tab,
    show_riders_tab,
)
