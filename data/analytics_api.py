"""
Race Analytics API

Clean interface for accessing race-specific rider analytics that combines
rider season results with detailed race stage data.
"""

from typing import Any, Literal

import pandas as pd

from .loaders import load_race_data
from .models.combined_analytics import RaceAnalyticsSummary, RiderRaceAnalytics
from .models.race import RaceData
from .models.rider import RiderData
from .processors.combined_rider_analytics import (
    calculate_race_analytics_summary,
    calculate_race_specific_analytics,
)
from .processors.rider_matching import match_riders_across_sources


class RaceAnalyticsAPI:
    """Clean interface for accessing race-specific rider analytics."""

    def __init__(self, race_key: str):
        """
        Initialize API for a specific race.

        Args:
            race_key: Race identifier from SUPPORTED_RACES
        """
        self.race_key = race_key
        self._race_data: RaceData | None = None
        self._rider_analytics_cache: dict[str, RiderRaceAnalytics] = {}
        self._race_summary_cache: RaceAnalyticsSummary | None = None

    @property
    def race_data(self) -> RaceData:
        """Lazy load race data."""
        if self._race_data is None:
            self._race_data = load_race_data(self.race_key)
        return self._race_data

    def get_rider_race_analytics(
        self, rider: RiderData, force_refresh: bool = False
    ) -> RiderRaceAnalytics:
        """
        Get comprehensive race analytics for a specific rider.

        Args:
            rider: Rider data from fantasy roster
            force_refresh: Force recalculation even if cached

        Returns:
            RiderRaceAnalytics with complete performance data
        """
        cache_key = rider.get("fantasy_name", "")

        if not force_refresh and cache_key in self._rider_analytics_cache:
            return self._rider_analytics_cache[cache_key]

        analytics = calculate_race_specific_analytics(rider, self.race_data, self.race_key)

        if cache_key:
            self._rider_analytics_cache[cache_key] = analytics

        return analytics

    def get_multiple_rider_analytics(
        self, riders: pd.DataFrame, force_refresh: bool = False
    ) -> dict[str, RiderRaceAnalytics]:
        """
        Get analytics for multiple riders efficiently.

        Args:
            riders: DataFrame with fantasy rider data
            force_refresh: Force recalculation for all riders

        Returns:
            Dict mapping fantasy_name -> RiderRaceAnalytics
        """
        results = {}

        for _, rider in riders.iterrows():
            rider_dict = rider.to_dict()
            fantasy_name = rider_dict.get("fantasy_name", "")

            if fantasy_name:
                analytics = self.get_rider_race_analytics(rider_dict, force_refresh)
                results[fantasy_name] = analytics

        return results

    def get_classification_leaderboard(
        self, classification: Literal["gc", "points", "kom", "youth"], top_n: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get current standings for a specific classification.

        Args:
            classification: Classification type
            top_n: Number of riders to return

        Returns:
            List of rider standings with current positions
        """
        stages = self.race_data.get("stages", [])
        completed_stages = [stage for stage in stages if stage.get("results")]

        if not completed_stages:
            return []

        # Get latest standings from most recent stage
        latest_stage = completed_stages[-1]

        classification_map = {
            "gc": "general_classification",
            "points": "points_classification",
            "kom": "kom_classification",
            "youth": "youth_classification",
        }

        classification_key = classification_map.get(classification)
        if not classification_key:
            return []

        standings = latest_stage.get(classification_key, [])

        # Format leaderboard
        leaderboard = []
        for i, rider in enumerate(standings[:top_n], 1):
            leaderboard.append(
                {
                    "rank": i,
                    "rider_name": rider.get("rider_name"),
                    "team_name": rider.get("team_name"),
                    "nationality": rider.get("nationality"),
                    "age": rider.get("age"),
                    "time": rider.get("time"),
                    "points": rider.get("pcs_points", 0),
                    "prev_rank": rider.get("prev_rank"),
                }
            )

        return leaderboard

    def compare_riders(self, rider_names: list[str], riders_df: pd.DataFrame) -> dict[str, Any]:
        """
        Compare multiple riders' race performance.

        Args:
            rider_names: List of fantasy names to compare
            riders_df: DataFrame with fantasy rider data

        Returns:
            Comparison data with side-by-side metrics
        """
        comparison_data = {"riders": {}, "comparison_metrics": {}}

        analytics_list = []

        # Get analytics for each rider
        for rider_name in rider_names:
            rider_row = riders_df[riders_df["fantasy_name"] == rider_name]
            if rider_row.empty:
                continue

            rider_dict = rider_row.iloc[0].to_dict()
            analytics = self.get_rider_race_analytics(rider_dict)
            analytics_list.append(analytics)
            comparison_data["riders"][rider_name] = analytics

        if len(analytics_list) < 2:
            return comparison_data

        # Calculate comparison metrics
        metrics = {}

        # Stage performance comparison
        avg_positions = [
            a.get("avg_stage_position") for a in analytics_list if a.get("avg_stage_position")
        ]
        if avg_positions:
            metrics["best_avg_stage_position"] = min(avg_positions)
            metrics["worst_avg_stage_position"] = max(avg_positions)

        # GC comparison
        gc_ranks = []
        for analytics in analytics_list:
            gc_analytics = analytics.get("gc_analytics")
            if gc_analytics and gc_analytics.get("current_rank"):
                gc_ranks.append(gc_analytics["current_rank"])

        if gc_ranks:
            metrics["best_gc_position"] = min(gc_ranks)
            metrics["worst_gc_position"] = max(gc_ranks)

        # Points comparison
        total_points = [a.get("total_stage_pcs_points", 0) for a in analytics_list]
        metrics["highest_points"] = max(total_points) if total_points else 0
        metrics["lowest_points"] = min(total_points) if total_points else 0

        # Consistency comparison
        consistency_scores = [
            a.get("consistency_score")
            for a in analytics_list
            if a.get("consistency_score") is not None
        ]
        if consistency_scores:
            metrics["most_consistent"] = min(consistency_scores)  # Lower = more consistent
            metrics["least_consistent"] = max(consistency_scores)

        comparison_data["comparison_metrics"] = metrics

        return comparison_data

    def get_stage_winners(self) -> list[dict[str, Any]]:
        """
        Get winners and key stats for each completed stage.

        Returns:
            List of stage winner information
        """
        stages = self.race_data.get("stages", [])
        completed_stages = [stage for stage in stages if stage.get("results")]

        winners = []

        for i, stage in enumerate(completed_stages, 1):
            results = stage.get("results", [])
            if not results:
                continue

            winner = results[0]  # First result is the winner

            winners.append(
                {
                    "stage_number": i,
                    "stage_name": f"Stage {i}",
                    "date": stage.get("date"),
                    "stage_type": stage.get("stage_type"),
                    "profile_icon": stage.get("profile_icon"),
                    "distance": stage.get("distance"),
                    "departure": stage.get("departure"),
                    "arrival": stage.get("arrival"),
                    "rider_name": winner.get("rider_name"),
                    "team_name": winner.get("team_name"),
                    "nationality": winner.get("nationality"),
                    "age": winner.get("age"),
                    "time": winner.get("time"),
                    "pcs_points": winner.get("pcs_points", 0),
                    "uci_points": winner.get("uci_points", 0),
                }
            )

        return winners

    def get_race_summary(self, force_refresh: bool = False) -> RaceAnalyticsSummary:
        """
        Get comprehensive race summary statistics.

        Args:
            force_refresh: Force recalculation even if cached

        Returns:
            RaceAnalyticsSummary with race-wide statistics
        """
        if not force_refresh and self._race_summary_cache:
            return self._race_summary_cache

        summary = calculate_race_analytics_summary(self.race_data, self.race_key)
        self._race_summary_cache = summary

        return summary

    def get_rider_stage_progression(
        self,
        rider: RiderData,
        classification: Literal["stage", "gc", "points", "kom", "youth"] = "gc",
    ) -> list[dict[str, Any]]:
        """
        Get stage-by-stage progression for a specific rider and classification.

        Args:
            rider: Rider data
            classification: Which classification to track

        Returns:
            List of stage progression data
        """
        analytics = self.get_rider_race_analytics(rider)
        stage_results = analytics.get("stage_results", [])

        progression = []

        for stage_perf in stage_results:
            stage_data = {
                "stage_number": stage_perf.get("stage_number"),
                "date": stage_perf.get("date"),
                "stage_type": stage_perf.get("stage_type"),
                "profile_icon": stage_perf.get("profile_icon"),
            }

            if classification == "stage":
                stage_data["position"] = stage_perf.get("stage_rank")
                stage_data["points"] = stage_perf.get("stage_pcs_points", 0)
            elif classification == "gc":
                stage_data["position"] = stage_perf.get("gc_rank")
                stage_data["time"] = stage_perf.get("gc_time")
            elif classification == "points":
                stage_data["position"] = stage_perf.get("points_rank")
            elif classification == "kom":
                stage_data["position"] = stage_perf.get("kom_rank")
            elif classification == "youth":
                stage_data["position"] = stage_perf.get("youth_rank")

            progression.append(stage_data)

        return progression

    def get_top_performers_by_metric(
        self,
        riders_df: pd.DataFrame,
        metric: str,
        top_n: int = 10,
        ascending: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get top performers by a specific metric.

        Args:
            riders_df: DataFrame with fantasy rider data
            metric: Metric to rank by (e.g., 'avg_stage_position', 'total_stage_pcs_points')
            top_n: Number of riders to return
            ascending: True for ascending order (lower is better), False for descending

        Returns:
            List of top performers with their metrics
        """
        all_analytics = self.get_multiple_rider_analytics(riders_df)

        # Extract metric values
        rider_metrics = []
        for fantasy_name, analytics in all_analytics.items():
            metric_value = analytics.get(metric)
            if metric_value is not None:
                rider_metrics.append(
                    {
                        "fantasy_name": fantasy_name,
                        "rider_name": analytics.get("rider_name"),
                        "team_name": analytics.get("team_name"),
                        "metric_value": metric_value,
                        "analytics": analytics,
                    }
                )

        # Sort and return top N
        rider_metrics.sort(key=lambda x: x["metric_value"], reverse=not ascending)

        return rider_metrics[:top_n]

    def clear_cache(self):
        """Clear all cached analytics data."""
        self._rider_analytics_cache.clear()
        self._race_summary_cache = None
