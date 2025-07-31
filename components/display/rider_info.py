"""
Basic rider information display components.
"""

import streamlit as st
from config.settings import POSITION_ICONS
from ..common.formatting import emoji_flag
from ..common.calculations import get_fantasy_value_tier


def render_fantasy_value_indicator(rider, percentiles):
    """Render fantasy value assessment for the rider in compact form."""
    pcs_per_star = rider.get("pcs_per_star", 0)
    uci_per_star = rider.get("uci_per_star", 0)
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
    star_count = int(rider["stars"])
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
    demographics_available = any(
        [
            rider.get("age"),
            rider.get("nationality"),
            rider.get("birthplace"),
            rider.get("weight_kg"),
            rider.get("height_m"),
        ]
    )

    if demographics_available:
        with st.expander("👤 Rider Details", expanded=False):
            if rider.get("age"):
                st.caption(
                    f"**Age:** {rider['age']} | **Born:** {rider.get('birthdate', 'N/A')}"
                )

            if rider.get("nationality"):
                flag = emoji_flag(rider["nationality"])
                st.caption(f"**Nationality:** {flag} {rider['nationality']}")

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
