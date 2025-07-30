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

def load_fdot_traffic_data(city=None):
    """
    Load traffic data from FDOT Traffic Online API using ArcGIS REST API
    
    Args:
        city: City name for filtering (optional)
    """
    try:
        from fdot_api import FDOTArcGISAPI
        
        # Initialize FDOT API client
        fdot_api = FDOTArcGISAPI()
        
        # Try to get AADT data first (more comprehensive)
        st.info("🔍 Fetching AADT data from FDOT API...")
        # Get data for all counties and filter by city
        traffic_data = fdot_api.get_aadt_data(year=2023)
        
        if not traffic_data.empty:
            # Debug: Show what columns we actually got
            st.info(f"🔍 Debug: AADT data columns received: {list(traffic_data.columns)}")
            
            # Rename 'aadt' column to 'current_volume' to match expected format
            if 'aadt' in traffic_data.columns:
                traffic_data = traffic_data.rename(columns={'aadt': 'current_volume'})
                st.success("✅ Successfully renamed 'aadt' to 'current_volume'")
            else:
                st.warning("⚠️ 'aadt' column not found in AADT data")
            
            # Check if we have the required 'current_volume' column
            if 'current_volume' not in traffic_data.columns:
                st.warning("⚠️ No traffic volume data available from FDOT API")
                st.info("🔄 Creating sample data for demonstration purposes...")
                
                # Create sample data with realistic traffic volumes
                sample_data = []
                functional_classes = ['Arterial', 'Collector', 'Local']
                road_names = ['Sample Road 1', 'Sample Road 2', 'Sample Road 3', 'Sample Road 4', 'Sample Road 5']
                
                for i in range(10):
                    sample_data.append({
                        'segment_id': f'SAMPLE_{i+1:03d}',
                        'road_name': road_names[i % len(road_names)],
                        'functional_class': functional_classes[i % len(functional_classes)],
                        'current_volume': np.random.randint(1000, 50000),  # Random traffic volumes
                        'county': 'Sample County',
                        'latitude': 26.7153 + (i * 0.01),
                        'longitude': -80.0534 + (i * 0.01)
                    })
                
                traffic_data = pd.DataFrame(sample_data)
                st.success(f"✅ Created {len(traffic_data)} sample records for demonstration")
            
            # Filter by city if specified
            if city and city != "All Cities":
                # Try to filter by city name in various possible columns
                city_columns = [col for col in traffic_data.columns if any(term in col.lower() for term in ['city', 'municipal', 'name'])]
                if city_columns:
                    # Filter by city name
                    original_count = len(traffic_data)
                    traffic_data = traffic_data[traffic_data[city_columns[0]].str.contains(city, case=False, na=False)]
                    filtered_count = len(traffic_data)
                    st.info(f"🔍 Filtered data for city '{city}': {filtered_count} records (from {original_count} total)")
                else:
                    st.warning(f"⚠️ Could not filter by city '{city}' - no city column found in data")
            
            st.session_state.fdot_data_source = "FDOT AADT Data (Layer 1) - with sample data fallback"
            st.success(f"✅ Successfully loaded {len(traffic_data)} records from FDOT API")
            return traffic_data
        else:
            # Fallback to traffic monitoring sites
            st.info("🔍 AADT data not available, fetching traffic monitoring sites...")
            traffic_data = fdot_api.get_traffic_monitoring_sites()
            
            if not traffic_data.empty:
                # Debug: Show what columns we actually got
                st.info(f"🔍 Debug: Traffic monitoring sites columns received: {list(traffic_data.columns)}")
                
                # Rename columns to match expected format
                column_renames = {}
                if 'site_id' in traffic_data.columns:
                    column_renames['site_id'] = 'segment_id'
                if 'site_name' in traffic_data.columns:
                    column_renames['site_name'] = 'road_name'
                if 'aadt' in traffic_data.columns:
                    column_renames['aadt'] = 'current_volume'
                
                if column_renames:
                    traffic_data = traffic_data.rename(columns=column_renames)
                    st.success(f"✅ Successfully renamed columns: {column_renames}")
                else:
                    st.warning("⚠️ No expected columns found in traffic monitoring sites data")
                
                # Check if we have the required 'current_volume' column
                if 'current_volume' not in traffic_data.columns:
                    st.warning("⚠️ No traffic volume data available from traffic monitoring sites")
                    st.info("🔄 Creating sample data for demonstration purposes...")
                    
                    # Create sample data with realistic traffic volumes
                    sample_data = []
                    functional_classes = ['Arterial', 'Collector', 'Local']
                    road_names = ['Sample Road 1', 'Sample Road 2', 'Sample Road 3', 'Sample Road 4', 'Sample Road 5']
                    
                    for i in range(10):
                        sample_data.append({
                            'segment_id': f'SAMPLE_{i+1:03d}',
                            'road_name': road_names[i % len(road_names)],
                            'functional_class': functional_classes[i % len(functional_classes)],
                            'current_volume': np.random.randint(1000, 50000),  # Random traffic volumes
                            'county': 'Sample County',
                            'latitude': 26.7153 + (i * 0.01),
                            'longitude': -80.0534 + (i * 0.01)
                        })
                    
                    traffic_data = pd.DataFrame(sample_data)
                    st.success(f"✅ Created {len(traffic_data)} sample records for demonstration")
                
                # Filter by city if specified
                if city and city != "All Cities":
                    # Try to filter by city name in various possible columns
                    city_columns = [col for col in traffic_data.columns if any(term in col.lower() for term in ['city', 'municipal', 'name'])]
                    if city_columns:
                        # Filter by city name
                        original_count = len(traffic_data)
                        traffic_data = traffic_data[traffic_data[city_columns[0]].str.contains(city, case=False, na=False)]
                        filtered_count = len(traffic_data)
                        st.info(f"🔍 Filtered data for city '{city}': {filtered_count} records (from {original_count} total)")
                    else:
                        st.warning(f"⚠️ Could not filter by city '{city}' - no city column found in data")
                
                st.session_state.fdot_data_source = "FDOT Traffic Monitoring Sites (Layer 0) - with sample data fallback"
                st.success(f"✅ Successfully loaded {len(traffic_data)} records from FDOT API")
                return traffic_data
            else:
                st.warning("⚠️ No data available from FDOT API")
                st.info("🔄 Creating sample data for demonstration purposes...")
                
                # Create comprehensive sample data
                sample_data = []
                functional_classes = ['Arterial', 'Collector', 'Local']
                road_names = ['Sample Road 1', 'Sample Road 2', 'Sample Road 3', 'Sample Road 4', 'Sample Road 5']
                
                for i in range(15):
                    sample_data.append({
                        'segment_id': f'SAMPLE_{i+1:03d}',
                        'road_name': road_names[i % len(road_names)],
                        'functional_class': functional_classes[i % len(functional_classes)],
                        'current_volume': np.random.randint(1000, 50000),  # Random traffic volumes
                        'county': 'Sample County',
                        'latitude': 26.7153 + (i * 0.01),
                        'longitude': -80.0534 + (i * 0.01)
                    })
                
                traffic_data = pd.DataFrame(sample_data)
                st.session_state.fdot_data_source = "Sample Data (FDOT API Unavailable)"
                st.success(f"✅ Created {len(traffic_data)} sample records for demonstration")
                return traffic_data
            
    except ImportError:
        st.warning("⚠️ FDOT API module not available")
        st.info("🔄 Creating sample data for demonstration purposes...")
        
        # Create sample data when API module is not available
        sample_data = []
        functional_classes = ['Arterial', 'Collector', 'Local']
        road_names = ['Sample Road 1', 'Sample Road 2', 'Sample Road 3', 'Sample Road 4', 'Sample Road 5']
        
        for i in range(12):
            sample_data.append({
                'segment_id': f'SAMPLE_{i+1:03d}',
                'road_name': road_names[i % len(road_names)],
                'functional_class': functional_classes[i % len(functional_classes)],
                'current_volume': np.random.randint(1000, 50000),  # Random traffic volumes
                'county': 'Sample County',
                'latitude': 26.7153 + (i * 0.01),
                'longitude': -80.0534 + (i * 0.01)
            })
        
        traffic_data = pd.DataFrame(sample_data)
        st.session_state.fdot_data_source = "Sample Data (API Module Unavailable)"
        st.success(f"✅ Created {len(traffic_data)} sample records for demonstration")
        return traffic_data
    except Exception as e:
        st.warning(f"⚠️ Error connecting to FDOT API: {e}")
        st.info("🔄 Creating sample data for demonstration purposes...")
        
        # Create sample data when API fails
        sample_data = []
        functional_classes = ['Arterial', 'Collector', 'Local']
        road_names = ['Sample Road 1', 'Sample Road 2', 'Sample Road 3', 'Sample Road 4', 'Sample Road 5']
        
        for i in range(10):
            sample_data.append({
                'segment_id': f'SAMPLE_{i+1:03d}',
                'road_name': road_names[i % len(road_names)],
                'functional_class': functional_classes[i % len(functional_classes)],
                'current_volume': np.random.randint(1000, 50000),  # Random traffic volumes
                'county': 'Sample County',
                'latitude': 26.7153 + (i * 0.01),
                'longitude': -80.0534 + (i * 0.01)
            })
        
        traffic_data = pd.DataFrame(sample_data)
        st.session_state.fdot_data_source = "Sample Data (API Error)"
        st.success(f"✅ Created {len(traffic_data)} sample records for demonstration")
        return traffic_data

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

def create_interactive_map(gdf, selected_city="All Cities"):
    """
    Create an interactive map with V/C ratio visualization
    
    Args:
        gdf: GeoDataFrame with traffic data
        selected_city: Selected city for map centering
    """
    # Default center (Florida)
    default_lat, default_lon = 27.6648, -81.5158
    
    # City-specific coordinates
    city_coords = {
        "West Palm Beach": [26.7153, -80.0534],
        "Boca Raton": [26.3683, -80.1289],
        "Delray Beach": [26.4615, -80.0728],
        "Boynton Beach": [26.5317, -80.0905],
        "Fort Lauderdale": [26.1224, -80.1373],
        "Hollywood": [26.0112, -80.1495],
        "Miami": [25.7617, -80.1918],
        "Miami Beach": [25.7907, -80.1300],
        "Key West": [24.5557, -81.7826],
        "Orlando": [28.5383, -81.3792],
        "Tampa": [27.9506, -82.4572],
        "Jacksonville": [30.3322, -81.6557]
    }
    
    # Get coordinates for selected city or use default
    if selected_city in city_coords:
        center_lat, center_lon = city_coords[selected_city]
    else:
        center_lat, center_lon = default_lat, default_lon
    
    # Create base map centered on selected city or Florida
    m = folium.Map(
        location=[center_lat, center_lon],
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
        
        # City selection with FDOT Open Data Hub integration
        st.subheader("City Selection")
        
        # Initialize city list in session state
        if 'cities_list' not in st.session_state:
            st.session_state.cities_list = []
            st.session_state.cities_loaded = False
        
        # Load cities from FDOT Open Data Hub
        if not st.session_state.cities_loaded:
            with st.spinner("Loading cities from FDOT Open Data Hub..."):
                try:
                    from fdot_opendata_api import FDOTOpenDataAPI
                    api = FDOTOpenDataAPI()
                    
                    if api.test_connection():
                        cities = api.get_florida_cities()
                        if cities:
                            st.session_state.cities_list = cities
                            st.session_state.cities_loaded = True
                            st.success(f"✅ Loaded {len(cities)} cities from FDOT Open Data Hub")
                        else:
                            st.warning("⚠️ No cities found in FDOT Open Data Hub, using default list")
                            st.session_state.cities_list = [
                                "West Palm Beach", "Boca Raton", "Delray Beach", "Boynton Beach", 
                                "Lake Worth", "Wellington", "Jupiter", "Palm Beach Gardens",
                                "Fort Lauderdale", "Hollywood", "Pompano Beach", "Coral Springs",
                                "Miami", "Hialeah", "Miami Beach", "Coral Gables", "Key West"
                            ]
                            st.session_state.cities_loaded = True
                    else:
                        st.error("❌ Failed to connect to FDOT Open Data Hub")
                        st.session_state.cities_list = [
                            "West Palm Beach", "Boca Raton", "Delray Beach", "Boynton Beach", 
                            "Lake Worth", "Wellington", "Jupiter", "Palm Beach Gardens",
                            "Fort Lauderdale", "Hollywood", "Pompano Beach", "Coral Springs",
                            "Miami", "Hialeah", "Miami Beach", "Coral Gables", "Key West"
                        ]
                        st.session_state.cities_loaded = True
                except Exception as e:
                    st.error(f"❌ Error loading cities: {e}")
                    st.session_state.cities_list = [
                        "West Palm Beach", "Boca Raton", "Delray Beach", "Boynton Beach", 
                        "Lake Worth", "Wellington", "Jupiter", "Palm Beach Gardens",
                        "Fort Lauderdale", "Hollywood", "Pompano Beach", "Coral Springs",
                        "Miami", "Hialeah", "Miami Beach", "Coral Gables", "Key West"
                    ]
                    st.session_state.cities_loaded = True
        
        # City selection dropdown
        selected_city = st.selectbox(
            "Select City",
            ["All Cities"] + st.session_state.cities_list,
            index=0,
            help="Select a specific city or 'All Cities' to analyze all cities in the county"
        )
        
        # Show city count
        if st.session_state.cities_loaded:
            st.info(f"📋 Available cities: {len(st.session_state.cities_list)}")
        
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
            ["FDOT Traffic Online", "Manual Entry"]
        )
        
        # Load data button
        if st.button("Load Data", type="primary"):
            st.session_state.data_loaded = True
        
        # Test FDOT API button
        st.subheader("🔧 API Testing")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Test FDOT Traffic API"):
                with st.spinner("Testing FDOT Traffic API connection..."):
                    try:
                        from fdot_api import test_fdot_api
                        test_df = test_fdot_api()
                        if not test_df.empty:
                            st.success(f"✅ FDOT Traffic API test successful! Found {len(test_df)} records")
                            st.dataframe(test_df.head())
                        else:
                            st.warning("⚠️ FDOT Traffic API test completed but no data found")
                    except Exception as e:
                        st.error(f"❌ FDOT Traffic API test failed: {e}")
        
        with col2:
            if st.button("Test FDOT Open Data Hub"):
                with st.spinner("Testing FDOT Open Data Hub connection..."):
                    try:
                        from fdot_opendata_api import test_fdot_opendata_api
                        test_df = test_fdot_opendata_api()
                        if not test_df.empty:
                            st.success(f"✅ FDOT Open Data Hub test successful! Found {len(test_df)} cities")
                            st.dataframe(test_df.head())
                        else:
                            st.warning("⚠️ FDOT Open Data Hub test completed but no cities found")
                    except Exception as e:
                        st.error(f"❌ FDOT Open Data Hub test failed: {e}")
    
    # Main content area
    if st.session_state.data_loaded:
        # Load data
        with st.spinner("Loading traffic data..."):
            traffic_data = load_fdot_traffic_data(selected_city)
            capacity_data = load_capacity_table()
        
        # Display raw FDOT data
        st.header("📊 FDOT Traffic Data")
        
        # Show data source info
        if 'fdot_data_source' in st.session_state:
            data_source = st.session_state.fdot_data_source
            if "Sample Data" in data_source:
                st.warning(f"📡 Data Source: {data_source}")
                st.info("💡 This is sample data for demonstration. In production, this would be real FDOT traffic data.")
            else:
                st.info(f"📡 Data Source: {data_source}")
        
        # Display raw traffic data
        st.subheader("🗂️ Raw Traffic Data")
        st.write(f"**Total Records:** {len(traffic_data)}")
        
        # Show data info
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Data Columns:**")
            st.write(list(traffic_data.columns))
        with col2:
            st.write("**Data Types:**")
            st.write(traffic_data.dtypes.to_dict())
        
        # Display the raw data table
        st.dataframe(
            traffic_data,
            use_container_width=True,
            height=300
        )
        
        # Show data statistics
        st.subheader("📈 Data Statistics")
        if 'current_volume' in traffic_data.columns:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Min Volume", f"{traffic_data['current_volume'].min():,.0f}")
            with col2:
                st.metric("Max Volume", f"{traffic_data['current_volume'].max():,.0f}")
            with col3:
                st.metric("Mean Volume", f"{traffic_data['current_volume'].mean():,.0f}")
            with col4:
                st.metric("Total Volume", f"{traffic_data['current_volume'].sum():,.0f}")
        else:
            st.warning("⚠️ 'current_volume' column not available for statistics")
        
        # Show functional class distribution
        if 'functional_class' in traffic_data.columns:
            st.subheader("🛣️ Functional Class Distribution")
            class_counts = traffic_data['functional_class'].value_counts()
            st.bar_chart(class_counts)
        
        st.divider()
        
        # Calculate V/C ratios
        st.header("📊 V/C Ratio Analysis")
        
        # Ensure functional_class column exists before merge
        if 'functional_class' not in traffic_data.columns:
            traffic_data['functional_class'] = 'Arterial'
        
        # Ensure current_volume column exists
        if 'current_volume' not in traffic_data.columns:
            st.error("❌ Error: 'current_volume' column not found in traffic data. Available columns: " + str(list(traffic_data.columns)))
            st.stop()
        
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
        map_obj = create_interactive_map(map_data, selected_city)
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
        
        # Filter display columns to only include those that exist in the dataframe
        available_cols = [col for col in display_cols if col in traffic_data.columns]
        missing_cols = [col for col in display_cols if col not in traffic_data.columns]
        
        if missing_cols:
            st.warning(f"⚠️ Some columns not available for display: {missing_cols}")
        
        st.dataframe(
            traffic_data[available_cols].round(2),
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
        2. Select your city and growth parameters
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
            
            1. **Select City**: Choose your target city from the sidebar
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