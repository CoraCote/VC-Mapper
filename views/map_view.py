"""
Map View - UI components for map visualization
"""

from typing import Optional
import streamlit as st
from streamlit_folium import st_folium
import logging
from models.city_model import City, CityCollection
from models.street_model import StreetCollection
from controllers.map_controller import MapController
from controllers.city_controller import CityController

logger = logging.getLogger(__name__)


class MapView:
    """
    View component for map visualization
    """
    
    def __init__(self):
        """Initialize the map view"""
        self.map_controller = MapController()
        self.city_controller = CityController()
    
    def display_florida_only_map(self) -> None:
        """
        Display a map showing only the Florida state boundary
        """
        try:
            # Center on Florida
            center_lat, center_lon = 27.8333, -81.717
            zoom_level = 7
            
            # Create base map
            m = self.map_controller.create_base_map(center_lat, center_lon, zoom_level)
            
            # Add Florida state boundary
            self.map_controller.add_florida_boundary(m)
            
            # Add layer control
            self.map_controller.add_layer_control(m)
            
            # Display the map
            with st.container():
                st.markdown('<div class="map-container">', unsafe_allow_html=True)
                st.info("📍 Press the 'FETCH CITY' button from the sidebar to load city data and explore specific locations.")
                st_folium(m, width=None, height=600)
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            logger.error(f"Error displaying Florida only map: {e}")
            st.error("❌ Error loading map. Please try refreshing the page.")
    
    def display_cities_on_map(self, cities: CityCollection) -> None:
        """
        Display cities on an enhanced interactive map with options
        
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
            
            # Map configuration options
            selected_city, show_only_selected, show_streets = self._render_map_controls(valid_cities)
            
            # Create and display the map
            m = self._create_enhanced_map(
                valid_cities, 
                selected_city,
                show_only_selected,
                show_streets
            )
            
            if m is None:
                st.error("🚫 Unable to create map")
                return
            
            # Display map with statistics
            self._display_map_with_stats(m, valid_cities, selected_city)
            
        except Exception as e:
            logger.error(f"Error displaying cities on map: {e}")
            st.error("❌ Error displaying map. Please try refreshing the page.")
    
    def _render_map_controls(self, valid_cities: CityCollection) -> tuple:
        """
        Render map control options
        
        Args:
            valid_cities: Collection of valid cities
            
        Returns:
            Tuple of (selected_city, show_only_selected, show_streets)
        """
        col1, col2 = st.columns(2)
        
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
        
        return selected_city, show_only_selected, show_streets
    
    def _create_enhanced_map(self, cities: CityCollection, selected_city: Optional[City],
                           show_only_selected: bool, show_streets: bool):
        """
        Create enhanced map with cities and optional features
        
        Args:
            cities: Collection of cities
            selected_city: Currently selected city
            show_only_selected: Whether to show only selected city
            show_streets: Whether to show streets
            
        Returns:
            Folium map object
        """
        try:
            # Determine which cities to show
            if show_only_selected and selected_city:
                cities_to_show = CityCollection([selected_city.to_dict()])
            else:
                cities_to_show = cities
            
            # Calculate center and zoom
            center_lat, center_lon, zoom_level = self.map_controller.calculate_map_center_and_zoom(
                cities_to_show, selected_city, show_only_selected
            )
            
            # Create base map
            m = self.map_controller.create_base_map(center_lat, center_lon, zoom_level)
            
            # Add city markers
            self.map_controller.add_city_markers(m, cities_to_show, selected_city)
            
            # Add population legend
            self.map_controller.add_population_legend(m)
            
            # Add city boundaries
            show_boundaries = True
            if show_boundaries:
                boundary_func = self.city_controller.get_city_boundary
                self.map_controller.add_city_boundaries(m, cities_to_show, selected_city, boundary_func)
            
            # Add streets if requested and a city is selected
            if show_streets and selected_city:
                with st.spinner(f"Loading streets for {selected_city.name}..."):
                    from controllers.street_controller import StreetController
                    street_controller = StreetController()
                    streets = street_controller.get_streets_for_city(selected_city)
                    
                    if streets.streets:
                        self.map_controller.add_streets_to_map(m, streets, show_traffic=False, city_selected=True)
                        logger.info(f"Added {len(streets)} streets for {selected_city.name}")
                    else:
                        st.warning(f"⚠️ No street data available for {selected_city.name}")
            
            # Add layer control
            self.map_controller.add_layer_control(m)
            
            return m
            
        except Exception as e:
            logger.error(f"Error creating enhanced map: {e}")
            return None
    
    def _display_map_with_stats(self, m, valid_cities: CityCollection, selected_city: Optional[City]) -> None:
        """
        Display map with statistics and interaction
        
        Args:
            m: Folium map object
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
                
                # Display the map
                map_data = st_folium(m, width=None, height=600, returned_objects=["last_clicked"])
                
                # Show selected city details
                if selected_city:
                    self._display_selected_city_details(selected_city)
                
                # Show clicked city details for additional interaction
                self._handle_map_click(map_data, valid_cities)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            logger.error(f"Error displaying map with stats: {e}")
    
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
    
    def _handle_map_click(self, map_data: dict, cities: CityCollection) -> None:
        """Handle map click interactions"""
        if map_data.get('last_clicked'):
            try:
                clicked_lat = map_data['last_clicked']['lat']
                clicked_lng = map_data['last_clicked']['lng']
                
                # Find the closest city to the clicked point
                closest_city = cities.find_closest_city(clicked_lat, clicked_lng)
                
                if closest_city:
                    st.success(f"📍 Clicked: **{closest_city.name}** - Population: {closest_city.population:,}")
            except Exception as e:
                st.info("📍 Click on a city marker to see details")
                logger.error(f"Error handling map click: {e}")
    
    def create_simple_map(self, center_lat: float, center_lon: float, zoom: int = 10):
        """
        Create a simple map for basic display
        
        Args:
            center_lat: Latitude for map center
            center_lon: Longitude for map center
            zoom: Zoom level
            
        Returns:
            Folium map object
        """
        try:
            return self.map_controller.create_base_map(center_lat, center_lon, zoom)
        except Exception as e:
            logger.error(f"Error creating simple map: {e}")
            return None