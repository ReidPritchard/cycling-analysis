"""
Calculation utilities for performance metrics and fantasy values.
"""


def get_fantasy_value_tier(pcs_per_star, percentiles):
    """Determine fantasy value tier based on PCS efficiency."""
    if pcs_per_star >= percentiles["90th"]:
        return (
            "🔥 Exceptional Value",
            "green",
            "Top 10% efficiency - excellent fantasy pick",
        )
    elif pcs_per_star >= percentiles["75th"]:
        return "⭐ Great Value", "blue", "Top 25% efficiency - strong fantasy option"
    elif pcs_per_star >= percentiles["50th"]:
        return "💰 Good Value", "orange", "Above average efficiency"
    elif pcs_per_star > 0:
        return "🔵 Standard", "gray", "Below average efficiency"
    else:
        return "❓ No Data", "red", "No points earned this season"


def calculate_percentiles(df):
    """Calculate performance percentiles for value assessment."""
    riders_with_points = df[df["pcs_per_star"] > 0]
    if riders_with_points.empty:
        return {"90th": 0, "75th": 0, "50th": 0, "25th": 0}

    return {
        "90th": riders_with_points["pcs_per_star"].quantile(0.9),
        "75th": riders_with_points["pcs_per_star"].quantile(0.75),
        "50th": riders_with_points["pcs_per_star"].quantile(0.5),
        "25th": riders_with_points["pcs_per_star"].quantile(0.25),
    }


def get_consistency_interpretation(score):
    """Interpret consistency score with proper logic (lower is better)."""
    if score < 0.3:
        return "Excellent", "green", "Very consistent performance"
    elif score < 0.7:
        return "Good", "blue", "Reasonably consistent performance"
    elif score < 1.0:
        return "Variable", "orange", "Inconsistent performance"
    else:
        return "Unpredictable", "red", "Highly variable performance"


def get_trend_interpretation(score):
    """Interpret trend score (negative = improving, positive = declining)."""
    if score < -0.5:
        return "Improving", "green", "📈", "Strong upward trend in performance"
    elif score < -0.1:
        return "Slight Upturn", "blue", "📈", "Moderate improvement in recent results"
    elif score > 0.5:
        return "Declining", "red", "📉", "Performance trending downward"
    elif score > 0.1:
        return "Slight Decline", "orange", "📉", "Minor decline in recent performance"
    else:
        return "Stable", "gray", "➡️", "Consistent performance level"
