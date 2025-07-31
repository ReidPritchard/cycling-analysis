# UI components package - improved organization

# Display components
from .display.rider_cards import display_rider_cards, render_single_rider_card
from .display.rider_tables import display_rider_table
from .display.summary_stats import display_summary_stats
from .display.rider_info import render_rider_info, render_fantasy_value_indicator
from .display.performance import (
    render_season_results,
    render_compact_performance_summary,
)

# Chart components
from .charts.overview import create_stats_overview, create_star_cost_distribution_chart
from .charts.value_analysis import create_value_analysis_charts
from .charts.performance import create_performance_distribution_charts
from .charts.team_analysis import create_team_analysis_charts

# Analytics
from .analytics.main import show_detailed_analytics, create_visualizations
from .analytics.insights import (
    show_performance_insights,
    show_outlier_analysis,
    show_statistical_insights,
)
from .analytics.outliers import identify_performance_outliers, identify_value_picks

# Layout
from .layout.tabs import (
    show_overview_tab,
    show_riders_tab,
    show_analytics_tab,
    show_race_tab,
)
from .layout.sidebar import render_sidebar

# Common utilities
from .common.formatting import emoji_flag
from .common.calculations import (
    get_fantasy_value_tier,
    calculate_percentiles,
    get_consistency_interpretation,
    get_trend_interpretation,
)
from .common.pagination import paginate_dataframe

# Filtering
from .filtering.controls import render_unified_controls
from .filtering.filters import apply_filters
from .filtering.search import filter_riders_by_search, get_sort_options
