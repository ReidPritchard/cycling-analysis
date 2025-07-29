"""
Configuration settings for the Fantasy Cycling Stats app.
"""

from datetime import timedelta

# Fantasy data file scraped from TdF site (star data)
FANTASY_DATA_FILE = "fantasy-data.json"

# Cache file settings
PCS_CACHE_FILE = "pcs_data_cache.json"
RACE_CACHE_FILE = "race_data_cache.json"
CACHE_EXPIRY_DAYS = 7  # Cache expires after 7 days
CACHE_EXPIRY_DELTA = timedelta(days=CACHE_EXPIRY_DAYS)

# Race settings
# TDF_FEMMES_2025_PATH = "race/tour-de-france-femmes/2025"
SUPPORTED_RACES = {
    "TDF_FEMMES_2025": {
        "name": "Tour de France Femmes 2025",
        "url_path": "race/tour-de-france-femmes/2025",
        "startlist_cache_path": "tdf_femmes_2025_startlist.json",
    },
}

# Streamlit page configuration
PAGE_CONFIG = {
    "page_title": "Fantasy Cycling Stats",
    "page_icon": "🚴",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Position icons mapping
POSITION_ICONS = {
    "Leader": "🏆",
    "Sprint": "🏁",
    "Climber": "⛰️",
    "All-Rounder": "🚴",
}
