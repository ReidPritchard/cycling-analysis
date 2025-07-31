"""
Name formatting utilities for converting fantasy rider names to ProCyclingStats format.
"""

import unicodedata
from difflib import SequenceMatcher as SM
from typing import Any

import pandas as pd
import streamlit as st


def format_rider_name_for_pcs(full_name: str) -> str:
    """
    Convert fantasy rider name format to ProCyclingStats URL format.

    Parses names like "KOPECKY Lotte" or "LE COURT PIENAAR Kimberley"
    where last name is all uppercase, followed by first name(s).
    Also handles special characters like "BRAUßE Franziska" => "franziska-brausse"
    and "BURLOVÁ Kristýna" => "kristyna-burlova".

    Args:
        full_name (str): The full name in fantasy format

    Returns:
        str: The formatted name for PCS URL (e.g., "lotte-kopecky")
    """
    # FIXME: There are some names like:
    # "LE COURT PIENAAR Kimberley" that needs to be mapped to
    # "kimberley-le-court" (no pienaar), but the current code
    # doesn't handle this case. It's unclear if there is a "rule"
    # that can be used to fix this.
    hard_coded_conversions = {
        "LE COURT PIENAAR Kimberley": "kimberley-le-court",
    }

    if full_name in hard_coded_conversions:
        return hard_coded_conversions[full_name]

    try:
        name_parts = full_name.strip().split()
        if not name_parts or len(name_parts) < 2:
            raise ValueError("full_name format unexpected")

        # Find where the uppercase block ends
        last_name_parts = []
        first_name_parts = []
        for i, part in enumerate(name_parts):
            if part.isupper():
                last_name_parts.append(part)
            else:
                first_name_parts = name_parts[i:]
                break

        if not last_name_parts or not first_name_parts:
            raise ValueError("Could not split last and first names")

        # Combine first and last names
        pcs_name = "-".join(first_name_parts + last_name_parts)

        # Normalize special characters to ASCII equivalents
        # This handles characters like ß -> ss, ý -> y, etc.
        normalized_name = unicodedata.normalize("NFD", pcs_name)
        ascii_name = normalized_name.encode("ascii", "ignore").decode("ascii")

        # Convert to lowercase
        return ascii_name.lower()

    except Exception as e:
        st.warning(f"Could not parse full_name '{full_name}': {e}")
        # Fallback: simple replacement with normalization
        try:
            normalized_name = unicodedata.normalize("NFD", full_name)
            ascii_name = normalized_name.encode("ascii", "ignore").decode("ascii")
            return ascii_name.replace(" ", "-").lower()
        except Exception as fallback_e:
            st.error(f"Fallback normalization failed for '{full_name}': {fallback_e}")
            return full_name.replace(" ", "-").lower()


def find_best_match(search_string: str, choices: list[str]) -> str | None:
    """
    Find the best match for a search string in a list of choices using fuzzy matching.

    Args:
        search_string (str): The string to search for
        choices (List[str]): List of strings to match against

    Returns:
        Optional[str]: The best matching choice or None if no good match found
    """
    if not search_string or not choices:
        return None

    # Filter out empty choices
    valid_choices = [choice for choice in choices if choice and isinstance(choice, str)]
    if not valid_choices:
        return None

    best_match = None
    best_ratio = 0.0

    for choice in valid_choices:
        try:
            ratio = SM(None, search_string.strip(), choice.strip()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = choice
        except Exception as e:
            # Log but don't fail - continue with other choices
            st.warning(f"Error comparing '{search_string}' with '{choice}': {e}")
            continue

    # Return the match only if it exceeds a reasonable threshold
    return best_match if best_ratio > 0.8 else None


def match_rider_names(
    riders: pd.DataFrame | list[dict[str, Any]],
    startlist_riders: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Match fantasy riders with PCS/startlist riders using team and name fuzzy matching.

    Args:
        riders (pd.DataFrame or list): DataFrame or list of rider dictionaries with
                                     'full_name' field and optionally 'team' field
        startlist_riders (list): List of PCS rider dictionaries with
                               'rider_name', 'rider_url', and optionally 'team_name' fields

    Returns:
        dict: Dictionary mapping fantasy rider names to matched PCS rider data
    """
    # Input validation and normalization
    if riders is None or startlist_riders is None:
        return {}

    # Convert inputs to consistent format
    if hasattr(riders, "to_dict"):
        # Convert DataFrame to list of records
        riders_list = riders.to_dict("records")
    elif isinstance(riders, list):
        riders_list = riders
    else:
        st.warning(f"Unexpected riders input type: {type(riders)}")
        return {}

    if not isinstance(startlist_riders, list):
        st.warning(
            f"Expected startlist_riders to be a list, got: {type(startlist_riders)}"
        )
        return {}

    if not riders_list or not startlist_riders:
        return {}

    matched_riders = {}

    # Check if we have team information for team-based matching
    riders_have_teams = any(rider.get("team") for rider in riders_list)
    startlist_have_teams = any(rider.get("team_name") for rider in startlist_riders)

    if riders_have_teams and startlist_have_teams:
        # Team-based matching approach
        matched_riders = _match_by_team_and_name(riders_list, startlist_riders)
    else:
        # Fallback to name-only matching
        matched_riders = _match_by_name_only(riders_list, startlist_riders)

    return matched_riders


def _match_by_team_and_name(
    riders_list: list[dict[str, Any]], startlist_riders: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Helper function to match riders by team and name."""
    matched_riders = {}

    # Group riders by team
    riders_by_team = {}
    for rider in riders_list:
        team = rider.get("team", "Unknown")
        if team not in riders_by_team:
            riders_by_team[team] = []
        riders_by_team[team].append(rider)

    # Group startlist riders by team
    startlist_by_team = {}
    for rider in startlist_riders:
        team = rider.get("team_name", "Unknown")
        if team not in startlist_by_team:
            startlist_by_team[team] = []
        startlist_by_team[team].append(rider)

    # Create team mappings using fuzzy matching
    team_mappings = {}
    riders_teams = set(riders_by_team.keys())
    startlist_teams = set(startlist_by_team.keys())

    for fantasy_team in riders_teams:
        best_match = find_best_match(fantasy_team, list(startlist_teams))
        if best_match:
            team_mappings[fantasy_team] = best_match

    # Match riders within matched teams
    for fantasy_team, team_riders in riders_by_team.items():
        if fantasy_team not in team_mappings:
            # Fallback to name-only matching for unmatched teams
            for rider in team_riders:
                _try_match_rider_by_name(rider, startlist_riders, matched_riders)
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
            startlist_names = [
                r.get("rider_name", "") for r in startlist_riders_for_team
            ]
            matched_name = find_best_match(full_name, startlist_names)

            if matched_name:
                # Find the full PCS rider data
                for pcs_rider in startlist_riders_for_team:
                    if pcs_rider.get("rider_name") == matched_name:
                        matched_riders[full_name] = {
                            # TODO: Rename these fields to be more accurate
                            # maybe "pcs_data" -> "matched_startlist_rider",
                            "matched_startlist_rider": pcs_rider,
                            "pcs_matched_name": matched_name,
                            "pcs_rider_url": pcs_rider.get("rider_url"),
                        }
                        break

    return matched_riders


def _match_by_name_only(
    riders_list: list[dict[str, Any]], startlist_riders: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Helper function to match riders by name only."""
    matched_riders = {}

    for rider in riders_list:
        _try_match_rider_by_name(rider, startlist_riders, matched_riders)

    return matched_riders


def _try_match_rider_by_name(
    rider: dict[str, Any],
    startlist_riders: list[dict[str, Any]],
    matched_riders: dict[str, dict[str, Any]],
) -> None:
    """Helper function to attempt matching a single rider by name."""
    full_name = rider.get("full_name", "")
    if not full_name:
        return

    startlist_names = [r.get("rider_name", "") for r in startlist_riders]
    matched_name = find_best_match(full_name, startlist_names)

    if matched_name:
        # Find the full PCS rider data
        for pcs_rider in startlist_riders:
            if pcs_rider.get("rider_name") == matched_name:
                matched_riders[full_name] = {
                    "matched_startlist_rider": pcs_rider,
                    "pcs_matched_name": matched_name,
                    "pcs_rider_url": pcs_rider.get("rider_url"),
                }
                break
