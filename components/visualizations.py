"""
Data visualization components for the Fantasy Cycling Stats app.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional


def create_stats_overview(df):
    """Create an enhanced overview of key statistics with outlier insights"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Riders", len(df), help="Total number of fantasy riders")

    with col2:
        avg_stars = df["stars"].mean()
        st.metric(
            "Average Star Cost",
            f"{avg_stars:.1f}",
            help="Average star cost across all riders",
        )

    with col3:
        total_teams = df["team"].nunique()
        st.metric("Teams", total_teams, help="Number of unique teams")

    with col4:
        positions = df["position"].nunique()
        st.metric(
            "Styles", positions, help="Number of different rider styles/positions"
        )
    
    # Add performance insights
    if len(df) > 0 and df['total_pcs_points'].sum() > 0:
        st.divider()
        _show_performance_insights(df)


def create_star_cost_distribution_chart(df):
    """Create an enhanced chart of the star cost distribution with performance overlay"""
    star_counts = df["stars"].value_counts().sort_index(ascending=False)
    
    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add bar chart for rider counts
    fig.add_trace(
        go.Bar(
            x=star_counts.index,
            y=star_counts.values,
            name="Rider Count",
            marker_color="lightblue",
            opacity=0.7
        ),
        secondary_y=False,
    )
    
    # Add line chart for average performance by star cost
    if df['total_pcs_points'].sum() > 0:
        avg_performance = df.groupby('stars')['total_pcs_points'].mean()
        fig.add_trace(
            go.Scatter(
                x=avg_performance.index,
                y=avg_performance.values,
                mode='lines+markers',
                name="Avg PCS Points",
                line=dict(color="red", width=3),
                marker=dict(size=8)
            ),
            secondary_y=True,
        )
    
    # Update layout
    fig.update_xaxes(title_text="Star Cost")
    fig.update_yaxes(title_text="Number of Riders", secondary_y=False)
    fig.update_yaxes(title_text="Average PCS Points", secondary_y=True)
    fig.update_layout(
        title="Star Cost Distribution vs Performance",
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _show_performance_insights(df):
    """Show key performance insights and outliers"""
    col1, col2, col3 = st.columns(3)
    
    # Calculate outliers
    overperformers, underperformers = _identify_performance_outliers(df)
    value_picks = _identify_value_picks(df)
    
    with col1:
        if len(overperformers) > 0:
            st.metric(
                "🚀 Overperformers", 
                len(overperformers),
                help="Riders performing significantly better than expected for their star cost"
            )
        else:
            st.metric("🚀 Overperformers", "0")
    
    with col2:
        if len(underperformers) > 0:
            st.metric(
                "📉 Underperformers", 
                len(underperformers),
                help="Riders performing significantly worse than expected for their star cost"
            )
        else:
            st.metric("📉 Underperformers", "0")
    
    with col3:
        if len(value_picks) > 0:
            st.metric(
                "💎 Value Picks", 
                len(value_picks),
                help="High-performing riders with low star costs"
            )
        else:
            st.metric("💎 Value Picks", "0")


def _identify_performance_outliers(df, z_threshold=1.5):
    """Identify riders who are performing significantly better or worse than expected"""
    if len(df) < 5 or df['total_pcs_points'].sum() == 0:
        return [], []
    
    # Calculate expected performance based on star cost
    df_with_points = df[df['total_pcs_points'] > 0].copy()
    if len(df_with_points) < 5:
        return [], []
    
    # Calculate performance per star
    df_with_points['performance_ratio'] = df_with_points['total_pcs_points'] / df_with_points['stars']
    
    # Calculate z-scores
    mean_ratio = df_with_points['performance_ratio'].mean()
    std_ratio = df_with_points['performance_ratio'].std()
    
    if std_ratio == 0:
        return [], []
    
    df_with_points['z_score'] = (df_with_points['performance_ratio'] - mean_ratio) / std_ratio
    
    # Identify outliers
    overperformers = df_with_points[df_with_points['z_score'] > z_threshold]
    underperformers = df_with_points[df_with_points['z_score'] < -z_threshold]
    
    return overperformers, underperformers


def _identify_value_picks(df, min_points=10, max_stars=4):
    """Identify riders with high performance relative to low star cost"""
    if len(df) == 0:
        return pd.DataFrame()
    
    # Filter for low-cost riders with decent performance
    value_candidates = df[
        (df['total_pcs_points'] >= min_points) & 
        (df['stars'] <= max_stars)
    ].copy()
    
    if len(value_candidates) == 0:
        return pd.DataFrame()
    
    # Sort by points per star ratio
    value_candidates['value_score'] = value_candidates['total_pcs_points'] / value_candidates['stars']
    return value_candidates.nlargest(5, 'value_score')


def create_visualizations(df):
    """Create reorganized interactive charts with outlier highlighting"""
    
    # Section 1: Value Analysis - Most Important Charts
    st.subheader("💰 Value Analysis")
    _create_value_analysis_charts(df)
    
    st.divider()
    
    # Section 2: Performance Distribution
    st.subheader("📊 Performance Distribution")
    _create_performance_distribution_charts(df)
    
    st.divider()
    
    # Section 3: Team Analysis  
    st.subheader("🏆 Team Analysis")
    _create_team_analysis_charts(df)


def _create_value_analysis_charts(df):
    """Create charts focused on value and outlier identification"""
    col1, col2 = st.columns(2)
    
    with col1:
        # Enhanced scatter plot with outlier highlighting
        _create_outlier_scatter_plot(df)
    
    with col2:
        # Performance efficiency chart
        _create_efficiency_chart(df)


def _create_outlier_scatter_plot(df):
    """Create scatter plot highlighting overperformers and underperformers"""
    if len(df) == 0 or df['total_pcs_points'].sum() == 0:
        st.info("No performance data available for scatter plot")
        return
    
    # Get outliers
    overperformers, underperformers = _identify_performance_outliers(df)
    
    # Create scatter plot
    fig = go.Figure()
    
    # Add all riders as base layer
    fig.add_trace(go.Scatter(
        x=df['stars'],
        y=df['total_pcs_points'],
        mode='markers',
        name='All Riders',
        marker=dict(
            size=8,
            color='lightgray',
            opacity=0.6
        ),
        text=df['full_name'] + '<br>' + df['team'] + '<br>' + df['position'],
        hovertemplate='<b>%{text}</b><br>Stars: %{x}<br>PCS Points: %{y}<extra></extra>'
    ))
    
    # Highlight overperformers
    if len(overperformers) > 0:
        fig.add_trace(go.Scatter(
            x=overperformers['stars'],
            y=overperformers['total_pcs_points'],
            mode='markers',
            name='🚀 Overperformers',
            marker=dict(
                size=12,
                color='green',
                symbol='star',
                line=dict(width=2, color='darkgreen')
            ),
            text=overperformers['full_name'] + '<br>' + overperformers['team'] + '<br>Z-score: ' + overperformers['z_score'].round(2).astype(str),
            hovertemplate='<b>%{text}</b><br>Stars: %{x}<br>PCS Points: %{y}<extra></extra>'
        ))
    
    # Highlight underperformers
    if len(underperformers) > 0:
        fig.add_trace(go.Scatter(
            x=underperformers['stars'],
            y=underperformers['total_pcs_points'],
            mode='markers',
            name='📉 Underperformers',
            marker=dict(
                size=12,
                color='red',
                symbol='x',
                line=dict(width=2, color='darkred')
            ),
            text=underperformers['full_name'] + '<br>' + underperformers['team'] + '<br>Z-score: ' + underperformers['z_score'].round(2).astype(str),
            hovertemplate='<b>%{text}</b><br>Stars: %{x}<br>PCS Points: %{y}<extra></extra>'
        ))
    
    # Add trend line if we have enough data
    if len(df[df['total_pcs_points'] > 0]) > 5:
        x_data = df[df['total_pcs_points'] > 0]['stars']
        y_data = df[df['total_pcs_points'] > 0]['total_pcs_points']
        
        # Calculate trend line
        z = np.polyfit(x_data, y_data, 1)
        p = np.poly1d(z)
        
        fig.add_trace(go.Scatter(
            x=sorted(x_data),
            y=p(sorted(x_data)),
            mode='lines',
            name='Expected Performance',
            line=dict(dash='dash', color='orange', width=2)
        ))
    
    fig.update_layout(
        title="Performance vs Star Cost (Outliers Highlighted)",
        xaxis_title="Star Cost",
        yaxis_title="Total PCS Points",
        height=500,
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _create_efficiency_chart(df):
    """Create efficiency chart showing points per star by position"""
    if len(df) == 0 or df['total_pcs_points'].sum() == 0:
        st.info("No performance data available for efficiency chart")
        return
    
    # Calculate efficiency by position
    df_with_points = df[df['total_pcs_points'] > 0].copy()
    
    fig = px.box(
        df_with_points,
        x="position",
        y="pcs_per_star",
        color="position",
        title="Efficiency by Position (PCS Points per Star)",
        hover_data=["full_name", "team", "stars", "total_pcs_points"],
        points="outliers"  # Show outlier points
    )
    
    fig.update_layout(
        showlegend=False, 
        height=500,
        xaxis_title="Rider Position/Style",
        yaxis_title="PCS Points per Star"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _create_performance_distribution_charts(df):
    """Create charts showing performance distributions"""
    col1, col2 = st.columns(2)
    
    with col1:
        # Stars distribution by position
        fig = px.violin(
            df,
            x="position",
            y="stars",
            color="position",
            title="Star Cost Distribution by Position",
            hover_data=["full_name", "team"],
            box=True
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Performance tiers visualization
        if df['total_pcs_points'].sum() > 0:
            _create_performance_tiers_chart(df)
        else:
            st.info("No performance data available")


def _create_performance_tiers_chart(df):
    """Create a clearer performance visualization using tiers and rankings"""
    df_with_points = df[df['total_pcs_points'] > 0].copy()
    
    if len(df_with_points) == 0:
        st.info("No performance data available")
        return
    
    # Calculate performance tiers based on quartiles
    points_data = df_with_points['total_pcs_points']
    q25 = points_data.quantile(0.25)
    q50 = points_data.quantile(0.50)  # median
    q75 = points_data.quantile(0.75)
    
    # Assign performance tiers
    def assign_tier(points):
        if points >= q75:
            return "Elite (Top 25%)"
        elif points >= q50:
            return "Strong (25-50%)"
        elif points >= q25:
            return "Average (50-75%)"
        else:
            return "Struggling (Bottom 25%)"
    
    df_with_points['performance_tier'] = df_with_points['total_pcs_points'].apply(assign_tier)
    
    # Create a stacked bar chart showing position distribution within each tier
    tier_position_counts = df_with_points.groupby(['performance_tier', 'position']).size().reset_index(name='count')
    
    # Define tier order for proper display
    tier_order = ["Elite (Top 25%)", "Strong (25-50%)", "Average (50-75%)", "Struggling (Bottom 25%)"]
    tier_position_counts['performance_tier'] = pd.Categorical(
        tier_position_counts['performance_tier'], 
        categories=tier_order, 
        ordered=True
    )
    tier_position_counts = tier_position_counts.sort_values('performance_tier')
    
    # Create the visualization
    fig = px.bar(
        tier_position_counts,
        x='performance_tier',
        y='count',
        color='position',
        title='Performance Tiers of Rider\'s with Points by Position',
        labels={
            'performance_tier': 'Performance Tier',
            'count': 'Number of Riders',
            'position': 'Rider Position'
        },
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    
    # Add tier threshold annotations
    fig.add_hline(
        y=0, 
        annotation_text=f"Thresholds: Elite ≥{q75:.0f} | Strong ≥{q50:.0f} | Average ≥{q25:.0f} pts",
        annotation_position="top right",
        line_width=0
    )
    
    fig.update_layout(
        height=400,
        xaxis_tickangle=-45,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add summary stats below the chart
    col1, col2, col3, col4 = st.columns(4)
    
    tier_counts = df_with_points['performance_tier'].value_counts()
    
    with col1:
        elite_count = tier_counts.get("Elite (Top 25%)", 0)
        st.metric("🏆 Elite", elite_count, help=f"≥{q75:.0f} PCS points")
    
    with col2:
        strong_count = tier_counts.get("Strong (25-50%)", 0)
        st.metric("💪 Strong", strong_count, help=f"{q50:.0f}-{q75:.0f} PCS points")
    
    with col3:
        average_count = tier_counts.get("Average (50-75%)", 0)
        st.metric("📊 Average", average_count, help=f"{q25:.0f}-{q50:.0f} PCS points")
    
    with col4:
        struggling_count = tier_counts.get("Struggling (Bottom 25%)", 0)
        st.metric("📉 Struggling", struggling_count, help=f"<{q25:.0f} PCS points")


def _create_team_analysis_charts(df):
    """Create team-focused analysis charts"""
    col1, col2 = st.columns(2)
    
    with col1:
        # Team efficiency
        if df['total_pcs_points'].sum() > 0:
            team_stats = df.groupby("team").agg({
                'total_pcs_points': 'sum',
                'stars': 'sum',
                'full_name': 'count'
            }).reset_index()
            team_stats = team_stats[team_stats['full_name'] >= 2]  # Teams with 2+ riders
            team_stats['team_efficiency'] = team_stats['total_pcs_points'] / team_stats['stars']
            team_stats = team_stats.sort_values('team_efficiency', ascending=False).head(10)
            
            fig = px.bar(
                team_stats,
                x="team_efficiency",
                y="team",
                orientation="h",
                title="Most Efficient Teams (Points per Star)",
                labels={"team_efficiency": "PCS Points per Star", "team": "Team"},
                color="team_efficiency",
                color_continuous_scale="viridis"
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance data available for team efficiency")
    
    with col2:
        # Team depth analysis - showing impact of rider dropouts
        team_overview = df.groupby("team").agg({
            'stars': ['mean', 'sum'],
            'full_name': 'count',
            'total_pcs_points': 'sum'
        }).reset_index()
        team_overview.columns = ['team', 'avg_stars', 'total_stars', 'rider_count', 'total_points']
        team_overview = team_overview[team_overview['rider_count'] >= 2]
        
        # Calculate dropouts (assuming teams start with 7 riders)
        team_overview['dropouts'] = 7 - team_overview['rider_count']
        team_overview['roster_strength'] = team_overview['rider_count'] / 7  # Percentage of original roster
        
        # Create color mapping based on dropout severity
        team_overview['dropout_category'] = team_overview['dropouts'].apply(
            lambda x: 'No Dropouts' if x == 0 else f'{x} Dropout{"s" if x > 1 else ""}'
        )
        
        fig = px.scatter(
            team_overview,
            x="avg_stars",
            y="total_points" if df['total_pcs_points'].sum() > 0 else "total_stars",
            color="dropout_category",
            hover_name="team",
            hover_data={
                "dropouts": True,
                "rider_count": True,
                "roster_strength": ":.1%"
            },
            title="Team Depth Analysis (Impact of Dropouts)",
            labels={
                "avg_stars": "Average Star Cost per Rider",
                "total_points": "Total PCS Points" if df['total_pcs_points'].sum() > 0 else "Total Stars",
                "rider_count": "Current Roster Size",
                "dropout_category": "Dropout Status"
            },
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig, use_container_width=True)


def show_detailed_analytics(filtered_riders):
    """Show enhanced detailed analytics section"""
    if len(filtered_riders) > 0:
        create_visualizations(filtered_riders)

        # Outlier Analysis Section
        st.subheader("🎯 Outlier Analysis")
        _show_outlier_analysis(filtered_riders)
        
        st.divider()
        
        # Statistical Summary
        st.subheader("📊 Statistical Insights")
        _show_statistical_insights(filtered_riders)

    else:
        st.info("No riders match the current filters. Please adjust your selection.")


def _show_outlier_analysis(df):
    """Show detailed outlier analysis with actionable insights"""
    col1, col2, col3 = st.columns(3)
    
    # Get outliers and value picks
    overperformers, underperformers = _identify_performance_outliers(df)
    value_picks = _identify_value_picks(df)
    
    with col1:
        st.write("**🚀 Top Overperformers**")
        if len(overperformers) > 0:
            display_df = overperformers.nlargest(5, 'z_score')[
                ["full_name", "stars", "total_pcs_points", "z_score"]
            ].copy()
            display_df.columns = ["Rider", "Stars", "PCS Points", "Z-Score"]
            display_df["Z-Score"] = display_df["Z-Score"].round(2)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No significant overperformers identified")
    
    with col2:
        st.write("**📉 Top Underperformers**")
        if len(underperformers) > 0:
            display_df = underperformers.nsmallest(5, 'z_score')[
                ["full_name", "stars", "total_pcs_points", "z_score"]
            ].copy()
            display_df.columns = ["Rider", "Stars", "PCS Points", "Z-Score"]
            display_df["Z-Score"] = display_df["Z-Score"].round(2)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No significant underperformers identified")
    
    with col3:
        st.write("**💎 Best Value Picks**")
        if len(value_picks) > 0:
            display_df = value_picks[
                ["full_name", "stars", "total_pcs_points", "value_score"]
            ].copy()
            display_df.columns = ["Rider", "Stars", "PCS Points", "Value Score"]
            display_df["Value Score"] = display_df["Value Score"].round(2)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No value picks identified")


def _show_statistical_insights(df):
    """Show statistical insights and correlations"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Performance Statistics**")
        if df['total_pcs_points'].sum() > 0:
            stats_data = {
                "Metric": [
                    "Total Riders with Points",
                    "Average PCS Points",
                    "Median PCS Points", 
                    "Standard Deviation",
                    "Best Performance",
                    "Points per Star (Avg)"
                ],
                "Value": [
                    len(df[df['total_pcs_points'] > 0]),
                    f"{df[df['total_pcs_points'] > 0]['total_pcs_points'].mean():.1f}",
                    f"{df[df['total_pcs_points'] > 0]['total_pcs_points'].median():.1f}",
                    f"{df[df['total_pcs_points'] > 0]['total_pcs_points'].std():.1f}",
                    f"{df['total_pcs_points'].max():.0f}",
                    f"{df[df['total_pcs_points'] > 0]['pcs_per_star'].mean():.2f}"
                ]
            }
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        else:
            st.info("No performance data available")
    
    with col2:
        st.write("**Position Analysis**")
        if df['total_pcs_points'].sum() > 0:
            position_stats = df[df['total_pcs_points'] > 0].groupby('position').agg({
                'total_pcs_points': ['count', 'mean', 'std'],
                'pcs_per_star': 'mean'
            }).round(2)
            
            position_stats.columns = ['Count', 'Avg Points', 'Std Dev', 'Efficiency']
            position_stats = position_stats.sort_values('Efficiency', ascending=False)
            st.dataframe(position_stats, use_container_width=True)
        else:
            st.info("No performance data available")
