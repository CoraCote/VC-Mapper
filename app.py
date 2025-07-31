import streamlit as st
import pandas as pd
from typing import List, Dict
import logging
from fdot_api import FDOTGISAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FDOT GIS API client
fdot_api = FDOTGISAPI()

def display_city_data_sidebar(cities: List[Dict]) -> None:
    """
    Display city data in the sidebar under controls
    
    Args:
        cities: List of city dictionaries
    """
    if not cities:
        st.sidebar.warning("No city data available")
        return
    
    # Convert to DataFrame for better display
    df_data = []
    for city in cities:
        df_data.append({
            'Name': city.get('name', ''),
            'Full Name': city.get('full_name', ''),
            'GEOID': city.get('geoid', ''),
            'Latitude': city.get('latitude', ''),
            'Longitude': city.get('longitude', ''),
            'Population': city.get('population', 0),
            'Land Area (sq m)': city.get('land_area', 0),
            'Water Area (sq m)': city.get('water_area', 0),
            'State FIPS': city.get('state_fips', ''),
            'Place FIPS': city.get('place_fips', ''),
            'LSAD': city.get('lsad', ''),
            'Class FP': city.get('class_fp', ''),
            'Func Stat': city.get('func_stat', '')
        })
    
    df = pd.DataFrame(df_data)
    
    # Display the data in sidebar
    st.sidebar.subheader("📋 City Data and Statistics")
    st.sidebar.dataframe(df, use_container_width=True)
    
    # Show summary statistics in sidebar
    st.sidebar.subheader("Summary Statistics")
    
    total_cities = len(cities)
    total_population = sum(city.get('population', 0) for city in cities)
    avg_population = total_population / len(cities) if cities else 0
    
    st.sidebar.metric("Total Cities", total_cities)
    st.sidebar.metric("Total Population", f"{total_population:,}")
    st.sidebar.metric("Average Population", f"{avg_population:,.0f}")

def display_city_data_main(cities: List[Dict]) -> None:
    """
    Display city data in the main content area (for reference)
    
    Args:
        cities: List of city dictionaries
    """
    if not cities:
        st.warning("No city data available")
        return
    
    # Convert to DataFrame for better display
    df_data = []
    for city in cities:
        df_data.append({
            'Name': city.get('name', ''),
            'Full Name': city.get('full_name', ''),
            'GEOID': city.get('geoid', ''),
            'Latitude': city.get('latitude', ''),
            'Longitude': city.get('longitude', ''),
            'Population': city.get('population', 0),
            'Land Area (sq m)': city.get('land_area', 0),
            'Water Area (sq m)': city.get('water_area', 0),
            'State FIPS': city.get('state_fips', ''),
            'Place FIPS': city.get('place_fips', ''),
            'LSAD': city.get('lsad', ''),
            'Class FP': city.get('class_fp', ''),
            'Func Stat': city.get('func_stat', '')
        })
    
    df = pd.DataFrame(df_data)
    
    # Display the data
    st.dataframe(df, use_container_width=True)
    
    # Show summary statistics
    st.subheader("Summary Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Cities", len(cities))
    
    with col2:
        total_population = sum(city.get('population', 0) for city in cities)
        st.metric("Total Population", f"{total_population:,}")
    
    with col3:
        avg_population = total_population / len(cities) if cities else 0
        st.metric("Average Population", f"{avg_population:,.0f}")

def main():
    """
    Main Streamlit application
    """
    st.set_page_config(
        page_title="FDOT City Data Explorer",
        page_icon="🗺️",
        layout="wide"
    )
    
    st.title("🗺️ FDOT City Data Explorer")
    st.markdown("Explore city boundary data from the Florida Department of Transportation GIS API")
    
    # Sidebar for controls
    st.sidebar.header("Controls")
    
    # Action selection
    action = st.sidebar.selectbox(
        "Select Action",
        ["Fetch All Cities", "Search Cities", "Get City by GEOID"]
    )
    
    # Initialize session state for storing city data
    if 'cities_data' not in st.session_state:
        st.session_state.cities_data = None
    
    if action == "Fetch All Cities":
        st.header("📋 All Cities")
        
        # Add limit option
        limit = st.sidebar.number_input(
            "Limit number of cities",
            min_value=1,
            max_value=1000,
            value=100,
            help="Limit the number of cities to fetch"
        )
        
        if st.sidebar.button("Fetch Cities", type="primary"):
            with st.spinner("Fetching cities from FDOT GIS API..."):
                cities = fdot_api.fetch_cities(limit=limit)
                
                if cities:
                    st.session_state.cities_data = cities
                    st.success(f"Successfully fetched {len(cities)} cities!")
                    # Display data in sidebar under controls
                    display_city_data_sidebar(cities)
                else:
                    st.error("Failed to fetch cities. Please check the API connection.")
        
        # # Display data in sidebar if available
        # if st.session_state.cities_data:
        #     display_city_data_sidebar(st.session_state.cities_data)
    
    elif action == "Search Cities":
        st.header("🔍 Search Cities")
        
        # Search input
        search_query = st.text_input(
            "Enter city name to search",
            placeholder="e.g., Miami, Orlando, Tampa"
        )
        
        search_limit = st.sidebar.number_input(
            "Search result limit",
            min_value=1,
            max_value=50,
            value=10
        )
        
        if search_query and st.button("Search", type="primary"):
            with st.spinner(f"Searching for cities matching '{search_query}'..."):
                cities = fdot_api.search_cities(search_query, search_limit)
                
                if cities:
                    st.session_state.cities_data = cities
                    st.success(f"Found {len(cities)} cities matching '{search_query}'!")
                    # Display data in sidebar under controls
                    display_city_data_sidebar(cities)
                else:
                    st.warning(f"No cities found matching '{search_query}'")
        
        # Display data in sidebar if available
        if st.session_state.cities_data:
            display_city_data_sidebar(st.session_state.cities_data)
    
    elif action == "Get City by GEOID":
        st.header("📍 Get City by GEOID")
        
        # GEOID input
        geoid = st.text_input(
            "Enter GEOID",
            placeholder="e.g., 1264400"
        )
        
        if geoid and st.button("Get City", type="primary"):
            with st.spinner(f"Fetching city with GEOID {geoid}..."):
                city = fdot_api.get_city_by_geoid(geoid)
                
                if city:
                    st.session_state.cities_data = [city]
                    st.success(f"Found city: {city['name']}")
                    # Display data in sidebar under controls
                    display_city_data_sidebar([city])
                else:
                    st.error(f"No city found with GEOID {geoid}")
        
        # Display data in sidebar if available
        if st.session_state.cities_data:
            display_city_data_sidebar(st.session_state.cities_data)
    
    # Main content area for additional information
    st.markdown("---")
    st.subheader("Additional Information")
    
    # Placeholder for additional features
    st.info("Right panel is available for additional features, charts, or detailed analysis.")
    
    # Quick stats if data is available
    if st.session_state.cities_data:
        st.subheader("Quick Stats:")
        cities = st.session_state.cities_data
        
        # Find largest and smallest cities
        if cities:
            largest_city = max(cities, key=lambda x: x.get('population', 0))
            smallest_city = min(cities, key=lambda x: x.get('population', 0))
            total_land_area = sum(city.get('land_area', 0) for city in cities)
            total_water_area = sum(city.get('water_area', 0) for city in cities)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Largest City", f"{largest_city['name']}", f"{largest_city.get('population', 0):,}")
                st.metric("Total Land Area", f"{total_land_area:,} sq m")
            
            with col2:
                st.metric("Smallest City", f"{smallest_city['name']}", f"{smallest_city.get('population', 0):,}")
                st.metric("Total Water Area", f"{total_water_area:,} sq m")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        **Data Source**: [FDOT GIS API](https://gis.fdot.gov/arcgis/rest/services/Admin_Boundaries/FeatureServer/7/query)
        
        This application uses the Florida Department of Transportation's GIS API to fetch city boundary data.
        """
    )

if __name__ == "__main__":
    main()