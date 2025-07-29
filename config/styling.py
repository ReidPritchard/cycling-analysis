"""
CSS styling for the Fantasy Cycling Stats app.
"""

# Main CSS styles for the application
MAIN_CSS = """
<style>
    .main-header {
        text-align: center;
        color: #2E8B57;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .cache-info {
        background-color: #2E8B5745;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #2E8B57;
    }
    
    .rider-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        border-left: 4px solid #2E8B57;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #2E8B57 0%, #228B22 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #228B22 0%, #2E8B57 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
"""

# Footer HTML
FOOTER_HTML = """
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>Fantasy Cycling Stats Dashboard • Built with Streamlit 🚴‍♀️</small>
</div>
"""
