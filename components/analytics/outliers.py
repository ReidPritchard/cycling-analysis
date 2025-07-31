"""
Outlier detection and value identification analytics.
"""

import pandas as pd


def identify_performance_outliers(
    df: pd.DataFrame, z_threshold: float = 1.5
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Identify riders who are performing significantly better or worse than expected"""
    if len(df) < 5 or df["total_pcs_points"].sum() == 0:
        return [], []

    # Calculate expected performance based on star cost
    df_with_points = df[df["total_pcs_points"] > 0].copy()
    if len(df_with_points) < 5:
        return [], []

    # Calculate performance per star
    df_with_points["performance_ratio"] = (
        df_with_points["total_pcs_points"] / df_with_points["stars"]
    )

    # Calculate z-scores
    mean_ratio = df_with_points["performance_ratio"].mean()
    std_ratio = df_with_points["performance_ratio"].std()

    if std_ratio == 0:
        return [], []

    df_with_points["z_score"] = (
        df_with_points["performance_ratio"] - mean_ratio
    ) / std_ratio

    # Identify outliers
    overperformers = df_with_points[df_with_points["z_score"] > z_threshold]
    underperformers = df_with_points[df_with_points["z_score"] < -z_threshold]

    return overperformers, underperformers


def identify_value_picks(
    df: pd.DataFrame, min_points: int = 10, max_stars: int = 4
) -> pd.DataFrame:
    """Identify riders with high performance relative to low star cost"""
    if len(df) == 0:
        return pd.DataFrame()

    # Filter for low-cost riders with decent performance
    value_candidates = df[
        (df["total_pcs_points"] >= min_points) & (df["stars"] <= max_stars)
    ].copy()

    if len(value_candidates) == 0:
        return pd.DataFrame()

    # Sort by points per star ratio
    value_candidates["value_score"] = (
        value_candidates["total_pcs_points"] / value_candidates["stars"]
    )
    return value_candidates.nlargest(5, "value_score")
