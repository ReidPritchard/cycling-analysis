"""
Cache management utilities for the Fantasy Cycling Stats app.
"""

import json
import logging
import os
from datetime import datetime

from config.settings import CACHE_EXPIRY_DELTA


def load_cache(cache_file, data_key="data"):
    """Load data from cache file if it exists and is not expired."""
    if not os.path.exists(cache_file):
        return {}

    try:
        with open(cache_file) as f:
            cache_data = json.load(f)

        # Check if cache is expired
        cache_date = datetime.fromisoformat(cache_data.get("cached_at", "1970-01-01"))
        if datetime.now() - cache_date > CACHE_EXPIRY_DELTA:
            logging.info("🔄 Cache expired. Will refresh data.")
            return {}

        return cache_data.get(data_key, {})
    except (json.JSONDecodeError, ValueError) as e:
        logging.error(f"❌ Error reading cache file: {e}")
        return {}


def save_cache(cache_file, data, data_key="data"):
    """Save data to cache file with timestamp."""
    cache_data = {"cached_at": datetime.now().isoformat(), data_key: data}

    try:
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)
        logging.info(f"✅ Data cached to {cache_file}")
    except Exception as e:
        logging.error(f"❌ Error saving cache: {e}")


def refresh_cache(cache_file, cache_type=""):
    """Force refresh of cache by deleting the cache file."""
    if os.path.exists(cache_file):
        os.remove(cache_file)
        logging.info(
            f"🗑️ {cache_type} cache cleared. Data will be refreshed on next fetch."
        )
    else:
        logging.info(f"ℹ️ No {cache_type.lower()} cache file found to clear.")


def get_cache_info(cache_file):
    """Get cache information for display."""
    if not os.path.exists(cache_file):
        return None

    try:
        with open(cache_file) as f:
            cache_info = json.load(f)

        cache_date = datetime.fromisoformat(cache_info.get("cached_at", "1970-01-01"))

        # Determine data count based on cache structure
        data = cache_info.get(
            "data", cache_info.get("riders_data", cache_info.get("race_data", {}))
        )
        data_count = len(data) if isinstance(data, dict) else 0

        return {
            "last_updated": cache_date.strftime("%Y-%m-%d %H:%M:%S"),
            "data_count": data_count,
        }
    except Exception:
        return None
