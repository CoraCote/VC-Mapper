import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
import logging
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from fdot_api import FDOTGISAPI
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FDOT GIS API client
fdot_api = FDOTGISAPI()

# Florida state boundary GeoJSON (simplified coordinates)
FLORIDA_BOUNDARY = {
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "properties": {"name": "Florida"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-87.634896, 30.997536],  # Northwest corner
                [-87.427917, 30.997536], 
                [-86.913892, 30.997536],
                [-85.497137, 30.997536],
                [-84.319447, 30.676609],
                [-82.879938, 30.564875],
                [-82.190083, 30.564875],
                [-81.24069, 30.564875],
                [-80.915156, 31.068903],
                [-80.565487, 31.068903],
                [-80.381653, 30.997536],
                [-80.08183, 30.997536],
                [-80.031983, 30.564875],
                [-80.031983, 29.229735],
                [-80.031983, 28.128005],
                [-80.031983, 26.994637],
                [-80.031983, 25.729595],
                [-80.218695, 25.204941],
                [-80.748177, 25.204941],
                [-81.092673, 24.411089],
                [-81.755371, 24.411089],
                [-82.650513, 24.568745],
                [-83.351287, 25.204941],
                [-84.02832, 25.573047],
                [-84.319447, 25.573047],
                [-85.064697, 25.890106],
                [-85.872803, 26.994637],
                [-86.462402, 28.128005],
                [-87.017822, 28.902305],
                [-87.459717, 29.675867],
                [-87.634896, 30.997536]   # Closing coordinate
            ]]
        }
    }]
}

def get_overpass_streets(bbox: List[float], city_name: str = "") -> List[Dict]:
    """
    Get street data from OpenStreetMap Overpass API within a bounding box
    
    Args:
        bbox: [south, west, north, east] bounding box coordinates
        city_name: Name of the city for filtering (optional)
    
    Returns:
        List of street dictionaries with geometry and properties
    """
    try:
        overpass_url = "http://overpass-api.de/api/interpreter"
        
        # Build Overpass query for streets (highways)
        query = f"""
        [out:json][timeout:25];
        (
          way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|service|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link)$"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        );
        out geom;
        """
        
        response = requests.get(overpass_url, params={'data': query}, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        streets = []
        
        for element in data.get('elements', []):
            if element.get('type') == 'way' and 'geometry' in element:
                # Convert OSM geometry to standard format
                coords = []
                for node in element['geometry']:
                    coords.append([node['lon'], node['lat']])
                
                street_data = {
                    'street_id': element.get('id'),
                    'street_name': element.get('tags', {}).get('name', 'Unnamed Street'),
                    'highway_type': element.get('tags', {}).get('highway', 'unknown'),
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': coords
                    },
                    'lanes': element.get('tags', {}).get('lanes'),
                    'maxspeed': element.get('tags', {}).get('maxspeed'),
                    'surface': element.get('tags', {}).get('surface'),
                    'raw_tags': element.get('tags', {})
                }
                streets.append(street_data)
        
        logger.info(f"Retrieved {len(streets)} streets from OpenStreetMap for {city_name or 'specified area'}")
        return streets
        
    except Exception as e:
        logger.error(f"Error fetching streets from OpenStreetMap: {e}")
        return []

def get_alternative_street_data(lat: float, lon: float, city_name: str = "") -> List[Dict]:
    """
    Try multiple methods to get street data for a city
    
    Args:
        lat: Latitude of the city center
        lon: Longitude of the city center  
        city_name: Name of the city
    
    Returns:
        List of street dictionaries
    """
    streets = []
    
    # Method 1: OpenStreetMap Overpass API with larger bounding box
    try:
        bbox_size = 0.02  # Start with smaller area
        bbox = [lat - bbox_size, lon - bbox_size, lat + bbox_size, lon + bbox_size]
        streets = get_overpass_streets(bbox, city_name)
        
        if streets:
            logger.info(f"Retrieved {len(streets)} streets using OpenStreetMap Overpass API")
            return streets
    except Exception as e:
        logger.error(f"OpenStreetMap method failed: {e}")
    
    # Method 2: Try larger bounding box
    try:
        bbox_size = 0.05  # Larger area
        bbox = [lat - bbox_size, lon - bbox_size, lat + bbox_size, lon + bbox_size]
        streets = get_overpass_streets(bbox, city_name)
        
        if streets:
            logger.info(f"Retrieved {len(streets)} streets using larger OpenStreetMap area")
            return streets
    except Exception as e:
        logger.error(f"Larger OpenStreetMap area method failed: {e}")
    
    # Method 3: Try alternative Overpass servers
    try:
        overpass_urls = [
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass-api.de/api/interpreter",
            "https://z.overpass-api.de/api/interpreter"
        ]
        
        bbox_size = 0.03
        bbox = [lat - bbox_size, lon - bbox_size, lat + bbox_size, lon + bbox_size]
        
        for overpass_url in overpass_urls:
            try:
                query = f"""
                [out:json][timeout:30];
                (
                  way["highway"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
                );
                out geom;
                """
                
                response = requests.get(overpass_url, params={'data': query}, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                for element in data.get('elements', []):
                    if element.get('type') == 'way' and 'geometry' in element:
                        coords = []
                        for node in element['geometry']:
                            coords.append([node['lon'], node['lat']])
                        
                        street_data = {
                            'street_id': element.get('id'),
                            'street_name': element.get('tags', {}).get('name', 'Unnamed Street'),
                            'highway_type': element.get('tags', {}).get('highway', 'road'),
                            'geometry': {
                                'type': 'LineString',
                                'coordinates': coords
                            },
                            'lanes': element.get('tags', {}).get('lanes'),
                            'maxspeed': element.get('tags', {}).get('maxspeed'),
                            'surface': element.get('tags', {}).get('surface'),
                            'raw_tags': element.get('tags', {})
                        }
                        streets.append(street_data)
                
                if streets:
                    logger.info(f"Retrieved {len(streets)} streets using alternative Overpass server: {overpass_url}")
                    return streets
                    
            except Exception as server_error:
                logger.warning(f"Failed with server {overpass_url}: {server_error}")
                continue
                
    except Exception as e:
        logger.error(f"Alternative servers method failed: {e}")
    
    logger.warning(f"Could not retrieve street data for {city_name} using any method")
    return []

def add_florida_boundary_to_map(m: folium.Map) -> None:
    """
    Add Florida state boundary to the map
    
    Args:
        m: Folium map object
    """
    try:
        folium.GeoJson(
            FLORIDA_BOUNDARY,
            style_function=lambda feature: {
                'fillColor': 'transparent',
                'color': '#1f77b4',
                'weight': 3,
                'fillOpacity': 0.1,
                'opacity': 0.8
            },
            popup=folium.Popup("State of Florida", max_width=200),
            tooltip="Florida State Boundary"
        ).add_to(m)
        
        logger.info("Added Florida state boundary to map")
        
    except Exception as e:
        logger.error(f"Error adding Florida boundary to map: {e}")

def display_florida_only_map() -> None:
    """
    Display a map showing only the Florida state boundary
    """
    # Center on Florida
    center_lat, center_lon = 27.8333, -81.717
    zoom_level = 7
    
    # Create folium map with modern styling
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_level,
        tiles=None
    )
    
    # Add multiple tile layers
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
    
    # Add Florida state boundary
    add_florida_boundary_to_map(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Display the map
    with st.container():
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        st.info("📍 Press the 'FETCH CITY' button from the sidebar to load city data and explore specific locations.")
        st_folium(m, width=None, height=600)
        st.markdown('</div>', unsafe_allow_html=True)

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

def add_city_boundary_to_map(m: folium.Map, city_data: Dict, boundary_data: Dict, is_selected: bool = False) -> None:
    """
    Add city boundary to the map with enhanced styling for selected city
    
    Args:
        m: Folium map object
        city_data: City information
        boundary_data: Boundary geometry data
        is_selected: Whether this is the selected city (for enhanced styling)
    """
    try:
        geometry = boundary_data.get('geometry', {})
        if not geometry:
            logger.warning(f"No geometry data for city {city_data.get('name', 'Unknown')}")
            return
        
        # Different styling for selected vs regular cities
        if is_selected:
            color = '#FF6B35'  # Orange for selected city
            weight = 4
            fillColor = '#FF6B35'
            fillOpacity = 0.3
            dash_array = None
        else:
            color = '#4A90E2'  # Blue for other cities
            weight = 2
            fillColor = '#4A90E2'
            fillOpacity = 0.1
            dash_array = '10,10'
        
        # Convert geometry to GeoJSON format for folium
        if geometry.get('type') == 'Polygon':
            coordinates = geometry.get('coordinates', [])
            if coordinates:
                # Convert coordinates to lat/lng format for folium
                folium_coords = []
                for ring in coordinates:
                    ring_coords = [[coord[1], coord[0]] for coord in ring]  # Swap x,y to lat,lng
                    folium_coords.append(ring_coords)
                
                # Enhanced popup for selected city
                popup_content = f"""
                <div style="font-family: Arial, sans-serif; width: 200px;">
                    <h4 style="margin: 0 0 8px 0; color: {'#FF6B35' if is_selected else '#4A90E2'};">
                        {'🎯 ' if is_selected else '🏢 '}{city_data.get('name', 'Unknown')}
                    </h4>
                    <p style="margin: 2px 0;"><strong>Status:</strong> {'Selected City' if is_selected else 'City Boundary'}</p>
                    <p style="margin: 2px 0;"><strong>Population:</strong> {city_data.get('population', 0):,}</p>
                    <p style="margin: 2px 0;"><strong>GEOID:</strong> {city_data.get('geoid', 'N/A')}</p>
                </div>
                """
                
                # Add polygon to map
                polygon = folium.Polygon(
                    locations=folium_coords,
                    popup=folium.Popup(popup_content, max_width=250),
                    tooltip=f"{'🎯 Selected: ' if is_selected else '🏢 '}{city_data.get('name', 'Unknown')}",
                    color=color,
                    weight=weight,
                    fillColor=fillColor,
                    fillOpacity=fillOpacity,
                    dashArray=dash_array
                )
                polygon.add_to(m)
                
                logger.info(f"Added {'highlighted' if is_selected else 'regular'} boundary for city {city_data.get('name', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"Error adding city boundary to map: {e}")

def add_streets_to_map(m: folium.Map, streets: List[Dict], show_traffic: bool = True, city_selected: bool = False) -> None:
    """
    Add street data to the map with traffic visualization or city highlighting
    
    Args:
        m: Folium map object
        streets: List of street data
        show_traffic: Whether to show traffic-based coloring
        city_selected: Whether this is for a selected city (use blue highlighting)
    """
    try:
        if not streets:
            return
        
        if city_selected:
            # For selected city, highlight streets in blue
            street_group = folium.FeatureGroup(name='🔵 City Streets').add_to(m)
            
            for street in streets:
                geometry = street.get('geometry', {})
                if not geometry:
                    continue
                
                # Create popup with street information
                popup_html = f"""
                <div style="font-family: Arial, sans-serif; width: 250px;">
                    <h4 style="margin: 0 0 8px 0; color: #333;">{street.get('street_name', 'Unknown Street')}</h4>
                    <p style="margin: 2px 0;"><strong>Type:</strong> {street.get('highway_type', 'N/A').replace('_', ' ').title()}</p>
                    <p style="margin: 2px 0;"><strong>Lanes:</strong> {street.get('lanes', 'N/A')}</p>
                    <p style="margin: 2px 0;"><strong>Max Speed:</strong> {street.get('maxspeed', 'N/A')}</p>
                    <p style="margin: 2px 0;"><strong>Surface:</strong> {street.get('surface', 'N/A')}</p>
                </div>
                """
                
                # Handle different geometry types
                if geometry.get('type') == 'LineString':
                    coordinates = geometry.get('coordinates', [])
                    if coordinates:
                        # Convert coordinates to lat/lng format
                        folium_coords = [[coord[1], coord[0]] for coord in coordinates]
                        
                        # Create blue polyline for city streets
                        line = folium.PolyLine(
                            locations=folium_coords,
                            popup=folium.Popup(popup_html, max_width=300),
                            tooltip=f"{street.get('street_name', 'Unknown Street')} - {street.get('highway_type', 'street').replace('_', ' ').title()}",
                            color='#0074D9',  # Blue color for city streets
                            weight=3,
                            opacity=0.8
                        )
                        
                        line.add_to(street_group)
            
            logger.info(f"Added {len(streets)} city streets highlighted in blue")
        
        else:
            # Original traffic-based coloring
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
                       show_traffic: bool = True, show_only_selected: bool = False) -> folium.Map:
    """
    Create an enhanced interactive map with improved styling, boundaries, and streets
    
    Args:
        cities: List of city dictionaries with latitude and longitude
        selected_city: Optional selected city for detailed view
        show_boundaries: Whether to show city boundaries
        show_streets: Whether to show street data
        show_traffic: Whether to show traffic visualization
        show_only_selected: Whether to show only selected city (clear everything else)
        
    Returns:
        Folium map object
    """
    # If no cities, this shouldn't be called - use display_florida_only_map instead
    if not cities:
        return None
    
    # Filter cities with valid coordinates
    valid_cities = [
        city for city in cities 
        if city.get('latitude') is not None and city.get('longitude') is not None
    ]
    
    if not valid_cities:
        return None
    
    # If showing only selected city, use only that city
    if show_only_selected and selected_city:
        cities_to_show = [selected_city] if selected_city in valid_cities else []
        if not cities_to_show:
            return None
    else:
        cities_to_show = valid_cities
    
    # Calculate center and zoom based on selected city or all cities
    if selected_city and selected_city.get('latitude') and selected_city.get('longitude'):
        center_lat = selected_city['latitude']
        center_lon = selected_city['longitude']
        zoom_level = 12 if show_only_selected else 10  # Closer zoom for selected city only
    else:
        center_lat = sum(city['latitude'] for city in cities_to_show) / len(cities_to_show)
        center_lon = sum(city['longitude'] for city in cities_to_show) / len(cities_to_show)
        zoom_level = 7
    
    # Create folium map with modern styling
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_level,
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
    
    # Add markers for cities (all cities or only selected city based on mode)
    for city in cities_to_show:
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
        for city in cities_to_show:
            # Show all boundaries or only selected city based on selection
            is_selected_city = selected_city and city.get('geoid') == selected_city.get('geoid')
            
            # If a city is selected, show all boundaries but highlight the selected one
            try:
                boundary_data = fdot_api.get_city_boundary(city.get('geoid', ''))
                if boundary_data:
                    add_city_boundary_to_map(m, city, boundary_data, is_selected=is_selected_city)
            except Exception as e:
                logger.error(f"Error adding boundary for city {city.get('name', 'Unknown')}: {e}")
    
    # Add streets if requested and a city is selected
    if show_streets and selected_city:
        try:
            # Use the robust alternative street data method
            lat, lon = selected_city.get('latitude', 0), selected_city.get('longitude', 0)
            city_name = selected_city.get('name', 'Unknown')
            
            streets = get_alternative_street_data(lat, lon, city_name)
            
            if streets:
                # Use blue highlighting for selected city streets
                add_streets_to_map(m, streets, show_traffic=False, city_selected=True)
                logger.info(f"Added {len(streets)} streets highlighted in blue for {city_name}")
            else:
                logger.warning(f"No street data could be retrieved for {city_name}")
                
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
    col1, col2 = st.columns(2)
    with col1:
        # City selector
        city_options = ["View All Cities"] + [f"{city.get('name', 'Unknown')} ({city.get('geoid', 'N/A')})" for city in valid_cities]
        selected_option = st.selectbox(
            "🎯 Select View",
            city_options,
            index=0,
            help="Choose 'View All Cities' or select a specific city for detailed view"
        )
        
        if selected_option == "View All Cities":
            st.session_state.selected_city = None
            show_only_selected = False
        else:
            # Find the selected city
            selected_index = city_options.index(selected_option) - 1  # -1 because of "View All Cities" option
            st.session_state.selected_city = valid_cities[selected_index]
            show_only_selected = True
    
    with col2:
        if st.session_state.selected_city:
            show_streets = st.checkbox("🛣️ Show Streets", value=True, help="Display street network for selected city")
        else:
            show_streets = False
            st.info("📍 Select a specific city to view streets")
    
    # Determine what to show
    if st.session_state.selected_city:
        # Show only selected city with red boundary and blue streets
        show_boundaries = True
        show_traffic = False  # We use blue for city selection mode
        
        with st.spinner(f"Loading data for {st.session_state.selected_city.get('name', 'selected city')}..."):
            m = create_enhanced_map(
                valid_cities, 
                selected_city=st.session_state.selected_city,
                show_boundaries=show_boundaries,
                show_streets=show_streets,
                show_traffic=show_traffic,
                show_only_selected=show_only_selected
            )
    else:
        # Show all cities with boundaries
        show_boundaries = True
        show_traffic = True
        
        m = create_enhanced_map(
            valid_cities, 
            selected_city=None,
            show_boundaries=show_boundaries,
            show_streets=False,
            show_traffic=show_traffic,
            show_only_selected=False
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

def display_street_data_table(streets: List[Dict], city_name: str) -> None:
    """
    Display street data in a formatted table
    
    Args:
        streets: List of street data dictionaries
        city_name: Name of the city for the table title
    """
    if not streets:
        st.info("📍 No street data available for the selected city")
        return
    
    st.subheader(f"🛣️ Street Data for {city_name}")
    
    # Prepare data for table
    table_data = []
    for street in streets:
        table_data.append({
            'Street Name': street.get('street_name', 'Unknown'),
            'Road Number': street.get('road_number', 'N/A'),
            'Traffic Volume': f"{street.get('traffic_volume', 0):,}",
            'Traffic Level': street.get('traffic_level', 'unknown').replace('_', ' ').title(),
            'Length': f"{street.get('length', 0):.2f}",
            'Lanes': street.get('lane_count', 'N/A'),
            'Speed Limit': f"{street.get('speed_limit', 'N/A')} mph" if street.get('speed_limit') else 'N/A',
            'County': street.get('county', 'N/A'),
            'Surface Type': street.get('surface_type', 'N/A'),
            'Functional Class': street.get('functional_class', 'N/A')
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(table_data)
    
    # Add search and filter controls
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("🔍 Search streets", placeholder="Enter street name...")
    with col2:
        traffic_filter = st.selectbox(
            "🚦 Filter by traffic level",
            ["All"] + sorted(list(set(street.get('traffic_level', 'unknown').replace('_', ' ').title() for street in streets)))
        )
    with col3:
        sort_by = st.selectbox(
            "📊 Sort by",
            ["Street Name", "Traffic Volume", "Length", "Speed Limit"]
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    if search_term:
        filtered_df = filtered_df[filtered_df['Street Name'].str.contains(search_term, case=False, na=False)]
    
    if traffic_filter != "All":
        filtered_df = filtered_df[filtered_df['Traffic Level'] == traffic_filter]
    
    # Apply sorting
    if sort_by == "Traffic Volume":
        filtered_df['Sort_Value'] = filtered_df['Traffic Volume'].str.replace(',', '').astype(int)
        filtered_df = filtered_df.sort_values('Sort_Value', ascending=False)
        filtered_df = filtered_df.drop('Sort_Value', axis=1)
    elif sort_by == "Length":
        filtered_df['Sort_Value'] = pd.to_numeric(filtered_df['Length'], errors='coerce')
        filtered_df = filtered_df.sort_values('Sort_Value', ascending=False)
        filtered_df = filtered_df.drop('Sort_Value', axis=1)
    elif sort_by == "Speed Limit":
        filtered_df['Sort_Value'] = filtered_df['Speed Limit'].str.extract('(\d+)').astype(float)
        filtered_df = filtered_df.sort_values('Sort_Value', ascending=False)
        filtered_df = filtered_df.drop('Sort_Value', axis=1)
    else:
        filtered_df = filtered_df.sort_values('Street Name')
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🛣️ Total Streets", len(filtered_df))
    with col2:
        total_traffic = sum(int(row['Traffic Volume'].replace(',', '')) for _, row in filtered_df.iterrows() if row['Traffic Volume'] != '0')
        st.metric("🚗 Total Daily Traffic", f"{total_traffic:,}")
    with col3:
        avg_traffic = total_traffic // len(filtered_df) if len(filtered_df) > 0 else 0
        st.metric("📊 Avg Traffic/Street", f"{avg_traffic:,}")
    with col4:
        total_length = sum(float(row['Length']) for _, row in filtered_df.iterrows() if row['Length'] != '0.00')
        st.metric("📏 Total Length", f"{total_length:.1f} units")
    
    # Display the table
    st.dataframe(
        filtered_df, 
        use_container_width=True,
        height=400,
        column_config={
            "Traffic Volume": st.column_config.NumberColumn(
                "Traffic Volume (daily)",
                help="Daily traffic volume",
                format="%d"
            ),
            "Traffic Level": st.column_config.TextColumn(
                "Traffic Level",
                help="Classification based on daily traffic volume"
            )
        }
    )
    
    # Traffic distribution chart
    if len(filtered_df) > 0:
        st.subheader("📈 Traffic Level Distribution")
        traffic_counts = filtered_df['Traffic Level'].value_counts()
        
        col1, col2 = st.columns(2)
        with col1:
            # Pie chart
            fig_pie = px.pie(
                values=traffic_counts.values,
                names=traffic_counts.index,
                title="Streets by Traffic Level",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Bar chart
            fig_bar = px.bar(
                x=traffic_counts.index,
                y=traffic_counts.values,
                title="Street Count by Traffic Level",
                labels={'x': 'Traffic Level', 'y': 'Number of Streets'},
                color=traffic_counts.values,
                color_continuous_scale='Viridis'
            )
            fig_bar.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)

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
            fetch_button = st.button("🚀 FETCH CITY", type="primary", use_container_width=True)
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
    if 'selected_city' not in st.session_state:
        st.session_state.selected_city = None
    
    # Smart sidebar
    action, params = create_smart_sidebar()
    
    # Handle data fetching
    handle_data_fetch(action, params)
    
    # Always show the Interactive Map tab first
    st.markdown("### 🗺️ Interactive City Map")
    
    # Display map - either Florida only or with cities
    if st.session_state.cities_data:
        cities = st.session_state.cities_data
        display_cities_on_map(cities)
    else:
        # Show Florida state map when no cities are loaded
        display_florida_only_map()
    
    # Show other tabs only if cities data is available
    if st.session_state.cities_data:
        cities = st.session_state.cities_data
        
        # Show additional tabs for data analysis
        st.markdown("---")
        
        # Create tabs for different views  
        tab1, tab2, tab3, tab4 = st.tabs([
            "🛣️ Street Data",
            "📊 City Data", 
            "📈 Analytics", 
            "📋 Summary"
        ])
        
        with tab1:
            st.markdown("### 🛣️ Street Data Analysis")
            
            if 'selected_city' in st.session_state and st.session_state.selected_city:
                selected = st.session_state.selected_city
                
                # Load street data using the robust alternative method
                with st.spinner(f"Loading street data for {selected.get('name', 'selected city')}..."):
                    try:
                        # Use the alternative street data method
                        lat, lon = selected.get('latitude', 0), selected.get('longitude', 0)
                        city_name = selected.get('name', 'Unknown')
                        
                        streets = get_alternative_street_data(lat, lon, city_name)
                        
                        if streets:
                            # Store in session state for reuse
                            st.session_state.current_streets = streets
                            display_street_data_table(streets, city_name)
                        else:
                            st.warning("⚠️ No street data available for this city")
                            st.info("This might be due to:")
                            st.markdown("- Limited street data in OpenStreetMap database")
                            st.markdown("- City location might be outside mapped areas")
                            st.markdown("- API connectivity issues")
                    except Exception as e:
                        st.error(f"❌ Error loading street data: {str(e)}")
                        logger.error(f"Street data error: {e}")
            else:
                st.info("🎯 Please select a city from the map above to view street data")
                st.markdown("**How to get started:**")
                st.markdown("1. Press 'FETCH CITY' button from the sidebar")
                st.markdown("2. Select a specific city from the dropdown on the map")
                st.markdown("3. Street data will be displayed here")
        
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