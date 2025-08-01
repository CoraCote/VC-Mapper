import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
import logging
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from fdot_api import FDOTGISAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FDOT GIS API client
fdot_api = FDOTGISAPI()

# Custom CSS for better styling
def load_css():
    st.markdown("""
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
    </style>
    """, unsafe_allow_html=True)

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

def add_city_boundary_to_map(m: folium.Map, city_data: Dict, boundary_data: Dict) -> None:
    """
    Add city boundary to the map
    
    Args:
        m: Folium map object
        city_data: City information
        boundary_data: Boundary geometry data
    """
    try:
        geometry = boundary_data.get('geometry', {})
        if not geometry:
            logger.warning(f"No geometry data for city {city_data.get('name', 'Unknown')}")
            return
        
        # Convert geometry to GeoJSON format for folium
        if geometry.get('type') == 'Polygon':
            coordinates = geometry.get('coordinates', [])
            if coordinates:
                # Convert coordinates to lat/lng format for folium
                folium_coords = []
                for ring in coordinates:
                    ring_coords = [[coord[1], coord[0]] for coord in ring]  # Swap x,y to lat,lng
                    folium_coords.append(ring_coords)
                
                # Add polygon to map
                folium.Polygon(
                    locations=folium_coords,
                    popup=f"<b>{city_data.get('name', 'Unknown')}</b><br/>City Boundary",
                    tooltip=f"City: {city_data.get('name', 'Unknown')}",
                    color='blue',
                    weight=2,
                    fillColor='lightblue',
                    fillOpacity=0.2
                ).add_to(m)
                
                logger.info(f"Added boundary for city {city_data.get('name', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"Error adding city boundary to map: {e}")

def add_streets_to_map(m: folium.Map, streets: List[Dict], show_traffic: bool = True) -> None:
    """
    Add street data to the map with traffic visualization
    
    Args:
        m: Folium map object
        streets: List of street data
        show_traffic: Whether to show traffic-based coloring
    """
    try:
        if not streets:
            return
        
        # Create feature groups for different traffic levels
        traffic_groups = {
            'very_high': folium.FeatureGroup(name='🔴 Very High Traffic'),
            'high': folium.FeatureGroup(name='🟠 High Traffic'),
            'medium': folium.FeatureGroup(name='🟡 Medium Traffic'),
            'low': folium.FeatureGroup(name='🟢 Low Traffic'),
            'very_low': folium.FeatureGroup(name='🔵 Very Low Traffic'),
            'unknown': folium.FeatureGroup(name='⚪ Unknown Traffic')
        }
        
        # Add each feature group to map
        for group in traffic_groups.values():
            group.add_to(m)
        
        for street in streets:
            geometry = street.get('geometry', {})
            if not geometry:
                continue
            
            # Get traffic level and color
            traffic_level = street.get('traffic_level', 'unknown')
            traffic_color = fdot_api.get_traffic_color(traffic_level) if show_traffic else '#0074D9'
            
            # Create popup with street information
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; width: 250px;">
                <h4 style="margin: 0 0 8px 0; color: #333;">{street.get('street_name', 'Unknown Street')}</h4>
                <p style="margin: 2px 0;"><strong>Road Number:</strong> {street.get('road_number', 'N/A')}</p>
                <p style="margin: 2px 0;"><strong>Traffic Volume:</strong> {street.get('traffic_volume', 0):,}/day</p>
                <p style="margin: 2px 0;"><strong>Traffic Level:</strong> {traffic_level.replace('_', ' ').title()}</p>
                <p style="margin: 2px 0;"><strong>Length:</strong> {street.get('length', 0):.2f} units</p>
                <p style="margin: 2px 0;"><strong>Lanes:</strong> {street.get('lane_count', 'N/A')}</p>
                <p style="margin: 2px 0;"><strong>Speed Limit:</strong> {street.get('speed_limit', 'N/A')} mph</p>
                <p style="margin: 2px 0;"><strong>County:</strong> {street.get('county', 'N/A')}</p>
            </div>
            """
            
            # Handle different geometry types
            if geometry.get('type') == 'LineString':
                coordinates = geometry.get('coordinates', [])
                if coordinates:
                    # Convert coordinates to lat/lng format
                    folium_coords = [[coord[1], coord[0]] for coord in coordinates]
                    
                    # Create polyline
                    line = folium.PolyLine(
                        locations=folium_coords,
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"{street.get('street_name', 'Unknown')} - {traffic_level.replace('_', ' ').title()} Traffic",
                        color=traffic_color,
                        weight=4 if show_traffic else 2,
                        opacity=0.8
                    )
                    
                    # Add to appropriate traffic group
                    line.add_to(traffic_groups[traffic_level])
            
            elif geometry.get('type') == 'MultiLineString':
                coordinates = geometry.get('coordinates', [])
                for line_coords in coordinates:
                    if line_coords:
                        folium_coords = [[coord[1], coord[0]] for coord in line_coords]
                        
                        line = folium.PolyLine(
                            locations=folium_coords,
                            popup=folium.Popup(popup_html, max_width=300),
                            tooltip=f"{street.get('street_name', 'Unknown')} - {traffic_level.replace('_', ' ').title()} Traffic",
                            color=traffic_color,
                            weight=4 if show_traffic else 2,
                            opacity=0.8
                        )
                        
                        line.add_to(traffic_groups[traffic_level])
        
        # Add traffic legend
        if show_traffic:
            legend_html = '''
            <div style="position: fixed; 
                        top: 10px; right: 10px; width: 200px; height: 180px; 
                        background: rgba(255,255,255,0.9); 
                        border: 2px solid #333; border-radius: 8px; z-index:9999; 
                        font-size:12px; padding: 10px; color: #333; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
            <h4 style="margin-top: 0; color: #333; text-align: center;">🚦 Traffic Legend</h4>
            <p style="margin: 4px 0;"><span style="color: #FF0000; font-size: 16px;">●</span> Very High (50k+ vehicles/day)</p>
            <p style="margin: 4px 0;"><span style="color: #FF6600; font-size: 16px;">●</span> High (25k-50k vehicles/day)</p>
            <p style="margin: 4px 0;"><span style="color: #FFFF00; font-size: 16px;">●</span> Medium (10k-25k vehicles/day)</p>
            <p style="margin: 4px 0;"><span style="color: #66FF00; font-size: 16px;">●</span> Low (5k-10k vehicles/day)</p>
            <p style="margin: 4px 0;"><span style="color: #00FF00; font-size: 16px;">●</span> Very Low (<5k vehicles/day)</p>
            <p style="margin: 4px 0;"><span style="color: #808080; font-size: 16px;">●</span> Unknown</p>
            </div>
            '''
            m.get_root().html.add_child(folium.Element(legend_html))
        
        logger.info(f"Added {len(streets)} streets to map with traffic visualization")
        
    except Exception as e:
        logger.error(f"Error adding streets to map: {e}")

def create_enhanced_map(cities: List[Dict], selected_city: Optional[Dict] = None, 
                       show_boundaries: bool = False, show_streets: bool = False, 
                       show_traffic: bool = True) -> folium.Map:
    """
    Create an enhanced interactive map with improved styling, boundaries, and streets
    
    Args:
        cities: List of city dictionaries with latitude and longitude
        selected_city: Optional selected city for detailed view
        show_boundaries: Whether to show city boundaries
        show_streets: Whether to show street data
        show_traffic: Whether to show traffic visualization
        
    Returns:
        Folium map object
    """
    # Filter cities with valid coordinates
    valid_cities = [
        city for city in cities 
        if city.get('latitude') is not None and city.get('longitude') is not None
    ]
    
    if not valid_cities:
        return None
    
    # Calculate center of map based on all cities
    avg_lat = sum(city['latitude'] for city in valid_cities) / len(valid_cities)
    avg_lon = sum(city['longitude'] for city in valid_cities) / len(valid_cities)
    
    # Create folium map with modern styling
    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=7,
        tiles=None
    )
    
    # Add multiple tile layers with proper attributions
    folium.TileLayer('OpenStreetMap', name='Street Map').add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    folium.TileLayer(
        tiles='CartoDB positron',
        name='Light Mode',
        attr='CartoDB'
    ).add_to(m)
    folium.TileLayer(
        tiles='CartoDB dark_matter', 
        name='Dark Mode',
        attr='CartoDB'
    ).add_to(m)
    
    # Add markers for each city with enhanced styling
    for city in valid_cities:
        population = city.get('population', 0)
        
        # Enhanced popup with better styling
        popup_html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; width: 280px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; padding: 15px; margin: -10px;">
            <h3 style="margin: 0 0 10px 0; text-align: center; font-size: 18px;">{city.get('name', 'Unknown')}</h3>
            <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin: 10px 0;">
                <p style="margin: 3px 0;"><strong>📍 Full Name:</strong> {city.get('full_name', 'N/A')}</p>
                <p style="margin: 3px 0;"><strong>🆔 GEOID:</strong> {city.get('geoid', 'N/A')}</p>
                <p style="margin: 3px 0;"><strong>👥 Population:</strong> {population:,}</p>
                <p style="margin: 3px 0;"><strong>🏞️ Land Area:</strong> {city.get('land_area', 0):,.0f} sq m</p>
                <p style="margin: 3px 0;"><strong>🌊 Water Area:</strong> {city.get('water_area', 0):,.0f} sq m</p>
                <p style="margin: 3px 0;"><strong>📊 Coordinates:</strong> {city.get('latitude', 0):.4f}, {city.get('longitude', 0):.4f}</p>
            </div>
        </div>
        """
        
        # Determine marker style based on population
        if population > 100000:
            color = 'red'
            icon = 'star'
            size = 12
        elif population > 50000:
            color = 'orange' 
            icon = 'info-sign'
            size = 10
        elif population > 10000:
            color = 'blue'
            icon = 'record'
            size = 8
        else:
            color = 'green'
            icon = 'circle'
            size = 6
        
        # Add enhanced marker
        folium.Marker(
            location=[city['latitude'], city['longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"<b>{city.get('name', 'Unknown')}</b><br/>Population: {population:,}",
            icon=folium.Icon(color=color, icon=icon, prefix='glyphicon')
        ).add_to(m)
        
        # Add circle marker for better visibility
        folium.CircleMarker(
            location=[city['latitude'], city['longitude']],
            radius=size,
            popup=folium.Popup(popup_html, max_width=300),
            color='white',
            weight=2,
            fillColor=color,
            fillOpacity=0.7
        ).add_to(m)
    
    # Add enhanced legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 220px; height: 140px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border: none; border-radius: 10px; z-index:9999; 
                font-size:12px; padding: 15px; color: white; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
    <h4 style="margin-top: 0; color: white; text-align: center;">🏙️ Population Legend</h4>
    <p style="margin: 5px 0;"><span style="color: #ff4444;">●</span> Metropolis (> 100,000)</p>
    <p style="margin: 5px 0;"><span style="color: #ff8800;">●</span> Large City (50,000 - 100,000)</p>
    <p style="margin: 5px 0;"><span style="color: #4488ff;">●</span> Medium City (10,000 - 50,000)</p>
    <p style="margin: 5px 0;"><span style="color: #44ff44;">●</span> Small City (< 10,000)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add city boundaries if requested
    if show_boundaries:
        for city in valid_cities:
            if selected_city and city.get('geoid') != selected_city.get('geoid'):
                continue  # Only show boundary for selected city if one is selected
                
            try:
                boundary_data = fdot_api.get_city_boundary(city.get('geoid', ''))
                if boundary_data:
                    add_city_boundary_to_map(m, city, boundary_data)
            except Exception as e:
                logger.error(f"Error adding boundary for city {city.get('name', 'Unknown')}: {e}")
    
    # Add streets if requested and a city is selected
    if show_streets and selected_city:
        try:
            streets = fdot_api.fetch_streets_in_city(selected_city.get('geoid', ''), limit=500)
            if streets:
                add_streets_to_map(m, streets, show_traffic)
                logger.info(f"Added {len(streets)} streets to map for {selected_city.get('name', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error loading streets for city {selected_city.get('name', 'Unknown')}: {e}")
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

def display_cities_on_map(cities: List[Dict]) -> None:
    """
    Display cities on an enhanced interactive map with boundary and street options
    
    Args:
        cities: List of city dictionaries with latitude and longitude
    """
    if not cities:
        st.error("🚫 No city data available to display on map")
        return
    
    # Filter cities with valid coordinates
    valid_cities = [
        city for city in cities 
        if city.get('latitude') is not None and city.get('longitude') is not None
    ]
    
    if not valid_cities:
        st.error("🚫 No cities with valid coordinates found")
        return
    
    # Initialize session state for selected city
    if 'selected_city' not in st.session_state:
        st.session_state.selected_city = None
    
    # Map configuration options
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        show_boundaries = st.checkbox("🏢 Show City Boundaries", value=False, help="Display city boundary polygons")
    with col2:
        show_streets = st.checkbox("🛣️ Show Streets", value=False, help="Display street network for selected city")
    with col3:
        show_traffic = st.checkbox("🚦 Show Traffic Data", value=True, help="Color-code streets by traffic volume")
    with col4:
        # City selector
        city_names = [f"{city.get('name', 'Unknown')} ({city.get('geoid', 'N/A')})" for city in valid_cities]
        selected_index = st.selectbox(
            "🎯 Select City for Details",
            range(len(city_names)),
            format_func=lambda x: city_names[x],
            index=0,
            help="Choose a city to view boundaries and streets"
        )
        st.session_state.selected_city = valid_cities[selected_index] if selected_index is not None else None
    
    # Create map with options
    if show_streets and st.session_state.selected_city:
        with st.spinner(f"Loading streets for {st.session_state.selected_city.get('name', 'selected city')}..."):
            m = create_enhanced_map(
                valid_cities, 
                selected_city=st.session_state.selected_city,
                show_boundaries=show_boundaries,
                show_streets=show_streets,
                show_traffic=show_traffic
            )
    else:
        m = create_enhanced_map(
            valid_cities, 
            selected_city=st.session_state.selected_city,
            show_boundaries=show_boundaries,
            show_streets=show_streets,
            show_traffic=show_traffic
        )
    
    if m is None:
        st.error("🚫 Unable to create map")
        return
    
    # Display map in a container with custom styling
    with st.container():
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        
        # Map header with statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏙️ Cities Mapped", len(valid_cities))
        with col2:
            total_pop = sum(city.get('population', 0) for city in valid_cities)
            st.metric("👥 Total Population", f"{total_pop:,}")
        with col3:
            avg_pop = total_pop / len(valid_cities) if valid_cities else 0
            st.metric("📊 Average Population", f"{avg_pop:,.0f}")
        with col4:
            total_area = sum(city.get('land_area', 0) for city in valid_cities)
            st.metric("🏞️ Total Land Area", f"{total_area/1000000:.1f} km²")
        
        st.markdown("---")
        
        # Display the map
        map_data = st_folium(m, width=None, height=600, returned_objects=["last_clicked"])
        
        # Show selected city details
        if st.session_state.selected_city:
            selected = st.session_state.selected_city
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"🎯 **Selected City:** {selected.get('name', 'Unknown')}")
                st.metric("👥 Population", f"{selected.get('population', 0):,}")
            with col2:
                st.metric("🏞️ Land Area", f"{selected.get('land_area', 0)/1000000:.2f} km²")
                st.metric("📍 Coordinates", f"{selected.get('latitude', 0):.4f}, {selected.get('longitude', 0):.4f}")
            with col3:
                st.metric("🆔 GEOID", selected.get('geoid', 'N/A'))
                st.metric("🌊 Water Area", f"{selected.get('water_area', 0)/1000000:.2f} km²")
        
        # Show clicked city details for additional interaction
        if map_data.get('last_clicked'):
            try:
                clicked_lat = map_data['last_clicked']['lat']
                clicked_lng = map_data['last_clicked']['lng']
                
                # Find the closest city to the clicked point
                closest_city = min(valid_cities, 
                                 key=lambda city: abs(city.get('latitude', 0) - clicked_lat) + abs(city.get('longitude', 0) - clicked_lng))
                
                st.success(f"📍 Clicked: **{closest_city.get('name', 'Unknown')}** - Population: {closest_city.get('population', 0):,}")
            except Exception as e:
                st.info("📍 Click on a city marker to see details")
        
        st.markdown('</div>', unsafe_allow_html=True)

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

def create_charts(cities: List[Dict]) -> None:
    """
    Create interactive charts for city data analysis
    
    Args:
        cities: List of city dictionaries
    """
    if not cities:
        st.info("📊 No data available for charts")
        return
    
    try:
        # Prepare data for charts
        df = pd.DataFrame(cities)
        df['population'] = pd.to_numeric(df['population'], errors='coerce').fillna(0)
        df['land_area_km2'] = pd.to_numeric(df['land_area'], errors='coerce').fillna(0) / 1000000
        df['water_area_km2'] = pd.to_numeric(df['water_area'], errors='coerce').fillna(0) / 1000000
        
        # Filter out cities with no name for better display
        df = df[df['name'].notna() & (df['name'] != '')]
        
        if len(df) == 0:
            st.warning("⚠️ No valid data available for charts")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Population distribution chart
            if df['population'].sum() > 0:
                fig_pop = px.histogram(
                    df, 
                    x='population', 
                    nbins=min(20, len(df)),
                    title="Population Distribution",
                    labels={'population': 'Population', 'count': 'Number of Cities'},
                    color_discrete_sequence=['#2a5298']
                )
                fig_pop.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#2a5298'
                )
                st.plotly_chart(fig_pop, use_container_width=True)
            else:
                st.info("📊 No population data available for histogram")
        
        with col2:
            # Top cities by population
            if len(df) > 0 and df['population'].sum() > 0:
                top_cities = df.nlargest(min(10, len(df)), 'population')
                if len(top_cities) > 0:
                    fig_top = px.bar(
                        top_cities, 
                        x='population', 
                        y='name',
                        orientation='h',
                        title="Top Cities by Population",
                        labels={'population': 'Population', 'name': 'City'},
                        color='population',
                        color_continuous_scale='Blues'
                    )
                    fig_top.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#2a5298',
                        yaxis={'categoryorder': 'total ascending'}
                    )
                    st.plotly_chart(fig_top, use_container_width=True)
                else:
                    st.info("📊 No cities available for ranking")
            else:
                st.info("📊 No population data available for ranking")
    
    except Exception as e:
        st.error(f"❌ Error creating charts: {str(e)}")
        st.info("📊 Charts will be available when valid data is loaded")

def create_smart_sidebar():
    """
    Create an enhanced sidebar with better organization
    """
    with st.sidebar:
        st.markdown('<div class="search-container">', unsafe_allow_html=True)
        
        st.markdown("### 🎯 Data Source")
        action = st.selectbox(
            "Choose data source",
            ["🌍 Fetch All Cities", "🔍 Search Cities", "📍 Get by GEOID"],
            help="Select how you want to retrieve city data"
        )
        
        st.markdown("### ⚙️ Settings")
        
        # Different settings based on action
        if action == "🌍 Fetch All Cities":
            limit = st.slider(
                "Number of cities",
                min_value=5,
                max_value=500,
                value=50,
                step=5,
                help="Limit the number of cities to fetch"
            )
            fetch_button = st.button("🚀 Fetch Cities", type="primary", use_container_width=True)
            return action, {"limit": limit, "button": fetch_button}
            
        elif action == "🔍 Search Cities":
            search_query = st.text_input(
                "City name",
                placeholder="e.g., Miami, Orlando, Tampa",
                help="Enter part of a city name to search"
            )
            search_limit = st.slider(
                "Max results",
                min_value=1,
                max_value=50,
                value=15,
                help="Maximum number of search results"
            )
            search_button = st.button("🔍 Search", type="primary", use_container_width=True)
            return action, {"query": search_query, "limit": search_limit, "button": search_button}
            
        elif action == "📍 Get by GEOID":
            geoid = st.text_input(
                "GEOID",
                placeholder="e.g., 1264400",
                help="Enter the Geographic Identifier"
            )
            geoid_button = st.button("📍 Get City", type="primary", use_container_width=True)
            return action, {"geoid": geoid, "button": geoid_button}
        
        st.markdown('</div>', unsafe_allow_html=True)

def handle_data_fetch(action: str, params: dict):
    """
    Handle data fetching based on action and parameters
    
    Args:
        action: The selected action
        params: Parameters for the action
    """
    if action == "🌍 Fetch All Cities" and params["button"]:
        with st.spinner("🔄 Fetching cities from FDOT GIS API..."):
            cities = fdot_api.fetch_cities(limit=params["limit"])
            
            if cities:
                st.session_state.cities_data = cities
                st.success(f"✅ Successfully fetched {len(cities)} cities!")
            else:
                st.error("❌ Failed to fetch cities. Please check the API connection.")
    
    elif action == "🔍 Search Cities" and params["button"] and params["query"]:
        with st.spinner(f"🔍 Searching for cities matching '{params['query']}'..."):
            cities = fdot_api.search_cities(params["query"], params["limit"])
            
            if cities:
                st.session_state.cities_data = cities
                st.success(f"✅ Found {len(cities)} cities matching '{params['query']}'!")
            else:
                st.warning(f"⚠️ No cities found matching '{params['query']}'")
    
    elif action == "📍 Get by GEOID" and params["button"] and params["geoid"]:
        with st.spinner(f"📍 Fetching city with GEOID {params['geoid']}..."):
            city = fdot_api.get_city_by_geoid(params["geoid"])
            
            if city:
                st.session_state.cities_data = [city]
                st.success(f"✅ Found city: {city['name']}")
            else:
                st.error(f"❌ No city found with GEOID {params['geoid']}")

def main():
    """
    Main Streamlit application with enhanced UI
    """
    st.set_page_config(
        page_title="FDOT City Data Explorer",
        page_icon="🗺️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    load_css()
    
    # Modern header
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🗺️ FDOT City Data Explorer</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            Explore Florida city data with interactive maps and analytics
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'cities_data' not in st.session_state:
        st.session_state.cities_data = None
    
    # Smart sidebar
    action, params = create_smart_sidebar()
    
    # Handle data fetching
    handle_data_fetch(action, params)
    
    # Main content area with tabs
    if st.session_state.cities_data:
        cities = st.session_state.cities_data
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "🗺️ Interactive Map", 
            "📊 Data Table", 
            "📈 Analytics", 
            "📋 Summary"
        ])
        
        with tab1:
            st.markdown("### 🗺️ Interactive City Map")
            display_cities_on_map(cities)
        
        with tab2:
            st.markdown("### 📊 City Data Table")
            
            # Add filters
            col1, col2, col3 = st.columns(3)
            with col1:
                max_pop = max(city.get('population', 0) for city in cities) if cities else 100000
                pop_filter = st.slider(
                    "Minimum Population", 
                    0, 
                    max_pop, 
                    0
                )
            with col2:
                # Get unique state FIPS for filter
                state_fips = list(set(city.get('state_fips', '') for city in cities if city.get('state_fips', '')))
                state_filter = st.selectbox("State FIPS", ["All"] + sorted(state_fips))
            with col3:
                sort_by = st.selectbox(
                    "Sort by", 
                    ["Name", "Population", "Land Area", "Water Area"]
                )
            
            # Filter and sort data
            filtered_cities = [
                city for city in cities 
                if city.get('population', 0) >= pop_filter and 
                (state_filter == "All" or city.get('state_fips', '') == state_filter)
            ]
            
            if sort_by == "Population":
                filtered_cities.sort(key=lambda x: x.get('population', 0), reverse=True)
            elif sort_by == "Land Area":
                filtered_cities.sort(key=lambda x: x.get('land_area', 0), reverse=True)
            elif sort_by == "Water Area":
                filtered_cities.sort(key=lambda x: x.get('water_area', 0), reverse=True)
            else:
                filtered_cities.sort(key=lambda x: x.get('name', ''))
            
            display_city_data_main(filtered_cities)
        
        with tab3:
            st.markdown("### 📈 City Analytics")
            create_charts(cities)
        
        with tab4:
            st.markdown("### 📋 Summary Statistics")
            
            if cities:
                # Enhanced summary statistics
                largest_city = max(cities, key=lambda x: x.get('population', 0))
                smallest_city = min(cities, key=lambda x: x.get('population', 0))
                total_pop = sum(city.get('population', 0) for city in cities)
                total_land = sum(city.get('land_area', 0) for city in cities)
                total_water = sum(city.get('water_area', 0) for city in cities)
                
                # Statistics grid
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric("🏙️ Total Cities", len(cities))
                    st.metric("👥 Total Population", f"{total_pop:,}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    avg_pop = total_pop/len(cities) if len(cities) > 0 else 0
                    populations = sorted([c.get('population', 0) for c in cities])
                    median_pop = populations[len(cities)//2] if len(populations) > 0 else 0
                    st.metric("📊 Average Population", f"{avg_pop:,.0f}")
                    st.metric("📍 Median Population", f"{median_pop:,}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric("🏞️ Total Land Area", f"{total_land/1000000:.1f} km²")
                    st.metric("🌊 Total Water Area", f"{total_water/1000000:.1f} km²")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col4:
                    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                    st.metric("🏆 Largest City", largest_city['name'], f"{largest_city.get('population', 0):,}")
                    st.metric("🏘️ Smallest City", smallest_city['name'], f"{smallest_city.get('population', 0):,}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Top cities showcase
                st.markdown("---")
                st.markdown("### 🏆 Top Cities")
                
                top_5 = sorted(cities, key=lambda x: x.get('population', 0), reverse=True)[:5]
                for i, city in enumerate(top_5, 1):
                    st.markdown(f"""
                    <div class="city-card">
                        <h4>#{i} {city.get('name', 'Unknown')}</h4>
                        <p><strong>Population:</strong> {city.get('population', 0):,} | 
                           <strong>GEOID:</strong> {city.get('geoid', 'N/A')} | 
                           <strong>Land Area:</strong> {city.get('land_area', 0)/1000000:.2f} km²</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    else:
        # Welcome screen with better styling
        st.markdown("### 🌟 Welcome to FDOT City Data Explorer")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="search-container">
                <h4>🚀 Getting Started</h4>
                <p>Explore Florida city data with our powerful tools:</p>
                <ul>
                    <li>🗺️ <strong>Interactive Maps</strong> - Visualize cities on modern map interfaces</li>
                    <li>📊 <strong>Data Tables</strong> - Browse detailed city information</li>
                    <li>📈 <strong>Analytics</strong> - Discover insights with charts and statistics</li>
                    <li>🔍 <strong>Smart Search</strong> - Find cities by name or GEOID</li>
                </ul>
                <p><strong>👈 Start by selecting a data source from the sidebar!</strong></p>
            </div>
            """, unsafe_allow_html=True)
    
    # Enhanced footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p><strong>Data Source:</strong> 
        <a href="https://gis.fdot.gov/arcgis/rest/services/Admin_Boundaries/FeatureServer/7/query" 
           target="_blank" style="color: #2a5298;">Florida Department of Transportation GIS API</a></p>
        <p>Built with ❤️ using Streamlit | Enhanced with Folium and Plotly</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()