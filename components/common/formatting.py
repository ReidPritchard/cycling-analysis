"""
Formatting utilities for the Fantasy Cycling Stats app.
"""

import re


def emoji_flag(country_code):
    """Convert a country code to its emoji flag representation."""
    cc = country_code.upper()
    if not re.match(r"^[A-Z]{2}$", cc):
        return ""

    return "".join(chr(c + 127397) for c in cc.encode("utf-8"))
