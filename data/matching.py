"""
Unified rider matching system for all data sources.

This module provides a single, coherent interface for matching riders across:
- Fantasy rosters
- PCS/startlist data
- Race stage results

Key principles:
- Pure functions with no side effects
- Clear confidence scoring
- Comprehensive match results
- Fallback strategies for partial matches
"""

import logging
import re
from difflib import SequenceMatcher
from typing import Any

from data.models.combined_analytics import RiderMatchingResult
from data.models.race import RaceData
from data.models.unified import RawDataSources, RiderMatchInfo

# =============================================================================
# Core Name Processing
# =============================================================================


def normalize_rider_name(name: str) -> str:
    """
    Normalize rider name for consistent matching.

    Args:
        name: Raw rider name

    Returns:
        Normalized name for matching
    """
    if not name:
        return ""

    # Convert to lowercase and clean whitespace
    normalized = re.sub(r"\s+", " ", name.lower().strip())

    # Remove parentheses and content (e.g., "(Le Court) Pienaar" -> "Pienaar")
    normalized = re.sub(r"\([^)]*\)\s*", "", normalized)

    # Handle name order variations (Last, First -> First Last)
    if "," in normalized:
        parts = [part.strip() for part in normalized.split(",")]
        if len(parts) == 2:
            normalized = f"{parts[1]} {parts[0]}"

    # Remove common suffixes/prefixes
    suffixes = ["jr", "sr", "ii", "iii"]
    words = normalized.split()
    words = [w for w in words if w not in suffixes]
    normalized = " ".join(words)

    return normalized


def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity score between two names (0.0 to 1.0).

    Args:
        name1: First name to compare
        name2: Second name to compare

    Returns:
        Similarity score from 0.0 (no match) to 1.0 (exact match)
    """
    if not name1 or not name2:
        return 0.0

    norm1 = normalize_rider_name(name1)
    norm2 = normalize_rider_name(name2)

    if norm1 == norm2:
        return 1.0

    # Use sequence matcher for fuzzy matching
    similarity = SequenceMatcher(None, norm1, norm2).ratio()

    # Boost similarity if last names match exactly
    words1 = norm1.split()
    words2 = norm2.split()

    if words1 and words2:
        # Check if last names match (assuming last word is surname)
        if words1[-1] == words2[-1]:
            similarity = min(1.0, similarity + 0.2)

        # Check if any word matches exactly
        if any(word in words2 for word in words1):
            similarity = min(1.0, similarity + 0.1)

    return similarity


def find_best_match(
    search_name: str, candidate_names: list[str], threshold: float = 0.8
) -> tuple[str | None, float]:
    """
    Find the best matching name from a list of candidates.

    Args:
        search_name: Name to search for
        candidate_names: List of names to match against
        threshold: Minimum similarity threshold

    Returns:
        Tuple of (best_match_name, confidence_score)
    """
    if not search_name or not candidate_names:
        return None, 0.0

    best_match = None
    best_score = 0.0
    high_scores = []

    for candidate in candidate_names:
        if not candidate:
            continue

        try:
            score = calculate_name_similarity(search_name, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate

            # Track high-scoring matches for debugging
            if score >= 0.7:  # Lower threshold for debug logging
                high_scores.append((candidate, score))

        except Exception as e:
            logging.warning(f"Error comparing '{search_name}' with '{candidate}': {e}")
            continue

    # # Log detailed matching info if there are interesting matches
    # if high_scores:
    #     high_scores.sort(key=lambda x: x[1], reverse=True)
    #     top_matches = high_scores[:3]  # Show top 3 matches
    #     matches_str = ", ".join([f"'{name}' ({score:.3f})" for name, score in top_matches])
    #     logging.debug(f"🔍 Name matching for '{search_name}': top matches = {matches_str}")

    # Return match only if it exceeds threshold
    if best_score >= threshold:
        # logging.debug(
        #     f"✅ Best match for '{search_name}': '{best_match}' (score: {
        #         best_score:.3f}, threshold: {threshold})"
        # )
        return best_match, best_score
    # elif best_match:
    #     logging.debug(
    #         f"❌ Match below threshold for '{search_name}': '{best_match}' (score: {
    #             best_score:.3f}, threshold: {threshold})"
    #     )

    return None, best_score


# =============================================================================
# Unified Matching System
# =============================================================================


class RiderMatcher:
    """
    Unified rider matching system for all data sources.
    """

    def __init__(self, fuzzy_threshold: float = 0.8):
        """
        Initialize matcher with configuration.

        Args:
            fuzzy_threshold: Minimum similarity for fuzzy matches
        """
        self.fuzzy_threshold = fuzzy_threshold

    def match_fantasy_to_startlist(
        self, fantasy_riders: list[dict[str, Any]], startlist_riders: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """
        Match fantasy riders to startlist riders.

        Args:
            fantasy_riders: List of fantasy rider dicts
            startlist_riders: List of startlist rider dicts

        Returns:
            Dict mapping fantasy names to matched startlist data
        """
        matches = {}

        # Check if we have team information for team-based matching
        fantasy_has_teams = any(rider.get("team") for rider in fantasy_riders)
        startlist_has_teams = any(rider.get("team_name") for rider in startlist_riders)

        if fantasy_has_teams and startlist_has_teams:
            # logging.debug(
            #     f"🏆 Using team-based matching: {len(fantasy_riders)} fantasy riders across te
            #     ams"
            # )
            matches = self._match_by_team_and_name(fantasy_riders, startlist_riders)
        else:
            # logging.debug(
            #     f"📝 Using name-only matching: fantasy_teams={fantasy_has_teams}, 
            #     startlist_teams={
            #         startlist_has_teams
            #     }"
            # )
            matches = self._match_by_name_only(fantasy_riders, startlist_riders)

        # logging.debug(
        #     f"🔗 Fantasy-to-startlist matching: {len(matches)} successful matches out of {
        #         len(fantasy_riders)
        #     } fantasy riders"
        # )
        return matches

    def match_fantasy_to_race_results(
        self, fantasy_rider: dict[str, Any], race_data: RaceData
    ) -> RiderMatchingResult:
        """
        Match a fantasy rider to race stage results.

        Args:
            fantasy_rider: Fantasy rider data
            race_data: Complete race data with stages

        Returns:
            RiderMatchingResult with match information
        """
        fantasy_name = fantasy_rider.get("fantasy_name", "")
        pcs_data = fantasy_rider.get("pcs_data", {})
        pcs_name = pcs_data.get("name", "") if pcs_data else ""

        # Try multiple name sources for matching
        candidate_names = [fantasy_name, pcs_name, fantasy_rider.get("full_name", "")]
        candidate_names = [name for name in candidate_names if name]

        # logging.debug(
        #     f"🏁 Race matching for '{fantasy_name}': trying {len(candidate_names)} name variants"
        # )

        if not candidate_names:
            # logging.debug(f"⚠️ No candidate names for '{fantasy_name}' - skipping race matching")
            return RiderMatchingResult(
                fantasy_name=fantasy_name, match_confidence=0.0, match_method="no_name"
            )

        best_match = None
        best_confidence = 0.0
        matched_stages = 0

        # Try to find rider in completed stages
        stages = race_data.get("stages", [])
        completed_stages = [s for s in stages if s.get("results")]

        # logging.debug(
        #     f"📋 Searching {len(completed_stages)} completed stages for '{fantasy_name}'"
        # )

        for name in candidate_names:
            stage_matches = 0

            for stage in stages:
                stage_results = stage.get("results", None)
                # Check if stage has results (is completed)
                if not stage_results:
                    continue

                matched_rider, confidence = self._find_rider_in_stage_results(name, stage_results)

                if matched_rider and confidence >= self.fuzzy_threshold:
                    stage_matches += 1

                    if not best_match or confidence > best_confidence:
                        best_match = matched_rider
                        best_confidence = confidence

            if stage_matches > matched_stages:
                matched_stages = stage_matches
                # logging.debug(
                #     f"🎯 Found '{name}' in {stage_matches} stages (confidence: {
                #         best_confidence:.3f})"
                # )

        # Determine match method and canonical name
        match_method = "no_match"
        canonical_name = fantasy_name

        if best_match:
            if best_confidence == 1.0:
                match_method = "exact"
            elif best_confidence >= 0.9:
                match_method = "high_confidence_fuzzy"
            else:
                match_method = "fuzzy"

            canonical_name = best_match.get("rider_name", "")
            # logging.debug(
            #     f"✅ Race match for '{fantasy_name}': '{canonical_name}' ({match_method}, {
            #         best_confidence:.3f}, {matched_stages} stages)"
            # )
        # else:
        #     logging.debug(
        #         f"❌ No race match found for '{fantasy_name}' (searched {
        #             len(completed_stages)
        #         } stages)"
        #     )

        return RiderMatchingResult(
            fantasy_name=fantasy_name,
            pcs_name=pcs_name,
            stage_name=best_match.get("rider_name") if best_match else None,
            rider_url=(best_match.get("rider_url") if best_match else pcs_data.get("rider_url")),
            match_confidence=best_confidence,
            match_method=match_method,
            canonical_name=canonical_name,
            team_name=best_match.get("team_name") if best_match else None,
            rider_number=best_match.get("rider_number") if best_match else None,
            nationality=(
                best_match.get("nationality") if best_match else pcs_data.get("nationality")
            ),
            age=best_match.get("age") if best_match else None,
        )

    def match_all_riders(
        self,
        fantasy_riders: list[dict[str, Any]],
        startlist_riders: list[dict[str, Any]],
        pcs_cache: dict[str, Any],
        race_data: RaceData,
    ) -> dict[str, RiderMatchInfo]:
        """
        Create comprehensive matches across all data sources.

        Args:
            fantasy_riders: List of fantasy rider dicts
            startlist_riders: List of startlist rider dicts
            pcs_cache: Dict of cached PCS data
            race_data: Complete race data

        Returns:
            Dict mapping fantasy names to complete match information
        """
        # Step 1: Match fantasy to startlist/PCS
        startlist_matches = self.match_fantasy_to_startlist(fantasy_riders, startlist_riders)

        # Step 2: Create enriched rider data with PCS information
        enriched_riders = []
        for rider in fantasy_riders:
            enriched_rider = rider.copy()
            full_name = rider.get("full_name", "")

            # Add startlist match information
            if full_name in startlist_matches:
                match_info = startlist_matches[full_name]
                enriched_rider.update(
                    {
                        "matched_startlist_rider": match_info.get("matched_startlist_rider", {}),
                        "pcs_matched_name": match_info.get("pcs_matched_name", ""),
                        "pcs_rider_url": match_info.get("pcs_rider_url", ""),
                    }
                )

                # Add PCS data if available in cache
                rider_url = match_info.get("pcs_rider_url", "")
                if rider_url and rider_url in pcs_cache:
                    enriched_rider["pcs_data"] = pcs_cache[rider_url]

            enriched_riders.append(enriched_rider)

        # Step 3: Match enriched riders to race results
        final_matches = {}
        for rider in enriched_riders:
            fantasy_name = rider.get("fantasy_name", "")
            if not fantasy_name:
                continue

            race_match = self.match_fantasy_to_race_results(rider, race_data)

            # Combine all match information
            final_matches[fantasy_name] = {
                "fantasy_rider": rider,
                "startlist_match": startlist_matches.get(rider.get("full_name", "")),
                "race_match": race_match,
                "has_pcs_data": bool(rider.get("pcs_data")),
                "has_race_data": race_match.get("match_confidence", 0.0) >= self.fuzzy_threshold,
                "canonical_name": race_match.get("canonical_name", rider.get("full_name", "")),
            }

        return final_matches

    # =============================================================================
    # Helper Methods
    # =============================================================================

    def _find_rider_in_stage_results(
        self, rider_name: str, stage_results: list[dict[str, Any]]
    ) -> tuple[dict[str, Any] | None, float]:
        """Find rider in stage results using name matching."""
        if not rider_name or not stage_results:
            return None, 0.0

        result_names = [result.get("rider_name", "") for result in stage_results]
        matched_name, confidence = find_best_match(rider_name, result_names, self.fuzzy_threshold)

        if matched_name:
            # Find the full result data
            for result in stage_results:
                if result.get("rider_name") == matched_name:
                    return result, confidence

        return None, confidence

    def _match_by_team_and_name(
        self, fantasy_riders: list[dict[str, Any]], startlist_riders: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Match riders using team information first, then names within teams."""
        matches = {}

        # Group riders by team
        fantasy_by_team = {}
        for rider in fantasy_riders:
            team = rider.get("team", "Unknown")
            if team not in fantasy_by_team:
                fantasy_by_team[team] = []
            fantasy_by_team[team].append(rider)

        startlist_by_team = {}
        for rider in startlist_riders:
            team = rider.get("team_name", "Unknown")
            if team not in startlist_by_team:
                startlist_by_team[team] = []
            startlist_by_team[team].append(rider)

        # Create team mappings using fuzzy matching
        team_mappings = {}
        fantasy_teams = set(fantasy_by_team.keys())
        startlist_teams = set(startlist_by_team.keys())

        for fantasy_team in fantasy_teams:
            best_match, _ = find_best_match(fantasy_team, list(startlist_teams))
            if best_match:
                team_mappings[fantasy_team] = best_match

        # Match riders within matched teams
        for fantasy_team, team_riders in fantasy_by_team.items():
            if fantasy_team not in team_mappings:
                # Fallback to name-only matching for unmatched teams
                for rider in team_riders:
                    self._try_match_rider_by_name(rider, startlist_riders, matches)
                continue

            startlist_team = team_mappings[fantasy_team]
            if startlist_team not in startlist_by_team:
                continue

            startlist_riders_for_team = startlist_by_team[startlist_team]

            for rider in team_riders:
                full_name = rider.get("full_name", "")
                if not full_name:
                    continue

                # Find best match within the team
                startlist_names = [r.get("rider_name", "") for r in startlist_riders_for_team]
                matched_name, _ = find_best_match(full_name, startlist_names)

                if matched_name:
                    # Find the full PCS rider data
                    for pcs_rider in startlist_riders_for_team:
                        if pcs_rider.get("rider_name") == matched_name:
                            matches[full_name] = {
                                "matched_startlist_rider": pcs_rider,
                                "pcs_matched_name": matched_name,
                                "pcs_rider_url": pcs_rider.get("rider_url"),
                            }
                            break

        return matches

    def _match_by_name_only(
        self, fantasy_riders: list[dict[str, Any]], startlist_riders: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Match riders by name only when team information is not available."""
        matches = {}

        for rider in fantasy_riders:
            self._try_match_rider_by_name(rider, startlist_riders, matches)

        return matches

    def _try_match_rider_by_name(
        self,
        rider: dict[str, Any],
        startlist_riders: list[dict[str, Any]],
        matches: dict[str, dict[str, Any]],
    ) -> None:
        """Attempt to match a single rider by name."""
        full_name = rider.get("full_name", "")
        if not full_name:
            return

        startlist_names = [r.get("rider_name", "") for r in startlist_riders]
        matched_name, _ = find_best_match(full_name, startlist_names)

        if matched_name:
            # Find the full PCS rider data
            for pcs_rider in startlist_riders:
                if pcs_rider.get("rider_name") == matched_name:
                    matches[full_name] = {
                        "matched_startlist_rider": pcs_rider,
                        "pcs_matched_name": matched_name,
                        "pcs_rider_url": pcs_rider.get("rider_url"),
                    }
                    break


# =============================================================================
# Convenience Functions
# =============================================================================


def create_rider_matcher(fuzzy_threshold: float = 0.8) -> RiderMatcher:
    """
    Create a configured RiderMatcher instance.

    Args:
        fuzzy_threshold: Minimum similarity for fuzzy matches

    Returns:
        Configured RiderMatcher instance
    """
    return RiderMatcher(fuzzy_threshold=fuzzy_threshold)


def match_all_data_sources(
    raw_data: RawDataSources, fuzzy_threshold: float = 0.8
) -> dict[str, RiderMatchInfo]:
    """
    Convenience function to match all data sources.

    Args:
        raw_data: Dict containing all raw data sources
        fuzzy_threshold: Minimum similarity for fuzzy matches

    Returns:
        Complete matching results
    """
    fantasy_riders = raw_data.get("fantasy_riders", [])
    startlist_riders = raw_data.get("startlist_riders", [])
    pcs_cache = raw_data.get("pcs_cache", {})
    race_data = raw_data.get("race_data", {})

    # logging.debug(
    #     f"🔍 Starting rider matching: {len(fantasy_riders)} fantasy riders, {
    #         len(startlist_riders)
    #     } startlist riders, {len(pcs_cache)} PCS entries, threshold={fuzzy_threshold}"
    # )

    matcher = create_rider_matcher(fuzzy_threshold)

    matches = matcher.match_all_riders(
        fantasy_riders=fantasy_riders,
        startlist_riders=startlist_riders,
        pcs_cache=pcs_cache,
        race_data=race_data,
    )

    # Log summary statistics
    total_matches = len(matches)
    pcs_matches = sum(1 for m in matches.values() if m.get("has_pcs_data", False))
    race_matches = sum(1 for m in matches.values() if m.get("has_race_data", False))

    # logging.debug(
    #     f"✅ Matching completed: {total_matches} total matches, {pcs_matches} with PCS data, {
    #         race_matches
    #     } with race data"
    # )

    return matches
