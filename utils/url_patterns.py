def startlist_path(base_path: str = "race/tour-de-france-femmes/2025") -> str:
    """Generate the startlist path for a given base path."""
    # ex. "race/tour-de-france-femmes/2025/startlist"
    return f"{base_path}/startlist"


def race_climbs_path(base_path: str = "race/tour-de-france-femmes/2025") -> str:
    """Generate the climbs path for a given base path."""
    return f"{base_path}/route/climbs"
