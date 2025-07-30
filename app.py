import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import requests
import json
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(
    page_title="V/C Ratio Calculator",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-good { color: #28a745; }
    .status-warning { color: #ffc107; }
    .status-danger { color: #dc3545; }
    .status-critical { color: #6f42c1; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'vc_results' not in st.session_state:
    st.session_state.vc_results = None

def load_fdot_traffic_data(county="Palm Beach"):
    """
    Load traffic data from FDOT Traffic Online API
    This is a placeholder function - actual implementation would connect to FDOT API
    """
    # Placeholder data - in real implementation, this would query FDOT Traffic Online
    sample_data = {
        'segment_id': range(1, 21),
        'road_name': [f"Road {i}" for i in range(1, 21)],
        'functional_class': ['Arterial'] * 10 + ['Collector'] * 10,
        'current_volume': np.random.randint(5000, 25000, 20),
        'geometry': [f"POINT({-80.1 + i*0.01} {26.7 + i*0.01})" for i in range(20)]
    }
    return pd.DataFrame(sample_data)

def load_capacity_table():
    """
    Load roadway capacity table by functional classification
    """
    capacity_data = {
        'functional_class': ['Freeway', 'Arterial', 'Collector', 'Local'],
        'capacity_veh_day': [50000, 25000, 15000, 8000],
        'capacity_veh_hour': [2500, 1250, 750, 400]
    }
    return pd.DataFrame(capacity_data)

def calculate_vc_ratio(volume, capacity):
    """
    Calculate Volume/Capacity ratio
    """
    return volume / capacity if capacity > 0 else 0

def get_vc_status(vc_ratio):
    """
    Get status and color for V/C ratio
    """
    if vc_ratio < 0.7:
        return "Good", "status-good"
    elif vc_ratio < 0.9:
        return "Fair", "status-warning"
    elif vc_ratio <= 1.0:
        return "Poor", "status-danger"
    else:
        return "Critical", "status-critical"

def apply_growth_projection(base_volume, growth_rate, years=20):
    """
    Apply growth projection to base volume
    """
    return base_volume * (1 + growth_rate) ** years

def create_interactive_map(gdf):
    """
    Create an interactive map with V/C ratio visualization
    """
    # Create base map centered on Palm Beach County
    m = folium.Map(
        location=[26.7153, -80.0534],
        zoom_start=10,
        tiles='OpenStreetMap'
    )
    
    # Add V/C ratio visualization
    for idx, row in gdf.iterrows():
        vc_ratio = row['vc_ratio']
        status, color_class = get_vc_status(vc_ratio)
        
        # Determine color based on V/C ratio
        if vc_ratio < 0.7:
            color = 'green'
        elif vc_ratio < 0.9:
            color = 'yellow'
        elif vc_ratio <= 1.0:
            color = 'red'
        else:
            color = 'purple'
        
        # Add marker for each segment
        folium.CircleMarker(
            location=[26.7153 + idx*0.01, -80.0534 + idx*0.01],
            radius=10,
            popup=f"Road: {row['road_name']}<br>V/C: {vc_ratio:.2f}<br>Status: {status}",
            color=color,
            fill=True,
            fillOpacity=0.7
        ).add_to(m)
    
    return m

def generate_download_data(gdf):
    """
    Generate downloadable CSV data
    """
    output = BytesIO()
    gdf.to_csv(output, index=False)
    output.seek(0)
    return output

# Main application
def main():
    st.markdown('<h1 class="main-header">🚗 V/C Ratio Calculator</h1>', unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # County selection
        county = st.selectbox(
            "Select County",
            ["Palm Beach", "Broward", "Miami-Dade", "Monroe"],
            index=0
        )
        
        # Growth rate input
        st.subheader("Growth Projections")
        growth_rate = st.slider(
            "Annual Growth Rate (%)",
            min_value=0.0,
            max_value=5.0,
            value=2.0,
            step=0.1
        ) / 100
        
        # Projection years
        projection_years = st.slider(
            "Projection Years",
            min_value=5,
            max_value=30,
            value=20,
            step=5
        )
        
        # Data source selection
        st.subheader("Data Sources")
        data_source = st.radio(
            "Traffic Data Source",
            ["FDOT Traffic Online", "Upload CSV File", "Manual Entry"]
        )
        
        if data_source == "Upload CSV File":
            uploaded_file = st.file_uploader(
                "Upload Placer.ai CSV file",
                type=['csv']
            )
        
        # Load data button
        if st.button("Load Data", type="primary"):
            st.session_state.data_loaded = True
    
    # Main content area
    if st.session_state.data_loaded:
        # Load data
        with st.spinner("Loading traffic data..."):
            traffic_data = load_fdot_traffic_data(county)
            capacity_data = load_capacity_table()
        
        # Calculate V/C ratios
        st.header("📊 V/C Ratio Analysis")
        
        # Merge capacity data with traffic data
        traffic_data = traffic_data.merge(
            capacity_data[['functional_class', 'capacity_veh_day']],
            on='functional_class',
            how='left'
        )
        
        # Calculate current V/C ratios
        traffic_data['vc_ratio_current'] = traffic_data['current_volume'] / traffic_data['capacity_veh_day']
        
        # Calculate future volumes and V/C ratios
        traffic_data['future_volume'] = apply_growth_projection(
            traffic_data['current_volume'], 
            growth_rate, 
            projection_years
        )
        traffic_data['vc_ratio_future'] = traffic_data['future_volume'] / traffic_data['capacity_veh_day']
        
        # Store results in session state
        st.session_state.vc_results = traffic_data
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Segments",
                len(traffic_data),
                help="Number of roadway segments analyzed"
            )
        
        with col2:
            current_avg_vc = traffic_data['vc_ratio_current'].mean()
            st.metric(
                "Avg Current V/C",
                f"{current_avg_vc:.2f}",
                help="Average current volume/capacity ratio"
            )
        
        with col3:
            future_avg_vc = traffic_data['vc_ratio_future'].mean()
            st.metric(
                "Avg Future V/C",
                f"{future_avg_vc:.2f}",
                help=f"Average V/C ratio after {projection_years} years"
            )
        
        with col4:
            critical_segments = len(traffic_data[traffic_data['vc_ratio_future'] > 1.0])
            st.metric(
                "Critical Segments",
                critical_segments,
                help="Segments with V/C > 1.0 in future"
            )
        
        # Interactive map
        st.subheader("🗺️ Interactive Map")
        map_data = traffic_data.copy()
        map_data['vc_ratio'] = map_data['vc_ratio_future']  # Use future V/C for mapping
        
        # Create map
        map_obj = create_interactive_map(map_data)
        folium_static(map_obj, width=800, height=500)
        
        # V/C Ratio Distribution
        st.subheader("📈 V/C Ratio Distribution")
        
        # Create histogram
        fig = px.histogram(
            traffic_data,
            x='vc_ratio_future',
            nbins=20,
            title=f"Future V/C Ratio Distribution ({projection_years} years)",
            labels={'vc_ratio_future': 'V/C Ratio', 'count': 'Number of Segments'}
        )
        fig.add_vline(x=0.7, line_dash="dash", line_color="green", annotation_text="Good")
        fig.add_vline(x=0.9, line_dash="dash", line_color="yellow", annotation_text="Fair")
        fig.add_vline(x=1.0, line_dash="dash", line_color="red", annotation_text="Poor")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed results table
        st.subheader("📋 Detailed Results")
        
        # Add status column
        traffic_data['status'] = traffic_data['vc_ratio_future'].apply(
            lambda x: get_vc_status(x)[0]
        )
        
        # Display table with formatting
        display_cols = ['road_name', 'functional_class', 'current_volume', 
                       'vc_ratio_current', 'future_volume', 'vc_ratio_future', 'status']
        
        st.dataframe(
            traffic_data[display_cols].round(2),
            use_container_width=True
        )
        
        # Download section
        st.subheader("💾 Download Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Download CSV"):
                csv_data = generate_download_data(traffic_data)
                st.download_button(
                    label="Click to download",
                    data=csv_data.getvalue(),
                    file_name=f"vc_ratio_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("Download Excel"):
                # Create Excel file
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    traffic_data.to_excel(writer, sheet_name='V/C Results', index=False)
                    capacity_data.to_excel(writer, sheet_name='Capacity Data', index=False)
                
                output.seek(0)
                st.download_button(
                    label="Click to download",
                    data=output.getvalue(),
                    file_name=f"vc_ratio_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome to the V/C Ratio Calculator
        
        This tool helps transportation planners calculate and visualize Volume/Capacity (V/C) ratios 
        for roadway segments in Florida counties.
        
        ### Features:
        - 🔄 **Automated data loading** from FDOT Traffic Online
        - 📊 **Growth projections** with customizable rates
        - 🗺️ **Interactive mapping** with color-coded V/C ratios
        - 📈 **Statistical analysis** and reporting
        - 💾 **Export capabilities** (CSV/Excel)
        
        ### Getting Started:
        1. Configure your settings in the sidebar
        2. Select your county and growth parameters
        3. Click "Load Data" to begin analysis
        4. Explore the interactive maps and charts
        5. Download your results
        
        ### Color Coding:
        - 🟢 **Green**: V/C < 0.7 (Good)
        - 🟡 **Yellow**: V/C 0.7-0.9 (Fair)
        - 🔴 **Red**: V/C 0.9-1.0 (Poor)
        - 🟣 **Purple**: V/C > 1.0 (Critical)
        """)
        
        # Quick start guide
        with st.expander("📖 Quick Start Guide"):
            st.markdown("""
            ### Step-by-Step Instructions:
            
            1. **Select County**: Choose your target county from the sidebar
            2. **Set Growth Rate**: Adjust the annual growth rate (default: 2%)
            3. **Choose Data Source**: 
               - FDOT Traffic Online (automated)
               - Upload CSV file (manual)
               - Manual entry (for testing)
            4. **Load Data**: Click the "Load Data" button
            5. **Analyze Results**: Review maps, charts, and tables
            6. **Export**: Download results in your preferred format
            
            ### Data Requirements:
            - Roadway segment data (shapefile or geodatabase)
            - Traffic volume data (FDOT or Placer.ai)
            - Capacity tables by functional classification
            - TAZ-based growth factors (optional)
            """)

if __name__ == "__main__":
    main()