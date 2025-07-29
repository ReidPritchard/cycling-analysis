"""
Name formatting utilities for converting fantasy rider names to ProCyclingStats format.
"""

import unicodedata
import streamlit as st


def format_rider_name_for_pcs(full_name):
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
        normalized_name = unicodedata.normalize("NFD", full_name)
        ascii_name = normalized_name.encode("ascii", "ignore").decode("ascii")
        return ascii_name.replace(" ", "-").lower()
