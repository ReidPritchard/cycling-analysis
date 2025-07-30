# Fantasy Cycling Stats Dashboard

A Streamlit web application for analyzing fantasy cycling rider statistics and Tour de France Femmes 2025 race data.

## Quick Start

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**

   ```bash
   uv run streamlit run main.py
    # or if you have streamlit installed globally
   streamlit run app.py
   ```

3. **Open your browser** to the URL shown in the terminal (usually `http://localhost:8501`)

## Features

- **📊 Overview**: Key statistics and performance insights
- **🏆 Riders**: Browse and filter rider data with cards or table view
- **📈 Analytics**: Advanced visualizations with outlier detection and value analysis

## Key Analytics

- **Outlier Detection**: Identifies overperformers and underperformers using statistical analysis
- **Value Picks**: Highlights high-performing riders with low star costs
- **Performance Tiers**: Categorizes riders into Elite, Strong, Average, and Struggling tiers
- **Team Analysis**: Shows team efficiency and impact of rider dropouts

## Data Sources

- Fantasy rider data from `fantasy-data.json` (scraped from TdF fantasy game)
- Real cycling performance data from ProCyclingStats.com
- Cached data expires after 7 days for optimal performance

## Requirements

- Python 3.7+
- Streamlit
- Plotly
- Pandas
- ProCyclingStats library

---

_Built with ❤️ for fantasy cycling enthusiasts_

