"""
Map View - UI components for map visualization using Mapbox
"""

from typing import Optional, Dict, Any
import streamlit as st
import pydeck as pdk
import logging
from models.city_model import City, CityCollection
from models.street_model import StreetCollection
from models.traffic_model import TrafficCollection
from controllers.mapbox_controller import MapboxController
from controllers.city_controller import CityController
from controllers.traffic_controller import TrafficController

logger = logging.getLogger(__name__)


class MapView:
    """
    View component for map visualization using Mapbox
    """
    
    def __init__(self, mapbox_token: str = "pk.eyJ1IjoiZGFuaWVsMDkyNyIsImEiOiJjbWRtNWQ4aWEwMTM1MmpxNGZxd2E0bmpnIn0.iwPMtSv1shtLXBi8WdxfgA"):
        """
        Initialize the map view with Mapbox integration
        
        Args:
            mapbox_token: Mapbox API token for map rendering
        """
        self.mapbox_controller = MapboxController(mapbox_token)
        self.city_controller = CityController()
        self.traffic_controller = TrafficController()
    
    def display_florida_only_map(self) -> None:
        """
        Display a map showing only the Florida state boundary using Mapbox
        """
        try:
            # Create Florida map with real boundary data
            deck = self.mapbox_controller.create_florida_map()
            
            # Display the map
            with st.container():
                st.markdown('<div class="map-container">', unsafe_allow_html=True)
                st.info("📍 Now showing Florida with **real boundary data** from ArcGIS API! Press the 'FETCH CITY' button from the sidebar to load city data and explore specific locations.")
                
                # Display map style selector
                col1, col2 = st.columns([3, 1])
                with col2:
                    map_style = st.selectbox(
                        "Map Style",
                        options=[
                            'mapbox://styles/mapbox/streets-v11',
                            'mapbox://styles/mapbox/satellite-v9',
                            'mapbox://styles/mapbox/light-v10',
                            'mapbox://styles/mapbox/dark-v10'
                        ],
                        format_func=lambda x: {
                            'mapbox://styles/mapbox/streets-v11': 'Streets',
                            'mapbox://styles/mapbox/satellite-v9': 'Satellite',
                            'mapbox://styles/mapbox/light-v10': 'Light',
                            'mapbox://styles/mapbox/dark-v10': 'Dark'
                        }[x],
                        key="florida_map_style"
                    )
                
                # Update deck with selected style if changed
                if hasattr(st.session_state, 'florida_map_style') and st.session_state.florida_map_style != deck.map_style:
                    deck.map_style = map_style
                
                # Display the Mapbox map using PyDeck
                st.pydeck_chart(deck, use_container_width=True, height=600)
                
                # Show data source info
                st.success("🌍 **Real-time Florida boundary data** fetched from ArcGIS API")
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            logger.error(f"Error displaying Florida only map: {e}")
            st.error("❌ Error displaying map. Please try refreshing the page.")
            st.error(f"Details: {str(e)}")
    
    def display_cities_on_map(self, cities: CityCollection) -> None:
        """
        Display cities on a simplified interactive Mapbox map following the new UI design
        
        Args:
            cities: Collection of cities to display
        """
        try:
            if not cities or len(cities) == 0:
                st.error("🚫 No city data available to display on map")
                return
            
            # Filter cities with valid coordinates
            valid_cities = CityCollection()
            valid_cities.cities = cities.get_valid_cities()
            
            if len(valid_cities) == 0:
                st.error("🚫 No cities with valid coordinates found")
                return
            
            # Initialize session state for selected city
            if 'selected_city' not in st.session_state:
                st.session_state.selected_city = None
            
            # Render the new simplified UI layout
            self._render_simplified_ui_layout(valid_cities)
            
        except Exception as e:
            logger.error(f"Error displaying cities on map: {e}")
            st.error("❌ Error displaying map. Please try refreshing the page.")
            st.error(f"Details: {str(e)}")
    
    def _render_simplified_ui_layout(self, valid_cities: CityCollection) -> None:
        """
        Render the new simplified UI layout following the wireframe design
        
        Args:
            valid_cities: Collection of valid cities to display
        """
        try:
            # Top section: Simple selectors
            st.markdown("### 📍 Select District, County, City")
            self._render_location_selectors(valid_cities)
            
            st.markdown("---")
            
            # Main layout: Left controls + Right map
            left_col, right_col = st.columns([1, 2])
            
            with left_col:
                # Action buttons
                st.markdown("#### 🎯 Actions")
                self._render_action_buttons()
                
                st.markdown("---")
                
                # Statistical tables and important information
                st.markdown("#### 📊 Statistical Information")
                self._render_statistics_panel(valid_cities)
                
            with right_col:
                # Main map area
                st.markdown("#### 🗺️ Google Map")
                self._render_main_map_area(valid_cities)
                
                # Map view settings at bottom right
                st.markdown("---")
                with st.container():
                    st.markdown("##### ⚙️ Map View Settings")
                    self._render_map_settings()
                    
        except Exception as e:
            logger.error(f"Error rendering simplified UI layout: {e}")
            st.error("❌ Error displaying interface")
    
    def _render_location_selectors(self, valid_cities: CityCollection) -> None:
        """
        Render simple district, county, city selectors
        
        Args:
            valid_cities: Collection of cities for dropdown options
        """
        try:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Get unique districts (using state FIPS as district)
                districts = list(set(city.state_fips for city in valid_cities.cities if city.state_fips))
                selected_district = st.selectbox(
                    "District",
                    ["All Districts"] + sorted(districts),
                    key="district_selector"
                )
            
            with col2:
                # County selector - simplified since county data may not be available
                # Using place_fips as a proxy for county grouping
                if selected_district == "All Districts":
                    available_cities = valid_cities.cities
                else:
                    available_cities = [city for city in valid_cities.cities 
                                     if city.state_fips == selected_district]
                
                # Extract county-like groupings from place_fips (first 3 digits typically represent county)
                county_codes = list(set(city.place_fips[:3] if len(city.place_fips) >= 3 else 'N/A' 
                                       for city in available_cities if city.place_fips))
                if not county_codes or county_codes == ['N/A']:
                    county_codes = ["No County Data"]
                
                selected_county = st.selectbox(
                    "County Area", 
                    ["All Areas"] + sorted(county_codes),
                    key="county_selector",
                    help="Grouped by place code prefix"
                )
            
            with col3:
                # Get cities based on selected district and county area
                if selected_county == "All Areas":
                    filtered_cities = available_cities
                else:
                    # Filter by place_fips prefix if county code is selected
                    if selected_county != "No County Data":
                        filtered_cities = [city for city in available_cities 
                                         if city.place_fips.startswith(selected_county)]
                    else:
                        filtered_cities = available_cities
                
                city_options = ["All Cities"] + [city.get_display_name() for city in filtered_cities]
                selected_city_option = st.selectbox(
                    "City",
                    city_options,
                    key="city_selector"
                )
                
                # Update session state with selected city
                if selected_city_option != "All Cities":
                    city_index = city_options.index(selected_city_option) - 1
                    st.session_state.selected_city = filtered_cities[city_index].to_dict()
                else:
                    st.session_state.selected_city = None
                    
        except Exception as e:
            logger.error(f"Error rendering location selectors: {e}")
            st.error("Error in location selectors")
    
    def _render_action_buttons(self) -> None:
        """
        Render simple action buttons
        """
        try:
            # Show data button
            if st.button("📊 Show Data", use_container_width=True, type="primary"):
                st.session_state.show_data_panel = True
                st.rerun()
            
            # Toggle streets
            show_streets = st.checkbox("🛣️ Show Streets", key="toggle_streets")
            
            # Toggle traffic
            show_traffic = st.checkbox("🚦 Show Traffic", key="toggle_traffic")
            
            # Export buttons section
            st.markdown("##### 💾 Export Data")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 Export GeoJSON", use_container_width=True, help="Download geographic data as GeoJSON"):
                    self._export_geojson_data()
            
            with col2:
                if st.button("📊 Export CSV", use_container_width=True, help="Download data as CSV spreadsheet"):
                    self._export_csv_data()
            
            # Refresh data
            if st.button("🔄 Refresh", use_container_width=True):
                # Clear cache and refresh data
                if 'traffic_data' in st.session_state:
                    del st.session_state.traffic_data
                st.rerun()
                
        except Exception as e:
            logger.error(f"Error rendering action buttons: {e}")
    
    def _export_geojson_data(self) -> None:
        """
        Export current data as GeoJSON format
        """
        try:
            # Get current data
            cities = st.session_state.get('cities_data')
            traffic_data = self.traffic_controller.get_session_traffic_data()
            
            if not cities and not traffic_data:
                st.warning("⚠️ No data available to export")
                return
            
            # Create GeoJSON structure
            geojson_data = {
                "type": "FeatureCollection",
                "features": []
            }
            
            # Add city data if available
            if cities:
                for city in cities.cities:
                    if city.has_valid_coordinates():
                        feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [city.longitude, city.latitude]
                            },
                            "properties": {
                                "name": city.name,
                                "geoid": city.geoid,
                                "population": city.population,
                                "land_area": city.land_area,
                                "water_area": city.water_area,
                                "type": "city"
                            }
                        }
                        geojson_data["features"].append(feature)
            
            # Add traffic data if available
            if traffic_data:
                for traffic in traffic_data.traffic_data:
                    if traffic.coordinates and len(traffic.coordinates) > 1:
                        feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "LineString",
                                "coordinates": traffic.coordinates
                            },
                            "properties": {
                                "roadway_name": traffic.roadway_name,
                                "aadt": traffic.aadt,
                                "vc_ratio": traffic.calculate_vc_ratio(),
                                "vc_level": traffic.get_vc_ratio_level(),
                                "traffic_level": traffic.get_traffic_level(),
                                "county": traffic.county,
                                "year": traffic.year,
                                "type": "traffic"
                            }
                        }
                        geojson_data["features"].append(feature)
            
            # Convert to JSON string
            import json
            geojson_str = json.dumps(geojson_data, indent=2)
            
            # Create download button
            st.download_button(
                label="⬇️ Download GeoJSON",
                data=geojson_str,
                file_name=f"fdot_data_{len(geojson_data['features'])}_features.geojson",
                mime="application/geo+json",
                help=f"Download {len(geojson_data['features'])} geographic features"
            )
            
            st.success(f"✅ GeoJSON ready for download with {len(geojson_data['features'])} features!")
            
        except Exception as e:
            logger.error(f"Error exporting GeoJSON: {e}")
            st.error(f"❌ Export failed: {str(e)}")
    
    def _export_csv_data(self) -> None:
        """
        Export current data as CSV format
        """
        try:
            import pandas as pd
            import io
            
            # Get current data
            cities = st.session_state.get('cities_data')
            traffic_data = self.traffic_controller.get_session_traffic_data()
            
            if not cities and not traffic_data:
                st.warning("⚠️ No data available to export")
                return
            
            # Create CSV data
            csv_data = []
            
            # Add city data if available
            if cities:
                for city in cities.cities:
                    csv_data.append({
                        'Type': 'City',
                        'Name': city.name,
                        'GEOID': city.geoid,
                        'Population': city.population,
                        'Land Area (sq m)': city.land_area,
                        'Water Area (sq m)': city.water_area,
                        'Latitude': city.latitude,
                        'Longitude': city.longitude,
                        'State FIPS': city.state_fips,
                        'AADT': '',
                        'V/C Ratio': '',
                        'Level of Service': '',
                        'County': '',
                        'Year': ''
                    })
            
            # Add traffic data if available
            if traffic_data:
                for traffic in traffic_data.traffic_data:
                    csv_data.append({
                        'Type': 'Traffic',
                        'Name': traffic.roadway_name,
                        'GEOID': '',
                        'Population': '',
                        'Land Area (sq m)': '',
                        'Water Area (sq m)': '',
                        'Latitude': traffic.get_midpoint()[1] if traffic.get_midpoint() else '',
                        'Longitude': traffic.get_midpoint()[0] if traffic.get_midpoint() else '',
                        'State FIPS': '',
                        'AADT': traffic.aadt,
                        'V/C Ratio': round(traffic.calculate_vc_ratio(), 3),
                        'Level of Service': traffic.get_vc_ratio_level(),
                        'County': traffic.county,
                        'Year': traffic.year
                    })
            
            # Convert to DataFrame
            df = pd.DataFrame(csv_data)
            
            # Convert to CSV string
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_str = csv_buffer.getvalue()
            
            # Create download button
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_str,
                file_name=f"fdot_data_{len(csv_data)}_records.csv",
                mime="text/csv",
                help=f"Download {len(csv_data)} records as CSV"
            )
            
            st.success(f"✅ CSV ready for download with {len(csv_data)} records!")
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            st.error(f"❌ Export failed: {str(e)}")
    
    def _render_statistics_panel(self, valid_cities: CityCollection) -> None:
        """
        Render clean statistics panel with important information
        
        Args:
            valid_cities: Collection of cities for statistics
        """
        try:
            # Basic statistics
            with st.container():
                st.metric("🏙️ Total Cities", len(valid_cities))
                st.metric("👥 Total Population", f"{valid_cities.get_total_population():,}")
                st.metric("🏞️ Total Area", f"{valid_cities.get_total_land_area()/1000000:.1f} km²")
            
            # Selected city details
            if st.session_state.get('selected_city'):
                city_data = st.session_state.selected_city
                st.markdown("##### 🎯 Selected City")
                with st.container():
                    st.info(f"**{city_data.get('name', 'Unknown')}**")
                    st.metric("Population", f"{city_data.get('population', 0):,}")
                    st.metric("Area", f"{city_data.get('land_area', 0)/1000000:.2f} km²")
            
            # Traffic statistics if available
            if st.session_state.get('toggle_traffic', False):
                traffic_data = self.traffic_controller.get_session_traffic_data()
                if traffic_data:
                    stats = self.traffic_controller.get_traffic_statistics(traffic_data)
                    st.markdown("##### 🚦 Traffic Data")
                    st.metric("Segments", stats.get('total_segments', 0))
                    st.metric("Avg Volume", f"{stats.get('avg_volume', 0):,.0f}")
                    
                    # Add V/C Ratio Color Legend
                    with st.expander("🎨 V/C Ratio Color Legend", expanded=False):
                        st.markdown("""
                        <div style="font-size: 11px;">
                        <div style="display: flex; align-items: center; margin: 2px 0;">
                            <div style="width: 15px; height: 4px; background: rgb(139,0,0); margin-right: 6px;"></div>
                            <span>V/C ≥ 1.0 - LOS F (Oversaturated)</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 2px 0;">
                            <div style="width: 15px; height: 4px; background: rgb(255,0,0); margin-right: 6px;"></div>
                            <span>V/C ≥ 0.85 - LOS E (Forced Flow)</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 2px 0;">
                            <div style="width: 15px; height: 4px; background: rgb(255,69,0); margin-right: 6px;"></div>
                            <span>V/C ≥ 0.70 - LOS D (High Density)</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 2px 0;">
                            <div style="width: 15px; height: 4px; background: rgb(255,140,0); margin-right: 6px;"></div>
                            <span>V/C ≥ 0.55 - LOS C (Stable Flow)</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 2px 0;">
                            <div style="width: 15px; height: 4px; background: rgb(255,215,0); margin-right: 6px;"></div>
                            <span>V/C ≥ 0.35 - LOS B (Free Flow)</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 2px 0;">
                            <div style="width: 15px; height: 4px; background: rgb(0,255,0); margin-right: 6px;"></div>
                            <span>V/C < 0.35 - LOS A (Free Flow)</span>
                        </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
        except Exception as e:
            logger.error(f"Error rendering statistics panel: {e}")
    
    def _render_main_map_area(self, valid_cities: CityCollection) -> None:
        """
        Render the main map area
        
        Args:
            valid_cities: Collection of cities to display on map
        """
        try:
            # Get current settings
            selected_city = None
            if st.session_state.get('selected_city'):
                # Find the city object from session state
                city_data = st.session_state.selected_city
                for city in valid_cities.cities:
                    if city.geoid == city_data.get('geoid'):
                        selected_city = city
                        break
            
            show_streets = st.session_state.get('toggle_streets', False)
            show_traffic = st.session_state.get('toggle_traffic', False)
            
            # Get streets data if needed
            streets = None
            if show_streets and selected_city:
                from controllers.street_controller import StreetController
                street_controller = StreetController()
                streets = street_controller.get_streets_for_city(selected_city)
            
            # Get traffic data if needed - automatically fetch when traffic is enabled
            traffic_data = None
            if show_traffic:
                with st.spinner("🚦 Loading traffic data..."):
                    traffic_data = self._get_or_fetch_traffic_data(force_refresh=False)
            
            # Get map style from settings
            map_style = st.session_state.get('map_style_selector', 'mapbox://styles/mapbox/streets-v11')
            
            # Create map with simplified settings
            deck = self.mapbox_controller.create_florida_map(
                cities=valid_cities,
                selected_city=selected_city,
                streets=streets,
                traffic_data=traffic_data,
                show_traffic=show_traffic,
                show_only_selected=(selected_city is not None),
                map_style=map_style
            )
            
            # Display the map
            st.pydeck_chart(deck, use_container_width=True, height=500)
            
        except Exception as e:
            logger.error(f"Error rendering main map area: {e}")
            st.error("Error displaying map")
    
    def _render_map_settings(self) -> None:
        """
        Render simple map view settings and filter options at bottom right
        """
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                # Map style selector
                map_style = st.selectbox(
                    "Map Style",
                    options=[
                        'mapbox://styles/mapbox/streets-v11',
                        'mapbox://styles/mapbox/satellite-v9',
                        'mapbox://styles/mapbox/light-v10',
                        'mapbox://styles/mapbox/dark-v10'
                    ],
                    format_func=lambda x: {
                        'mapbox://styles/mapbox/streets-v11': 'Streets',
                        'mapbox://styles/mapbox/satellite-v9': 'Satellite',
                        'mapbox://styles/mapbox/light-v10': 'Light',
                        'mapbox://styles/mapbox/dark-v10': 'Dark'
                    }[x],
                    key="map_style_selector"
                )
            
            with col2:
                # Simple filter options
                zoom_to_selection = st.checkbox("🎯 Zoom to Selection", key="zoom_to_selection")
                show_labels = st.checkbox("🏷️ Show Labels", value=True, key="show_labels")
                
        except Exception as e:
            logger.error(f"Error rendering map settings: {e}")
    
    def _render_mapbox_controls(self, valid_cities: CityCollection) -> tuple:
        """
        Render Mapbox map control options including traffic data controls
        
        Args:
            valid_cities: Collection of valid cities
            
        Returns:
            Tuple of (selected_city, show_only_selected, show_streets, map_style, traffic_options)
        """
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # City selector
            city_options = ["View All Cities"] + [city.get_display_name() for city in valid_cities.cities]
            selected_option = st.selectbox(
                "🎯 Select View",
                city_options,
                index=0,
                help="Choose 'View All Cities' or select a specific city for detailed view"
            )
            
            if selected_option == "View All Cities":
                st.session_state.selected_city = None
                selected_city = None
                show_only_selected = False
            else:
                # Find the selected city
                selected_index = city_options.index(selected_option) - 1
                selected_city = valid_cities.cities[selected_index]
                st.session_state.selected_city = selected_city.to_dict()
                show_only_selected = True
        
        with col2:
            if selected_city:
                show_streets = st.checkbox("🛣️ Show Streets", value=True, help="Display street network for selected city")
            else:
                show_streets = False
                st.info("📍 Select a specific city to view streets")
        
        with col3:
            # Map style selector
            map_style = st.selectbox(
                "🗺️ Map Style",
                options=[
                    'mapbox://styles/mapbox/streets-v11',
                    'mapbox://styles/mapbox/satellite-v9',
                    'mapbox://styles/mapbox/light-v10',
                    'mapbox://styles/mapbox/dark-v10'
                ],
                format_func=lambda x: {
                    'mapbox://styles/mapbox/streets-v11': 'Streets',
                    'mapbox://styles/mapbox/satellite-v9': 'Satellite',
                    'mapbox://styles/mapbox/light-v10': 'Light',
                    'mapbox://styles/mapbox/dark-v10': 'Dark'
                }[x],
                index=0,
                help="Select Mapbox map style"
            )
        
        with col4:
            # Traffic data controls
            show_traffic_data = st.checkbox("🚦 Show Traffic", value=False, 
                                           help="Display FDOT Annual Average Daily Traffic (AADT) data (automatically fetches most recent year available)")
        
        # Initialize traffic options with default values
        traffic_options = {
            'show_traffic_data': show_traffic_data,
            'show_heatmap': False,
            'traffic_level_filter': None,
            'county_filter': None,
            'roadway_filter': None,
            'max_records': None,  # No default limit
            'force_refresh': False
        }
        
        if show_traffic_data:
            st.markdown("### 🚦 Traffic Data Controls")
            st.info("💡 **Auto-Recent Data:** The system automatically fetches the most recent year of AADT data available from FDOT.")
            
            # Create traffic control columns
            traffic_col1, traffic_col2, traffic_col3, traffic_col4 = st.columns(4)
            
            with traffic_col1:
                show_heatmap = st.checkbox("🌡️ AADT Heatmap", value=False,
                                         help="Show Annual Average Daily Traffic as heatmap overlay")
                
                traffic_level_filter = st.selectbox(
                    "📊 Traffic Level Filter",
                    options=['All', 'Low', 'Moderate', 'High', 'Heavy'],
                    index=0,
                    help="Filter traffic data by congestion level"
                )
            
            with traffic_col2:
                county_filter = st.text_input("🏢 County Filter", 
                                            placeholder="e.g., Miami-Dade",
                                            help="Filter by county name (optional)")
                
                roadway_filter = st.text_input("🛣️ Roadway Filter",
                                             placeholder="e.g., I-95",
                                             help="Filter by roadway name (optional)")
            
            with traffic_col3:
                # Option to limit records for performance
                limit_records = st.checkbox("📊 Limit Records", value=False,
                                          help="Check to limit the number of traffic segments for better performance")
                
                max_records = None
                if limit_records:
                    max_records = st.number_input("Max Records", 
                                                min_value=100, max_value=10000, 
                                                value=5000, step=100,
                                                help="Maximum number of traffic segments to load")
                
                force_refresh = st.button("🔄 Refresh Traffic Data",
                                        help="Force refresh of traffic data from server")
            
            with traffic_col4:
                # Traffic data status and info
                traffic_data = self.traffic_controller.get_session_traffic_data()
                if traffic_data:
                    stats = self.traffic_controller.get_traffic_statistics(traffic_data)
                    st.metric("📍 Traffic Segments", stats.get('total_segments', 0))
                    st.metric("🚗 Avg Volume", f"{stats.get('avg_volume', 0):,.0f}")
                else:
                    st.info("👆 Enable traffic data above to load FDOT AADT information")
            
            # Add AADT Color Legend
            if show_traffic_data:
                st.markdown("### 🎨 AADT Traffic Volume Color Legend")
                legend_col1, legend_col2 = st.columns(2)
                
                with legend_col1:
                    st.markdown("""
                    <div style="font-size: 12px;">
                    <div style="display: flex; align-items: center; margin: 2px 0;">
                        <div style="width: 20px; height: 8px; background: rgb(139,0,0); margin-right: 8px;"></div>
                        <span>75,000+ vehicles/day (Very Heavy)</span>
                    </div>
                    <div style="display: flex; align-items: center; margin: 2px 0;">
                        <div style="width: 20px; height: 6px; background: rgb(255,0,0); margin-right: 8px;"></div>
                        <span>50,000-75,000 vehicles/day (Heavy)</span>
                    </div>
                    <div style="display: flex; align-items: center; margin: 2px 0;">
                        <div style="width: 20px; height: 5px; background: rgb(255,69,0); margin-right: 8px;"></div>
                        <span>35,000-50,000 vehicles/day (High)</span>
                    </div>
                    <div style="display: flex; align-items: center; margin: 2px 0;">
                        <div style="width: 20px; height: 4px; background: rgb(255,140,0); margin-right: 8px;"></div>
                        <span>25,000-35,000 vehicles/day</span>
                    </div>
                    <div style="display: flex; align-items: center; margin: 2px 0;">
                        <div style="width: 20px; height: 3px; background: rgb(255,165,0); margin-right: 8px;"></div>
                        <span>15,000-25,000 vehicles/day</span>
                    </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with legend_col2:
                    st.markdown("""
                    <div style="font-size: 12px;">
                    <div style="display: flex; align-items: center; margin: 2px 0;">
                        <div style="width: 20px; height: 3px; background: rgb(255,215,0); margin-right: 8px;"></div>
                        <span>10,000-15,000 vehicles/day</span>
                    </div>
                    <div style="display: flex; align-items: center; margin: 2px 0;">
                        <div style="width: 20px; height: 2px; background: rgb(255,255,0); margin-right: 8px;"></div>
                        <span>5,000-10,000 vehicles/day</span>
                    </div>
                    <div style="display: flex; align-items: center; margin: 2px 0;">
                        <div style="width: 20px; height: 2px; background: rgb(154,205,50); margin-right: 8px;"></div>
                        <span>2,000-5,000 vehicles/day</span>
                    </div>
                    <div style="display: flex; align-items: center; margin: 2px 0;">
                        <div style="width: 20px; height: 1px; background: rgb(0,255,0); margin-right: 8px;"></div>
                        <span>500-2,000 vehicles/day (Low)</span>
                    </div>
                    <div style="display: flex; align-items: center; margin: 2px 0;">
                        <div style="width: 20px; height: 1px; background: rgb(105,105,105); margin-right: 8px;"></div>
                        <span>&lt; 500 vehicles/day (Minimal)</span>
                    </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Update traffic options
            traffic_options.update({
                'show_heatmap': show_heatmap,
                'traffic_level_filter': traffic_level_filter if traffic_level_filter != 'All' else None,
                'county_filter': county_filter if county_filter.strip() else None,
                'roadway_filter': roadway_filter if roadway_filter.strip() else None,
                'max_records': max_records,
                'force_refresh': force_refresh
            })
        
        return selected_city, show_only_selected, show_streets, map_style, traffic_options
    
    def _display_mapbox_with_stats(self, deck: pdk.Deck, valid_cities: CityCollection, selected_city: Optional[City]) -> None:
        """
        Display Mapbox map with statistics and interaction
        
        Args:
            deck: PyDeck map object
            valid_cities: Collection of valid cities
            selected_city: Currently selected city
        """
        try:
            # Display map in container with custom styling
            with st.container():
                st.markdown('<div class="map-container">', unsafe_allow_html=True)
                
                # Map header with statistics
                self._display_map_statistics(valid_cities)
                
                st.markdown("---")
                
                # Display the Mapbox map using PyDeck
                st.pydeck_chart(deck, use_container_width=True, height=600)
                
                # Show selected city details
                if selected_city:
                    self._display_selected_city_details(selected_city)
                
                # Show data source info
                st.success("🌍 **Enhanced with Mapbox** - Real-time Florida boundary data from ArcGIS API")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            logger.error(f"Error displaying Mapbox map with stats: {e}")
            st.error("❌ Error displaying map. Please try refreshing the page.")
    
    def _display_map_statistics(self, cities: CityCollection) -> None:
        """Display map statistics header"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏙️ Cities Mapped", len(cities))
        with col2:
            total_pop = cities.get_total_population()
            st.metric("👥 Total Population", f"{total_pop:,}")
        with col3:
            avg_pop = cities.get_average_population()
            st.metric("📊 Average Population", f"{avg_pop:,.0f}")
        with col4:
            total_area = cities.get_total_land_area()
            st.metric("🏞️ Total Land Area", f"{total_area/1000000:.1f} km²")
    
    def _display_selected_city_details(self, selected_city: City) -> None:
        """Display details for selected city"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"🎯 **Selected City:** {selected_city.name}")
            st.metric("👥 Population", f"{selected_city.population:,}")
        with col2:
            st.metric("🏞️ Land Area", f"{selected_city.land_area/1000000:.2f} km²")
            st.metric("📍 Coordinates", f"{selected_city.latitude:.4f}, {selected_city.longitude:.4f}")
        with col3:
            st.metric("🆔 GEOID", selected_city.geoid)
            st.metric("🌊 Water Area", f"{selected_city.water_area/1000000:.2f} km²")
    
    def _get_or_fetch_traffic_data(self, 
                                  county_filter: Optional[str] = None,
                                  roadway_filter: Optional[str] = None,
                                  max_records: Optional[int] = None,
                                  force_refresh: bool = False) -> Optional[TrafficCollection]:
        """
        Get traffic data from session or fetch from API
        
        Args:
            county_filter: Optional county name to filter results
            roadway_filter: Optional roadway name to filter results
            max_records: Maximum number of records to fetch
            force_refresh: Force refresh of cached data
            
        Returns:
            TrafficCollection with traffic data or None if error
        """
        try:
            with st.spinner("🚦 Loading FDOT AADT data..."):
                # Fetch traffic data
                traffic_data = self.traffic_controller.fetch_and_cache_traffic_data(
                    county_filter=county_filter,
                    roadway_filter=roadway_filter,
                    max_records=max_records,
                    force_refresh=force_refresh
                )
                
                if traffic_data and len(traffic_data) > 0:
                    # Display success message with statistics
                    stats = self.traffic_controller.get_traffic_statistics(traffic_data)
                    
                    # Get year information from the data
                    years_in_data = set(td.year for td in traffic_data.traffic_data)
                    years_str = ", ".join(map(str, sorted(years_in_data, reverse=True)))
                    most_recent_year = max(years_in_data) if years_in_data else "Unknown"
                    
                    st.success(f"✅ Loaded {stats['total_segments']} AADT segments "
                             f"(Most Recent Year: {most_recent_year}, Avg AADT: {stats['avg_volume']:,.0f} vehicles/day)")
                    
                    # Display year information prominently
                    if len(years_in_data) == 1:
                        st.info(f"📅 **Data Year:** {most_recent_year} (Most recent available from FDOT)")
                    else:
                        st.info(f"📅 **Data Years:** {years_str} (Displaying most recent available data)")
                    
                    # Display traffic level breakdown
                    level_counts = stats['traffic_levels']
                    if any(level_counts.values()):
                        cols = st.columns(4)
                        level_colors = {
                            'Low': '🟢', 'Moderate': '🟡', 'High': '🟠', 'Heavy': '🔴'
                        }
                        for idx, (level, count) in enumerate(level_counts.items()):
                            if count > 0:
                                with cols[idx % 4]:
                                    st.metric(f"{level_colors.get(level, '⚪')} {level}", count)
                    
                    return traffic_data
                else:
                    st.warning("⚠️ No traffic data found with current filters")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching traffic data: {e}")
            st.error("❌ Failed to load traffic data. Please try again.")
            return None
    
    def display_traffic_data_tab(self) -> None:
        """
        Display traffic data analysis tab
        """
        try:
            st.markdown("### 🚦 FDOT AADT Traffic Analysis")
            
            # Get traffic data from session
            traffic_data = self.traffic_controller.get_session_traffic_data()
            
            if not traffic_data:
                st.info("👆 Enable traffic data in the map view above to see AADT analysis")
                
                # Option to fetch traffic data directly
                if st.button("🚦 Load AADT Data Now"):
                    traffic_data = self._get_or_fetch_traffic_data()
                
                if not traffic_data:
                    return
            
            # Traffic data analysis interface
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Traffic statistics
                stats = self.traffic_controller.get_traffic_statistics(traffic_data)
                self._display_traffic_statistics(stats)
                
                # AADT data table
                st.markdown("#### 📊 AADT Data Table")
                self._display_traffic_data_table(traffic_data)
            
            with col2:
                # Traffic controls and filters
                st.markdown("#### 🎛️ Analysis Controls")
                filters = self._create_traffic_filters(traffic_data)
                
                # Export options
                st.markdown("#### 💾 Export Options")
                self._create_traffic_export_options(traffic_data)
                
                # Data quality information
                st.markdown("#### ℹ️ Data Info")
                self._display_traffic_data_info(traffic_data)
            
        except Exception as e:
            logger.error(f"Error displaying traffic data tab: {e}")
            st.error("❌ Error displaying traffic analysis")
    
    def _display_traffic_statistics(self, stats: Dict) -> None:
        """Display AADT statistics overview"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🛣️ Total Segments", stats.get('total_segments', 0))
            st.metric("🚗 Total AADT", f"{stats.get('total_volume', 0):,}")
        
        with col2:
            st.metric("📈 Avg AADT", f"{stats.get('avg_volume', 0):,.0f}")
            traffic_levels = stats.get('traffic_levels', {})
            st.metric("🔴 Heavy Traffic", traffic_levels.get('Heavy', 0))
        
        with col3:
            st.metric("🟠 High Traffic", traffic_levels.get('High', 0))
            st.metric("🟡 Moderate Traffic", traffic_levels.get('Moderate', 0))
        
        with col4:
            st.metric("🟢 Low Traffic", traffic_levels.get('Low', 0))
            if stats.get('last_updated'):
                from datetime import datetime
                try:
                    updated_time = datetime.fromisoformat(stats['last_updated'])
                    st.metric("🕒 Updated", updated_time.strftime('%H:%M'))
                except:
                    st.metric("🕒 Updated", "Recent")
    
    def _display_traffic_data_table(self, traffic_data: TrafficCollection) -> None:
        """Display AADT data in tabular format with pagination and sorting by most recent date"""
        import pandas as pd
        
        # Convert traffic data to DataFrame
        data_for_table = []
        for traffic in traffic_data.traffic_data:
            data_for_table.append({
                'Roadway': traffic.roadway_name,
                'From': traffic.desc_from,
                'To': traffic.desc_to,
                'County': traffic.county,
                'District': traffic.district,
                'AADT': traffic.aadt,
                'AADT Flag': traffic.aadt_flag,
                'Traffic Level': traffic.get_traffic_level(),
                'Year': traffic.year,
                'Data Quality': traffic.data_quality,
                'Data Timestamp': traffic.data_timestamp
            })
        
        if data_for_table:
            df = pd.DataFrame(data_for_table)
            
            # Sort by most recent date (Year) as default - descending order for most recent first
            df = df.sort_values(['Year', 'Data Timestamp'], ascending=[False, False])
            
            # Display paginated table with all data
            self._display_paginated_data_table(df, "aadt_traffic")
        else:
            st.warning("No traffic data to display")
    
    def _display_paginated_data_table(self, df, table_key: str, 
                                     items_per_page: int = 20) -> None:
        """
        Display paginated data table with navigation controls for traffic data
        
        Args:
            df: DataFrame to display
            table_key: Unique key for the table session state
            items_per_page: Number of items to display per page
        """
        try:
            if df.empty:
                st.info("No data to display")
                return
            
            # Initialize session state for pagination
            page_key = f"{table_key}_page"
            if page_key not in st.session_state:
                st.session_state[page_key] = 0
            
            total_rows = len(df)
            total_pages = (total_rows - 1) // items_per_page + 1
            
            # Pagination controls
            if total_pages > 1:
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                
                with col1:
                    if st.button("⏪ First", key=f"{table_key}_first", 
                               disabled=st.session_state[page_key] == 0):
                        st.session_state[page_key] = 0
                        st.rerun()
                
                with col2:
                    if st.button("◀ Previous", key=f"{table_key}_prev", 
                               disabled=st.session_state[page_key] == 0):
                        st.session_state[page_key] -= 1
                        st.rerun()
                
                with col3:
                    st.write(f"Page {st.session_state[page_key] + 1} of {total_pages} "
                            f"({total_rows:,} total records)")
                
                with col4:
                    if st.button("Next ▶", key=f"{table_key}_next", 
                               disabled=st.session_state[page_key] >= total_pages - 1):
                        st.session_state[page_key] += 1
                        st.rerun()
                
                with col5:
                    if st.button("Last ⏩", key=f"{table_key}_last", 
                               disabled=st.session_state[page_key] >= total_pages - 1):
                        st.session_state[page_key] = total_pages - 1
                        st.rerun()
            
            # Calculate start and end indices for current page
            start_idx = st.session_state[page_key] * items_per_page
            end_idx = min(start_idx + items_per_page, total_rows)
            
            # Display current page data
            page_df = df.iloc[start_idx:end_idx]
            
            # Configure columns for better display
            column_config = {
                "AADT": st.column_config.NumberColumn(
                    "AADT (Annual Average Daily Traffic)",
                    help="Annual Average Daily Traffic volume",
                    format="%d"
                ),
                "Year": st.column_config.NumberColumn(
                    "Data Year",
                    help="Year of the traffic data collection"
                ),
                "Traffic Level": st.column_config.TextColumn(
                    "Traffic Level",
                    help="Classification based on AADT volume"
                )
            }
            
            st.dataframe(
                page_df, 
                use_container_width=True,
                height=400,
                column_config=column_config
            )
            
            # Show items count for current page
            if total_pages > 1:
                st.caption(f"Showing items {start_idx + 1}-{end_idx} of {total_rows} "
                          f"(sorted by most recent data)")
            else:
                st.caption(f"Showing all {total_rows} records (sorted by most recent data)")
            
        except Exception as e:
            logger.error(f"Error displaying paginated traffic table: {e}")
            st.error("Error displaying table data")
    
    def _create_traffic_filters(self, traffic_data: TrafficCollection) -> Dict:
        """Create traffic data filter controls"""
        filters = {}
        
        # County filter
        counties = traffic_data.get_unique_counties()
        if counties:
            filters['county'] = st.selectbox(
                "🏢 Filter by County",
                ['All'] + counties,
                key="traffic_county_filter"
            )
        
        # Roadway filter
        roadways = traffic_data.get_unique_roadways()[:20]  # Limit for performance
        if roadways:
            filters['roadway'] = st.selectbox(
                "🛣️ Filter by Roadway",
                ['All'] + roadways,
                key="traffic_roadway_filter"
            )
        
        # Traffic level filter
        filters['traffic_level'] = st.selectbox(
            "📊 Filter by Traffic Level",
            ['All', 'Low', 'Moderate', 'High', 'Heavy'],
            key="traffic_level_filter"
        )
        
        return filters
    
    def _create_traffic_export_options(self, traffic_data: TrafficCollection) -> None:
        """Create traffic data export options"""
        export_format = st.selectbox(
            "📁 Export Format",
            ['GeoJSON', 'JSON', 'CSV'],
            key="traffic_export_format"
        )
        
        if st.button("💾 Export Traffic Data"):
            try:
                exported_data = self.traffic_controller.export_traffic_data(
                    traffic_data, export_format.lower()
                )
                
                # Create download
                filename = f"traffic_data.{export_format.lower()}"
                st.download_button(
                    label=f"⬇️ Download {export_format}",
                    data=exported_data,
                    file_name=filename,
                    mime="application/json" if export_format != "CSV" else "text/csv"
                )
                
            except Exception as e:
                st.error(f"Export failed: {e}")
    
    def _display_traffic_data_info(self, traffic_data: TrafficCollection) -> None:
        """Display traffic data information and metadata"""
        st.info(f"📊 **Data Source:** FDOT Annual Average Daily Traffic (AADT)")
        st.info(f"🔢 **Total Segments:** {len(traffic_data)}")
        
        # Display year information
        if traffic_data.traffic_data:
            years_in_data = set(td.year for td in traffic_data.traffic_data)
            years_str = ", ".join(map(str, sorted(years_in_data, reverse=True)))
            most_recent_year = max(years_in_data) if years_in_data else "Unknown"
            
            if len(years_in_data) == 1:
                st.info(f"📅 **Data Year:** {most_recent_year} (Most recent available)")
            else:
                st.info(f"📅 **Data Years:** {years_str}")
        
        if traffic_data.last_updated:
            st.info(f"🕒 **Last Fetched:** {traffic_data.last_updated}")
        
        # Data quality overview
        quality_counts = {}
        for traffic in traffic_data.traffic_data:
            quality = traffic.data_quality
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        if quality_counts:
            st.markdown("**Data Quality:**")
            for quality, count in quality_counts.items():
                if quality != 'Unknown':
                    st.write(f"• {quality}: {count} segments")