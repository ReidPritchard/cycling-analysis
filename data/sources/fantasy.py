"""
Fantasy data loading from JSON files.
"""

import json
from typing import Any

from config.settings import FANTASY_DATA_FILE


def load_fantasy_json() -> list[dict[str, Any]]:
    """
    Load the raw fantasy data from JSON file.

    Returns:
        list: Raw fantasy rider data as loaded from JSON
    """
    with open(FANTASY_DATA_FILE) as f:
        return json.load(f)
