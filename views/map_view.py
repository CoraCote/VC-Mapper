"""
Map View - UI components for map visualization using Mapbox
"""

from typing import Optional, Dict, Any
import streamlit as st
import pydeck as pdk
import logging
from models.city_model import City, CityCollection
from controllers.mapbox_controller import MapboxController
from controllers.city_controller import CityController

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
    
    def display_florida_only_map(self) -> None:
        """
        Display a map showing only the Florida state boundary using Mapbox
        """
        try:
            # Always load traffic data for map display
            traffic_data = self._get_traffic_data_for_map()
            
            # Create Florida map with real boundary data and traffic
            deck = self.mapbox_controller.create_florida_map(traffic_data=traffic_data)
            
            # Display the map
            with st.container():
                st.markdown('<div class="map-container">', unsafe_allow_html=True)
                st.info("📍 Now showing Florida with **real boundary data** and **traffic roadway segments**! Press the 'FETCH CITY' button from the sidebar to load city data and explore specific locations.")
                
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
                if traffic_data:
                    st.success("🌍 **Real-time Florida boundary data** and **🚦 traffic roadway segments** loaded!")
                else:
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
            st.markdown("### 📍 Select City")
            self._render_location_selectors(valid_cities)
            
            st.markdown("---")
            
            # Main layout: Left controls + Right map
            left_col, right_col = st.columns([1, 2])
            
            with left_col:
                # Action buttons
                st.markdown("#### 🎯 Actions")
                self._render_action_buttons()
                
                # Map view settings below refresh button
                st.markdown("---")
                st.markdown("##### ⚙️ Map View Settings")
                self._render_map_settings()
                
                st.markdown("---")
                
                # Statistical tables and important information
                st.markdown("#### 📊 Statistical Information")
                self._render_statistics_panel(valid_cities)
                
            with right_col:
                # Main map area
                st.markdown("#### 🗺️ Google Map")
                self._render_main_map_area(valid_cities)
                    
        except Exception as e:
            logger.error(f"Error rendering simplified UI layout: {e}")
            st.error("❌ Error displaying interface")
    
    def _render_location_selectors(self, valid_cities: CityCollection) -> None:
        """
        Render simple city selector
        
        Args:
            valid_cities: Collection of cities for dropdown options
        """
        try:
            # Simple city selector without district/county filters
            city_options = ["All Cities"] + [city.get_display_name() for city in valid_cities.cities]
            
            # Handle auto-scaled city selection
            default_index = 0  # Default to "All Cities"
            if st.session_state.get('auto_scaled_city', False) and st.session_state.get('selected_city'):
                # Find the auto-selected city in the dropdown
                auto_selected_city_name = st.session_state.selected_city.get('name', '')
                city_found = False
                for i, city in enumerate(valid_cities.cities):
                    if city.name == auto_selected_city_name:
                        default_index = i + 1  # +1 because of "All Cities" at index 0
                        city_found = True
                        break
                
                # If city not found, reset to "All Cities"
                if not city_found:
                    default_index = 0
            
            selected_city_option = st.selectbox(
                "City",
                city_options,
                index=default_index,
                key="city_selector"
            )
            
            # Update session state with selected city
            if selected_city_option != "All Cities":
                city_index = city_options.index(selected_city_option) - 1
                st.session_state.selected_city = valid_cities.cities[city_index].to_dict()
            else:
                st.session_state.selected_city = None
                
        except Exception as e:
            logger.error(f"Error rendering location selectors: {e}")
            st.error("Error in location selectors")
    
    def _render_action_buttons(self) -> None:
        """
        Render simplified, independent action buttons
        """
        try:
            # Main data display button
            if st.button("📊 Show Data", use_container_width=True, type="primary"):
                st.session_state.show_data_panel = True
                st.rerun()
            
            st.markdown("##### 🗺️ Map Layers")
            
            # Map layers coming soon
            st.info("🚧 Additional map layers will be available in future updates!")
            
            st.markdown("##### 💾 Export")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 GeoJSON", use_container_width=True, help="Download geographic data"):
                    self._export_geojson_data()
            
            with col2:
                if st.button("📊 CSV", use_container_width=True, help="Download spreadsheet data"):
                    self._export_csv_data()
            
            # Simple refresh
            if st.button("🔄 Refresh Map", use_container_width=True, help="Clear cache and refresh data"):
                # Clear cache and refresh data
                
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
            
            if not cities:
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
            
            if not cities:
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
                        'State FIPS': city.state_fips
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
            
            # Get map style from settings
            map_style = st.session_state.get('map_style_selector', 'mapbox://styles/mapbox/streets-v11')
            
            # Show auto-scaling indicator if a city was auto-selected from search
            if selected_city and st.session_state.get('auto_scaled_city', False):
                st.info(f"🎯 **Auto-zoomed to {selected_city.name}** - Map scaled to city area for better visibility!")
                # Clear the auto-scale flag after displaying the indicator
                st.session_state.auto_scaled_city = False
            
            # Always load traffic data for map display
            traffic_data = self._get_traffic_data_for_map()
            
            # Create map with simplified settings
            deck = self.mapbox_controller.create_florida_map(
                cities=valid_cities,
                selected_city=selected_city,
                show_only_selected=(selected_city is not None),
                traffic_data=traffic_data,
                map_style=map_style
            )
            
            # Display the map
            st.pydeck_chart(deck, use_container_width=True, height=500)
            
            # Traffic V/C Ratio Legend in row format below the map
            st.markdown("---")
            st.markdown("**🚦 Traffic V/C Ratio Legend:**")
            
            # Get traffic data for analytics
            if traffic_data and 'features' in traffic_data:
                from models.city_model import TrafficDataCollection
                traffic_collection = TrafficDataCollection(traffic_data)
                analytics = traffic_collection.get_vc_ratio_analytics()
                
                # Display legend in row format (4 columns)
                legend_col1, legend_col2, legend_col3, legend_col4 = st.columns(4)
                
                categories = [
                    ('low', legend_col1),
                    ('moderate', legend_col2), 
                    ('high', legend_col3),
                    ('over_capacity', legend_col4)
                ]
                
                for category, col in categories:
                    with col:
                        if category in analytics and analytics[category]['count'] > 0:
                            data = analytics[category]
                            st.markdown(f"{data['color']} **{data['name']}**")
                            st.markdown(f"V/C: {data['min_vc_ratio']:.2f}-{data['max_vc_ratio']:.2f}")
                            st.markdown(f"📊 {data['count']} segments")
                            st.markdown(f"({data['percentage']:.1f}%)")
                            st.markdown(f"🚗 Avg: {data['avg_aadt']:,.0f}")
                            if data['top_counties']:
                                st.markdown(f"📍 {', '.join(data['top_counties'][:2])}")
                        else:
                            # Show empty category
                            if category == 'low':
                                st.markdown("🟢 **Low Congestion**")
                                st.markdown("V/C < 0.5")
                                st.markdown("📊 No data")
                            elif category == 'moderate':
                                st.markdown("🟡 **Moderate**")
                                st.markdown("0.5 ≤ V/C < 0.8")
                                st.markdown("📊 No data")
                            elif category == 'high':
                                st.markdown("🟠 **High**")
                                st.markdown("0.8 ≤ V/C < 1.0")
                                st.markdown("📊 No data")
                            elif category == 'over_capacity':
                                st.markdown("🔴 **Over Capacity**")
                                st.markdown("V/C ≥ 1.0")
                                st.markdown("📊 No data")
            else:
                # Fallback legend without analytics in row format
                legend_col1, legend_col2, legend_col3, legend_col4 = st.columns(4)
                
                with legend_col1:
                    st.markdown("🟢 **Low**")
                    st.markdown("V/C < 0.5")
                with legend_col2:
                    st.markdown("🟡 **Moderate**")
                    st.markdown("0.5 ≤ V/C < 0.8")
                with legend_col3:
                    st.markdown("🟠 **High**")
                    st.markdown("0.8 ≤ V/C < 1.0")
                with legend_col4:
                    st.markdown("🔴 **Over Capacity**")
                    st.markdown("V/C ≥ 1.0")
            
        except Exception as e:
            logger.error(f"Error rendering main map area: {e}")
            st.error("Error displaying map")
    
    def _get_traffic_data_for_map(self) -> Optional[Dict]:
        """
        Always load traffic data for map display
        
        Returns:
            Traffic data dictionary or None if not available
        """
        try:
            # First check if traffic data is already in session state
            if st.session_state.get('traffic_data'):
                return st.session_state.traffic_data
            
            # If not in session state, try to load from saved JSON files
            traffic_data = self._load_traffic_data_from_files()
            if traffic_data:
                # Save to session state for future use
                st.session_state.traffic_data = traffic_data
                return traffic_data
            
            # If no saved data, fetch fresh traffic data
            with st.spinner("🚦 Loading traffic data..."):
                traffic_data = self.city_controller.fetch_traffic_data()
                if traffic_data:
                    # Save to session state and file
                    st.session_state.traffic_data = traffic_data
                    self.city_controller.save_traffic_data_to_json(traffic_data)
                    return traffic_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading traffic data for map: {e}")
            return None
    
    def _load_traffic_data_from_files(self) -> Optional[Dict]:
        """
        Load traffic data from saved JSON file (fixed filename)
        
        Returns:
            Traffic data dictionary or None if no file found
        """
        try:
            import os
            import json
            
            # Look for traffic data file in the data directory
            data_dir = "data"
            traffic_file = os.path.join(data_dir, "traffic_data.json")
            
            if not os.path.exists(traffic_file):
                return None
            
            # Load traffic data from fixed filename
            with open(traffic_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'traffic_data' in data:
                    logger.info(f"Loaded traffic data from {traffic_file}")
                    return data['traffic_data']
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading traffic data from files: {e}")
            return None
    
    def _render_map_settings(self) -> None:
        """
        Render simplified map settings with independent controls
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
                # Simple independent options
                show_city_labels = st.checkbox("🏷️ City Labels", value=True, key="show_city_labels")
                

                
        except Exception as e:
            logger.error(f"Error rendering map settings: {e}")
    
    def _render_mapbox_controls(self, valid_cities: CityCollection) -> tuple:
        """
        Render Mapbox map control options
        
        Args:
            valid_cities: Collection of valid cities
            
        Returns:
            Tuple of (selected_city, show_only_selected, map_style)
        """
        col1, col2, col3 = st.columns(3)
        
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
            # Reserved for future features
            st.info("Additional map layers coming soon!")
        
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
        
        return selected_city, show_only_selected, map_style
    
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
