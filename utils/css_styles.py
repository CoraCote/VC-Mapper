"""
CSS Styles - Custom CSS styling for the application
"""

import streamlit as st


def get_custom_css() -> str:
    """
    Get custom CSS styles for the application
    
    Returns:
        CSS string
    """
    return """
    <style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .metric-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2a5298;
        margin: 0.5rem 0;
    }
    
    .city-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        border-left: 4px solid #28a745;
    }
    
    .search-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .map-container {
        border: 2px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem;
        background: white;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 8px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #2a5298;
        color: white;
    }
    
    /* Custom sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Animation for loading states */
    .loading-animation {
        display: inline-block;
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    /* Enhanced button styling */
    .stButton > button {
        border-radius: 8px;
        border: none;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #2a5298 0%, #1e3c72 100%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }
    
    /* Enhanced selectbox styling */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 2px solid #e9ecef;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #2a5298;
        box-shadow: 0 0 0 0.2rem rgba(42, 82, 152, 0.25);
    }
    
    /* Enhanced metric styling */
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2a5298;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Enhanced dataframe styling */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Enhanced info/warning/error boxes */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stAlert[data-baseweb="notification"] > div {
        border-radius: 10px;
    }
    
    /* Enhanced sidebar */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Enhanced container backgrounds */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Enhanced chart styling */
    .plotly-graph-div {
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Enhanced text input styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e9ecef;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #2a5298;
        box-shadow: 0 0 0 0.2rem rgba(42, 82, 152, 0.25);
    }
    
    /* Enhanced slider styling */
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
    }
    
    /* Enhanced checkbox styling */
    .stCheckbox > label > div[data-testid="stMarkdownContainer"] > p {
        color: #2a5298;
        font-weight: 500;
    }
    
    /* Enhanced file uploader */
    .stFileUploader > div {
        border-radius: 10px;
        border: 2px dashed #2a5298;
        background: rgba(42, 82, 152, 0.05);
    }
    
    /* Enhanced success/error message styling */
    .stSuccess {
        background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .stError {
        background: linear-gradient(90deg, #dc3545 0%, #e74c3c 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .stWarning {
        background: linear-gradient(90deg, #ffc107 0%, #ffb300 100%);
        color: #212529;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .stInfo {
        background: linear-gradient(90deg, #17a2b8 0%, #20c997 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Enhanced progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
    }
    
    /* Enhanced expander */
    .streamlit-expanderHeader {
        background: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #e9ecef;
    }
    
    .streamlit-expanderContent {
        background: white;
        border-radius: 0 0 8px 8px;
        border: 1px solid #e9ecef;
        border-top: none;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem;
        }
        
        .main-header h1 {
            font-size: 1.8rem;
        }
        
        .stats-grid {
            grid-template-columns: 1fr;
        }
        
        .map-container {
            padding: 0.5rem;
        }
    }
    
    /* Dark mode compatibility */
    @media (prefers-color-scheme: dark) {
        .metric-container {
            background: #2d3748;
            color: white;
            border-left-color: #4299e1;
        }
        
        .city-card {
            background: #2d3748;
            color: white;
            border-left-color: #48bb78;
        }
        
        .search-container {
            background: #2d3748;
            color: white;
        }
        
        .map-container {
            background: #2d3748;
            border-color: #4a5568;
        }
    }
    </style>
    """


def load_css() -> None:
    """
    Load custom CSS styles into the Streamlit application
    """
    st.markdown(get_custom_css(), unsafe_allow_html=True)


def create_header(title: str, subtitle: str = "") -> None:
    """
    Create a styled header for the application
    
    Args:
        title: Main title text
        subtitle: Optional subtitle text
    """
    subtitle_html = f"<p style='margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.9;'>{subtitle}</p>" if subtitle else ""
    
    st.markdown(f"""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">{title}</h1>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def create_metric_container(title: str, content: str) -> None:
    """
    Create a styled metric container
    
    Args:
        title: Container title
        content: Container content
    """
    st.markdown(f"""
    <div class="metric-container">
        <h4>{title}</h4>
        {content}
    </div>
    """, unsafe_allow_html=True)


def create_city_card(rank: int, city_name: str, details: str) -> None:
    """
    Create a styled city card
    
    Args:
        rank: City ranking
        city_name: Name of the city
        details: City details
    """
    st.markdown(f"""
    <div class="city-card">
        <h4>#{rank} {city_name}</h4>
        <p>{details}</p>
    </div>
    """, unsafe_allow_html=True)


def create_search_container(content: str) -> None:
    """
    Create a styled search container
    
    Args:
        content: Container content
    """
    st.markdown(f"""
    <div class="search-container">
        {content}
    </div>
    """, unsafe_allow_html=True)


def create_footer() -> None:
    """
    Create a styled footer for the application
    """
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p><strong>Data Source:</strong> 
        <a href="https://gis.fdot.gov/arcgis/rest/services/Admin_Boundaries/FeatureServer/7/query" 
           target="_blank" style="color: #2a5298;">Florida Department of Transportation GIS API</a></p>
        <p>Built with ❤️ using Streamlit | Enhanced with Folium and Plotly</p>
    </div>
    """, unsafe_allow_html=True)