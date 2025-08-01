"""
Unified data pipeline that orchestrates loading, matching, and analytics.

This module provides a clean, high-level interface that combines all data
operations in a predictable sequence:

1. Load raw data from all sources
2. Match riders across data sources
3. Calculate analytics from matched data
4. Return structured results

Key benefits:
- Clear separation of concerns
- Comprehensive error handling
- Progress tracking
- Configurable pipeline stages
- Type-safe data flow
"""

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

import pandas as pd

from data.analytics import (
    calculate_basic_rider_metrics,
    calculate_enhanced_rider_analytics,
)
from data.loaders import fetch_missing_pcs_data, get_all_raw_data
from data.matching import match_all_data_sources
from data.models.race import RaceData
from data.models.unified import (
    AnalyticsDataSet,
    DataLoadResult,
    MatchedDataSet,
    PipelineConfig,
    PipelineStage,
    PipelineState,
    RawDataSources,
    RiderAnalyticsData,
    RiderMatchInfo,
)

# =============================================================================
# Pipeline Configuration
# =============================================================================


def create_default_config(race_key: str) -> PipelineConfig:
    """
    Create default pipeline configuration.

    Args:
        race_key: Race identifier

    Returns:
        Default configuration
    """
    return PipelineConfig(
        race_key=race_key,
        use_cache=True,
        force_refresh=False,
        fuzzy_threshold=0.8,
        require_team_match=True,
        use_enhanced_analytics=True,
        calculate_trends=True,
        include_comparisons=False,
        parallel_processing=False,
        batch_size=10,
        api_delay=0.5,
        include_debug_info=True,
        verbose_logging=True,
    )


# =============================================================================
# Main Pipeline Class
# =============================================================================


class DataPipeline:
    """
    Unified data pipeline for fantasy cycling analytics.
    """

    def __init__(self, config: PipelineConfig):
        """
        Initialize pipeline with configuration.

        Args:
            config: Pipeline configuration
        """
        race_key = config.get("race_key")
        if race_key is None:
            raise ValueError("Missing required config: race_key")

        self.config = config
        self.state = PipelineState(
            race_key=race_key,
            use_enhanced_analytics=config.get("use_enhanced_analytics", True),
            fuzzy_threshold=config.get("fuzzy_threshold", 0.8),
            pipeline_stages=[],
            current_stage=None,
            overall_success=False,
            total_fantasy_riders=0,
            matched_riders_count=0,
            enhanced_analytics_count=0,
            data_quality_distribution={},
        )

    def run(self, progress_callback: Callable[[float, str], None] | None = None) -> DataLoadResult:
        """
        Run the complete data pipeline.

        Args:
            progress_callback: Optional progress callback function

        Returns:
            Complete pipeline results
        """
        # Run pipeline stages with granular error handling
        self._start_pipeline_stage("loading")
        try:
            if progress_callback:
                progress_callback(0.05, "Starting data loading...")
            raw_data = self._load_raw_data(progress_callback)
            self.state["raw_data"] = raw_data
            self._complete_pipeline_stage("loading", True)
        except Exception as e:
            self._complete_pipeline_stage("loading", False, str(e))
            return self._prepare_error_result(str(e))

        self._start_pipeline_stage("matching")
        try:
            if progress_callback:
                progress_callback(0.35, "Starting rider matching...")
            matched_data = self._match_riders(raw_data, progress_callback)
            self.state["matched_data"] = matched_data
            self._complete_pipeline_stage("matching", True)
        except Exception as e:
            self._complete_pipeline_stage("matching", False, str(e))
            return self._prepare_error_result(str(e))

        self._start_pipeline_stage("analytics")
        try:
            if progress_callback:
                progress_callback(0.60, "Starting analytics computation...")
            analytics_data = self._calculate_analytics(matched_data, raw_data, progress_callback)
            self.state["analytics_data"] = analytics_data
            self._complete_pipeline_stage("analytics", True)
        except Exception as e:
            self._complete_pipeline_stage("analytics", False, str(e))
            return self._prepare_error_result(str(e))

        self._start_pipeline_stage("finalization")
        try:
            if progress_callback:
                progress_callback(0.90, "Preparing final results...")
            result = self._prepare_results(raw_data, matched_data, analytics_data)
            if progress_callback:
                progress_callback(0.95, "Finalizing data structures...")
            self._complete_pipeline_stage("finalization", True)
        except Exception as e:
            self._complete_pipeline_stage("finalization", False, str(e))
            return self._prepare_error_result(str(e))

        self.state["overall_success"] = True
        if progress_callback:
            progress_callback(1.0, "Pipeline completed successfully!")
        return result

    # =============================================================================
    # Pipeline Stages
    # =============================================================================

    def _load_raw_data(
        self, progress_callback: Callable[[float, str], None] | None = None
    ) -> RawDataSources:
        """Load raw data from all sources."""
        race_key = self.config.get("race_key", "")

        if progress_callback:
            progress_callback(0.10, "Loading fantasy rider data...")

        # Get all raw data
        raw_data = get_all_raw_data(race_key)

        if progress_callback:
            progress_callback(0.15, "Loading race and startlist data...")

        # Update state
        self.state["total_fantasy_riders"] = len(raw_data.get("fantasy_riders", []))

        if progress_callback:
            progress_callback(0.20, "Loading cached PCS data...")

        # Fetch missing PCS data if needed
        if not self.config.get("use_cache", True) or self.config.get("force_refresh", False):
            startlist_riders = raw_data.get("startlist_riders", [])
            rider_urls = [
                rider.get("rider_url", "") for rider in startlist_riders if rider.get("rider_url")
            ]

            if rider_urls:
                if progress_callback:
                    progress_callback(0.25, f"Fetching PCS data for {len(rider_urls)} riders...")
                new_pcs_data = fetch_missing_pcs_data(rider_urls, raw_data.get("pcs_cache"))
                # Update cache in raw_data
                pcs_cache = raw_data.get("pcs_cache", {})
                pcs_cache.update(new_pcs_data)
                raw_data["pcs_cache"] = pcs_cache
                if progress_callback:
                    progress_callback(0.30, "PCS data fetching completed")

        if progress_callback:
            progress_callback(0.32, "Raw data loading completed")

        return raw_data

    def _match_riders(
        self,
        raw_data: RawDataSources,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> MatchedDataSet:
        """Match riders across all data sources."""
        fuzzy_threshold = self.config.get("fuzzy_threshold", 0.8)

        if progress_callback:
            progress_callback(0.40, "Initializing rider matching process...")

        # Perform matching
        matches = match_all_data_sources(raw_data, fuzzy_threshold)

        if progress_callback:
            progress_callback(0.48, f"Matched {len(matches)} riders across data sources")

        # Update state
        self.state["matched_riders_count"] = len(matches)

        if progress_callback:
            progress_callback(0.52, "Calculating match summary statistics...")

        # Calculate match summary
        match_summary = self._calculate_match_summary(raw_data, matches)

        if progress_callback:
            progress_callback(0.55, "Rider matching completed")

        return MatchedDataSet(
            riders=matches,
            race_data=raw_data.get("race_data", {}),
            match_summary=match_summary,
        )

    def _calculate_analytics(
        self,
        matched_data: MatchedDataSet,
        raw_data: RawDataSources,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> AnalyticsDataSet:
        """Calculate analytics from matched data."""
        race_data = getattr(matched_data, "race_data", RaceData())
        race_key = self.config.get("race_key", "")
        use_enhanced = self.config.get("use_enhanced_analytics", True)

        matched_riders = matched_data.get("riders", {})

        if progress_callback:
            progress_callback(0.65, f"Computing basic rider metrics ({len(matched_riders)}...")

        # Calculate basic metrics for all riders
        basic_df = calculate_basic_rider_metrics(matched_riders)

        if progress_callback:
            progress_callback(0.70, f"Basic metrics calculated for {len(basic_df)} riders")

        # Calculate enhanced metrics if requested
        enhanced_df = None
        if use_enhanced and race_data:
            if progress_callback:
                progress_callback(0.72, "Computing enhanced race analytics...")
            try:
                enhanced_df = calculate_enhanced_rider_analytics(
                    matched_riders, race_data, race_key
                )
                self.state["enhanced_analytics_count"] = len(enhanced_df)
                if progress_callback:
                    progress_callback(
                        0.78, f"Enhanced analytics computed for {len(enhanced_df)} riders"
                    )
            except Exception as e:
                logging.warning(f"Enhanced analytics failed: {e}")
                enhanced_df = basic_df.copy()
                if progress_callback:
                    progress_callback(
                        0.78, "Using basic metrics as fallback for enhanced analytics"
                    )

        if progress_callback:
            progress_callback(0.80, "Building individual rider analytics...")

        # Create individual rider analytics
        rider_analytics = self._build_rider_analytics(
            matched_riders, basic_df, enhanced_df, use_enhanced
        )

        if progress_callback:
            progress_callback(0.83, "Computing race summary and pipeline metrics...")

        # Define missing variables
        race_summary = self._calculate_match_summary(raw_data, matched_riders)
        computed_race_info = {}  # Placeholder for computed race info
        pipeline_info = self._get_performance_metrics()

        if progress_callback:
            progress_callback(0.85, "Analytics computation completed")

        return AnalyticsDataSet(
            riders=rider_analytics,
            basic_metrics_df=basic_df,
            enhanced_metrics_df=enhanced_df,
            race_summary=race_summary,
            computed_race_info=computed_race_info,
            pipeline_info=pipeline_info,
        )

    def _prepare_results(
        self,
        raw_data: RawDataSources,
        matched_data: MatchedDataSet,
        analytics_data: AnalyticsDataSet,
    ) -> DataLoadResult:
        """Prepare final results for consumption."""
        # Use enhanced DataFrame if available, otherwise basic
        main_df = analytics_data.get("enhanced_metrics_df")
        if main_df is None:
            main_df = analytics_data.get("basic_metrics_df")
        if main_df is None:
            main_df = pd.DataFrame()

        # Calculate summary
        summary = {
            "total_riders": len(raw_data.get("fantasy_riders", [])),
            "matched_riders": matched_data.get("match_summary", {}).get("matched_riders", 0),
            "enhanced_analytics": self.state.get("enhanced_analytics_count", 0),
            "data_sources": {
                "fantasy": bool(raw_data.get("fantasy_riders")),
                "startlist": bool(raw_data.get("startlist_riders")),
                "pcs_cache": bool(raw_data.get("pcs_cache")),
                "race_data": bool(raw_data.get("race_data")),
            },
            "pipeline_stages": len(self.state.get("stages", [])),
            "overall_success": self.state.get("overall_success", False),
        }

        # Collect errors
        errors = []

        for stage in self.state.get("stages", []):
            stage_name = stage.get("stage_name", "Unknown Stage")
            stage_status = "Success" if stage.get("success", True) else "Failed"
            if not stage.get("success", True):
                error_message = stage.get("error_message", "No error message")
                errors.append(f"{stage_name}: {stage_status} - {error_message}")

        return DataLoadResult(
            riders_df=main_df,
            pipeline_state=self.state,
            raw_data=raw_data,
            matched_data=matched_data,
            analytics_data=analytics_data,
            summary=summary,
            warnings=[],  # Kept for compatibility; remove if not needed elsewhere
            errors=errors,
        )

    def _prepare_error_result(self, error_message: str) -> DataLoadResult:
        """Prepare error result when pipeline fails."""
        raw_data = self.state.get("raw_data")
        if raw_data is None:
            raw_data = RawDataSources()

        matched_data = self.state.get("matched_data")
        if matched_data is None:
            matched_data = MatchedDataSet()

        analytics_data = self.state.get("analytics_data")
        if analytics_data is None:
            analytics_data = AnalyticsDataSet()

        return DataLoadResult(
            riders_df=pd.DataFrame(),
            pipeline_state=self.state,
            raw_data=raw_data,
            matched_data=matched_data,
            analytics_data=analytics_data,
            summary={"error": error_message},
            warnings=[],
            errors=[error_message],
        )

    # =============================================================================
    # Helper Methods
    # =============================================================================

    def _start_pipeline_stage(self, stage_name: str) -> None:
        """Start tracking a pipeline stage."""
        self.state["current_stage"] = stage_name

        stage = PipelineStage(
            stage_name=stage_name,
            start_time=datetime.now().isoformat(),
            success=False,
            items_processed=0,
            items_succeeded=0,
        )

        if "pipeline_stages" not in self.state:
            self.state["pipeline_stages"] = []
        self.state["pipeline_stages"].append(stage)

        if self.config.get("verbose_logging", True):
            logging.info(f"🔄 Starting pipeline stage: {stage_name}")

    def _complete_pipeline_stage(
        self, search_stage_name: str, success: bool, error_message: str | None = None
    ) -> None:
        """Complete tracking a pipeline stage."""
        self.state["current_stage"] = None

        # Find and update the stage
        pipeline_stages = self.state.get("pipeline_stages", [])
        for stage in reversed(pipeline_stages):
            stage_name = stage.get("stage_name", "")
            if stage_name == search_stage_name:
                stage["end_time"] = datetime.now().isoformat()
                stage["success"] = success
                if error_message:
                    stage["error_message"] = error_message
                break

        if self.config.get("verbose_logging", True):
            status = "✅" if success else "❌"
            logging.info(f"{status} Completed pipeline stage: {search_stage_name}")
            if error_message:
                logging.error(f"Error in {search_stage_name}: {error_message}")

    def _calculate_data_quality(self, match_info: RiderMatchInfo) -> float:
        """Calculate data quality score for a rider."""
        score = 0.0

        # Has fantasy data (always true)
        score += 0.2

        # Has PCS data
        if match_info.get("has_pcs_data", False):
            score += 0.3

        # Has race data
        if match_info.get("has_race_data", False):
            score += 0.3

        # Match confidence
        race_match = match_info.get("race_match")
        if race_match:
            confidence = race_match.get("match_confidence", 0.0)
            score += 0.2 * confidence

        return min(1.0, score)

    def _get_performance_metrics(self) -> dict[str, Any]:
        """Get pipeline performance metrics."""
        pipeline_stages = self.state.get("pipeline_stages", [])
        total_time = 0.0
        stage_times = {}
        for stage in pipeline_stages:
            start_time = stage.get("start_time")
            end_time = stage.get("end_time")
            if start_time and end_time:
                try:
                    start = datetime.fromisoformat(start_time)
                    end = datetime.fromisoformat(end_time)
                    duration = (end - start).total_seconds()
                    if duration < 0:
                        duration = 0.0
                    stage_times[stage.get("stage_name")] = duration
                    total_time += duration
                except Exception:
                    continue
        successful_stages = sum(1 for s in pipeline_stages if s.get("success"))
        return {
            "total_time_seconds": total_time,
            "stage_times": stage_times,
            "successful_stages": successful_stages,
            "total_stages": len(pipeline_stages),
        }

    def _calculate_match_summary(self, raw_data, matches):
        return {
            "total_fantasy_riders": len(raw_data.get("fantasy_riders", [])),
            "matched_riders": len(matches),
            "has_pcs_data": sum(1 for m in matches.values() if m.get("has_pcs_data", False)),
            "has_race_data": sum(1 for m in matches.values() if m.get("has_race_data", False)),
            "match_rate": len(matches) / max(1, len(raw_data.get("fantasy_riders", []))),
        }

    def _build_rider_analytics(self, matched_riders, basic_df, enhanced_df, use_enhanced):
        rider_analytics = {}
        for fantasy_name, match_info in matched_riders.items():
            rider_data = RiderAnalyticsData(
                fantasy_name=fantasy_name,
                canonical_name=match_info.get("canonical_name", ""),
                match_info=match_info,
                basic_metrics=basic_df.loc[fantasy_name].to_dict()
                if fantasy_name in basic_df.index
                else {},
                race_analytics=enhanced_df.loc[fantasy_name].to_dict()
                if use_enhanced and enhanced_df is not None and fantasy_name in enhanced_df.index
                else None,
                has_enhanced_analytics=use_enhanced and bool(enhanced_df is not None),
                data_quality_score=self._calculate_data_quality(match_info),
            )
            rider_analytics[fantasy_name] = rider_data
        return rider_analytics


# =============================================================================
# Convenience Functions
# =============================================================================


def run_pipeline(
    race_key: str,
    config: PipelineConfig | None = None,
    progress_callback: Callable[[float, str], None] | None = None,
) -> DataLoadResult:
    """
    Run the complete data pipeline with default or custom configuration.

    Args:
        race_key: Race identifier
        config: Optional custom configuration
        progress_callback: Optional progress callback

    Returns:
        Complete pipeline results
    """
    if config is None:
        config = create_default_config(race_key)
    else:
        # Ensure race_key is set
        config["race_key"] = race_key

    pipeline = DataPipeline(config)
    return pipeline.run(progress_callback)


def get_pipeline_summary(race_key: str) -> dict[str, Any]:
    """
    Get a summary of what the pipeline would do without running it.

    Args:
        race_key: Race identifier

    Returns:
        Summary of expected pipeline behavior
    """
    config = create_default_config(race_key)

    return {
        "race_key": race_key,
        "stages": ["loading", "matching", "analytics", "finalization"],
        "data_sources": ["fantasy_riders", "startlist_riders", "pcs_cache", "race_data"],
        "analytics_types": ["basic_metrics", "enhanced_metrics", "race_summary"],
        "configuration": config,
        "estimated_time_seconds": 30,  # Rough estimate
    }
