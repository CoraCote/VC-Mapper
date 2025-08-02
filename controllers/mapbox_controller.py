"""
Mapbox Controller - Handles Mapbox map operations and data visualization
"""

from typing import List, Dict, Optional, Tuple, Any
import logging
import pydeck as pdk
import pandas as pd
from models.city_model import City, CityCollection, TrafficDataCollection
from utils.florida_boundary_service import florida_boundary_service

logger = logging.getLogger(__name__)


class MapboxController:
    """
    Controller for Mapbox-based map operations
    """
    
    def __init__(self, mapbox_token: str):
        """
        Initialize the Mapbox controller
        
        Args:
            mapbox_token: Mapbox API token
        """
        self.mapbox_token = mapbox_token
        # Set the mapbox token for pydeck (using environment variable method)
        import os
        os.environ['MAPBOX_API_KEY'] = mapbox_token
        
        # Default Florida center coordinates
        self.florida_center = {
            'lat': 27.8333,
            'lon': -81.717
        }
        
        # Cache for Florida boundary data
        self._florida_boundary_cache = None
    
    def create_base_deck(self, center_lat: float = 27.8333, center_lon: float = -81.717, 
                        zoom_level: int = 7, map_style: str = 'mapbox://styles/mapbox/streets-v11') -> pdk.Deck:
        """
        Create a base PyDeck map with Mapbox integration
        
        Args:
            center_lat: Latitude for map center
            center_lon: Longitude for map center
            zoom_level: Initial zoom level
            map_style: Mapbox map style
            
        Returns:
            PyDeck Deck object
        """
        try:
            # Create initial view state
            view_state = pdk.ViewState(
                latitude=center_lat,
                longitude=center_lon,
                zoom=zoom_level,
                pitch=0,
                bearing=0
            )
            
            # Create deck with basic configuration
            deck = pdk.Deck(
                map_style=map_style,
                initial_view_state=view_state,
                layers=[],  # Will be populated by other methods
                api_keys={"mapbox": self.mapbox_token},  # Pass token via api_keys
                tooltip={
                    "html": "<b>{name}</b>",
                    "style": {
                        "backgroundColor": "steelblue",
                        "color": "white",
                        "border": "1px solid white",
                        "borderRadius": "5px",
                        "padding": "10px"
                    }
                }
            )
            
            logger.info(f"Created base Mapbox deck centered at ({center_lat}, {center_lon}) with zoom {zoom_level}")
            return deck
            
        except Exception as e:
            logger.error(f"Error creating base Mapbox deck: {e}")
            raise
    
    def get_florida_boundary_layer(self) -> Optional[pdk.Layer]:
        """
        Create a layer for Florida state boundary using real API data
        
        Returns:
            PyDeck GeoJsonLayer for Florida boundary or None if error
        """
        try:
            # Fetch boundary data if not cached
            if self._florida_boundary_cache is None:
                logger.info("Fetching Florida boundary data from API...")
                self._florida_boundary_cache = florida_boundary_service.fetch_florida_boundary()
            
            if not self._florida_boundary_cache:
                logger.warning("Could not fetch Florida boundary data, using fallback")
                return self._get_fallback_florida_boundary_layer()
            
            # Validate the data
            if not florida_boundary_service.validate_boundary_data(self._florida_boundary_cache):
                logger.warning("Invalid boundary data, using fallback")
                return self._get_fallback_florida_boundary_layer()
            
            # Create the GeoJSON layer
            layer = pdk.Layer(
                "GeoJsonLayer",
                data=self._florida_boundary_cache,
                get_fill_color=[255, 0, 0, 50],  # Red with low opacity
                get_line_color=[255, 0, 0, 200],  # Red border
                get_line_width=3,
                filled=True,
                stroked=True,
                pickable=True,
                auto_highlight=True
            )
            
            logger.info("Created Florida boundary layer with real API data")
            return layer
            
        except Exception as e:
            logger.error(f"Error creating Florida boundary layer: {e}")
            return self._get_fallback_florida_boundary_layer()
    
    # def _get_fallback_florida_boundary_layer(self) -> pdk.Layer:
        """
        Create a fallback Florida boundary layer with static data
        
        Returns:
            PyDeck GeoJsonLayer with static Florida boundary
        """
        try:
            # Simplified Florida boundary as fallback
            fallback_boundary = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {"name": "Florida (Fallback)"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [-87.634896, 30.997536],
                            [-85.497137, 30.997536],
                            [-84.319447, 30.676609],
                            [-82.879938, 30.564875],
                            [-80.031983, 30.564875],
                            [-80.031983, 25.729595],
                            [-81.092673, 24.411089],
                            [-82.650513, 24.568745],
                            [-84.319447, 25.573047],
                            [-85.872803, 26.994637],
                            [-87.459717, 29.675867],
                            [-87.634896, 30.997536]
                        ]]
                    }
                }]
            }
            
            layer = pdk.Layer(
                "GeoJsonLayer",
                data=fallback_boundary,
                get_fill_color=[255, 100, 100, 50],
                get_line_color=[255, 100, 100, 200],
                get_line_width=2,
                filled=True,
                stroked=True,
                pickable=True
            )
            
            logger.info("Created fallback Florida boundary layer")
            return layer
            
        except Exception as e:
            logger.error(f"Error creating fallback boundary layer: {e}")
            return None
    
    def get_city_markers_layer(self, cities: CityCollection, 
                              selected_city: Optional[City] = None) -> Optional[pdk.Layer]:
        """
        Create a layer for city markers using custom city icon
        
        Args:
            cities: Collection of cities to display
            selected_city: Currently selected city for highlighting
            
        Returns:
            PyDeck IconLayer for city markers
        """
        try:
            valid_cities = cities.get_valid_cities()
            
            if not valid_cities:
                logger.warning("No valid cities to display")
                return None
            
            # Prepare data for the layer
            city_data = []
            for city in valid_cities:
                # Determine marker properties based on population
                color, size = self._get_city_marker_style(city, selected_city)
                
                city_data.append({
                    'latitude': city.latitude,
                    'longitude': city.longitude,
                    'name': city.name,
                    'population': city.population,
                    'color': color,
                    'size': size,
                    'geoid': city.geoid,
                    'full_name': city.full_name,
                    'icon': 'icon'  # Use the icon mapping defined in the layer
                })
            
            # Convert to DataFrame for pydeck
            df = pd.DataFrame(city_data)
            
            # Create icon layer with custom city icon
            layer = pdk.Layer(
                "IconLayer",
                data=df,
                get_position=['longitude', 'latitude'],
                get_icon='icon',
                get_size='size',
                size_scale=1,
                size_min_pixels=20,
                size_max_pixels=60,
                icon_atlas="https://cdn-icons-png.flaticon.com/512/684/684908.png",
                icon_mapping={
                    'icon': {
                        'x': 0,
                        'y': 0,
                        'width': 512,
                        'height': 512,
                        'anchorX': 256,
                        'anchorY': 256
                    }
                },
                pickable=True,
                auto_highlight=True,
                tooltip={
                    "html": """
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                color: white; padding: 15px; border-radius: 10px; font-family: Arial;">
                        <h3 style="margin: 0 0 10px 0;">🏙️ {name}</h3>
                        <p><strong>📍 Full Name:</strong> {full_name}</p>
                        <p><strong>🆔 GEOID:</strong> {geoid}</p>
                        <p><strong>👥 Population:</strong> {population:,}</p>
                    </div>
                    """,
                    "style": {"backgroundColor": "transparent", "border": "none"}
                }
            )
            
            logger.info(f"Created city markers layer with {len(valid_cities)} cities using custom icon")
            return layer
            
        except Exception as e:
            logger.error(f"Error creating city markers layer: {e}")
            return None
    
    def _get_city_marker_style(self, city: City, selected_city: Optional[City] = None) -> Tuple[List[int], int]:
        """
        Get marker style based on city properties
        
        Args:
            city: City object
            selected_city: Currently selected city
            
        Returns:
            Tuple of (color as RGBA list, size)
        """
        try:
            # Check if this is the selected city
            is_selected = selected_city and city.geoid == selected_city.geoid
            
            if is_selected:
                return [255, 107, 53, 255], 50  # Orange, larger size for selected city
            
            # Size based on population for icon layer
            population = city.population
            
            if population >= 100000:
                return [255, 68, 68, 200], 40  # Red for metropolis
            elif population >= 50000:
                return [255, 136, 0, 200], 35   # Orange for large city
            elif population >= 10000:
                return [68, 136, 255, 200], 30  # Blue for medium city
            else:
                return [68, 255, 68, 200], 25   # Green for small city
                
        except Exception as e:
            logger.error(f"Error getting city marker style: {e}")
            return [128, 128, 128, 200], 20  # Gray fallback
    

    
    def create_florida_map(self, cities: Optional[CityCollection] = None,
                          selected_city: Optional[City] = None,
                          show_only_selected: bool = False,
                          traffic_data: Optional[Dict] = None,
                          map_style: str = 'mapbox://styles/mapbox/streets-v11') -> pdk.Deck:
        """
        Create a complete Florida map with city and traffic layers
        
        Args:
            cities: Collection of cities to display
            selected_city: Currently selected city
            show_only_selected: Whether to show only selected city
            traffic_data: Traffic data to display as roadway segments
            map_style: Mapbox map style
            
        Returns:
            Complete PyDeck map
        """
        try:
            # Calculate appropriate center and zoom
            center_lat, center_lon, zoom_level = self._calculate_map_view(
                cities, selected_city, show_only_selected
            )
            
            # Create base deck
            deck = self.create_base_deck(center_lat, center_lon, zoom_level, map_style)
            
            # Build layers list
            layers = []
            
            # Add Florida boundary layer
            boundary_layer = self.get_florida_boundary_layer()
            if boundary_layer:
                layers.append(boundary_layer)
            
            # Add traffic roadway layer if provided
            if traffic_data:
                traffic_layer = self.get_traffic_roadway_layer(traffic_data)
                if traffic_layer:
                    layers.append(traffic_layer)
            
            # Add city markers if provided
            if cities:
                city_layer = self.get_city_markers_layer(cities, selected_city)
                if city_layer:
                    layers.append(city_layer)
            
            # Update deck with layers
            deck.layers = layers
            
            logger.info(f"Created complete Florida map with {len(layers)} layers")
            return deck
            
        except Exception as e:
            logger.error(f"Error creating Florida map: {e}")
            raise
    
    def _calculate_map_view(self, cities: Optional[CityCollection] = None,
                           selected_city: Optional[City] = None,
                           show_only_selected: bool = False) -> Tuple[float, float, int]:
        """
        Calculate appropriate map center and zoom level
        
        Args:
            cities: Collection of cities
            selected_city: Currently selected city
            show_only_selected: Whether showing only selected city
            
        Returns:
            Tuple of (center_lat, center_lon, zoom_level)
        """
        try:
            # If showing only selected city, center on it
            if selected_city and show_only_selected:
                if selected_city.has_valid_coordinates():
                    return selected_city.latitude, selected_city.longitude, 12
            
            # If we have a selected city, center on it but with wider view
            if selected_city and selected_city.has_valid_coordinates():
                # Check if this is an auto-scaled city from search
                import streamlit as st
                if st.session_state.get('auto_scaled_city', False):
                    # Use higher zoom for auto-scaled cities to really focus on the city area
                    return selected_city.latitude, selected_city.longitude, 13
                else:
                    # Regular zoom for manually selected cities
                    return selected_city.latitude, selected_city.longitude, 10
            
            # Otherwise, center on all valid cities
            if cities:
                valid_cities = cities.get_valid_cities()
                if valid_cities:
                    center_lat, center_lon = cities.get_center_coordinates()
                    return center_lat, center_lon, 7
            
            # Default to Florida center
            return self.florida_center['lat'], self.florida_center['lon'], 7
            
        except Exception as e:
            logger.error(f"Error calculating map view: {e}")
            return self.florida_center['lat'], self.florida_center['lon'], 7

    def get_traffic_roadway_layer(self, traffic_data: Dict) -> Optional[pdk.Layer]:
        """
        Create a layer for traffic roadway segments with V/C ratio color coding
        
        Args:
            traffic_data: GeoJSON traffic data from API
            
        Returns:
            PyDeck GeoJsonLayer for traffic roadways or None if error
        """
        try:
            if not traffic_data or 'features' not in traffic_data:
                logger.warning("No traffic data available for roadway layer")
                return None
            
            # Create traffic collection to process data
            traffic_collection = TrafficDataCollection(traffic_data)
            
            if len(traffic_collection) == 0:
                logger.warning("No traffic features found in data")
                return None
            
            # Calculate V/C ratios and prepare data for visualization
            roadway_data = []
            for traffic_record in traffic_collection:
                # Calculate V/C ratio (Volume/Capacity)
                # For this implementation, we'll use AADT as volume and estimate capacity
                # V/C ratio = AADT / Estimated Capacity
                aadt = traffic_record.aadt or 0
                
                # Estimate capacity based on typical roadway capacity
                # This is a simplified estimation - in practice, you'd have actual capacity data
                estimated_capacity = self._estimate_roadway_capacity(traffic_record)
                vc_ratio = aadt / estimated_capacity if estimated_capacity > 0 else 0
                
                # Get color based on V/C ratio
                color = self._get_vc_ratio_color(vc_ratio)
                
                # Prepare feature data
                if traffic_record.geometry:
                    roadway_data.append({
                        'geometry': traffic_record.geometry,
                        'properties': {
                            'name': f"Roadway {traffic_record.roadway}",  # Add explicit name for tooltip
                            'roadway': traffic_record.roadway,
                            'county': traffic_record.county,
                            'aadt': aadt,
                            'vc_ratio': vc_ratio,
                            'route': traffic_record.route,
                            'desc_from': traffic_record.desc_from,
                            'desc_to': traffic_record.desc_to,
                            'district': traffic_record.district,
                            'color': color
                        }
                    })
            
            if not roadway_data:
                logger.warning("No valid roadway geometries found")
                return None
            
            # Create GeoJSON for the layer
            roadway_geojson = {
                'type': 'FeatureCollection',
                'features': roadway_data
            }
            
            # Create the GeoJSON layer
            layer = pdk.Layer(
                "GeoJsonLayer",
                data=roadway_geojson,
                get_fill_color='properties.color',
                get_line_color='properties.color',
                get_line_width=50,
                filled=False,
                stroked=True,
                pickable=True,
                auto_highlight=True,
                tooltip={
                    "html": """
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                color: white; padding: 15px; border-radius: 10px; font-family: Arial;">
                        <h3 style="margin: 0 0 10px 0;">{name}</h3>
                        <p><strong>📍 County:</strong> {county}</p>
                        <p><strong>🛣️ Route:</strong> {route}</p>
                        <p><strong>📋 From:</strong> {desc_from}</p>
                        <p><strong>📋 To:</strong> {desc_to}</p>
                        <p><strong>🚗 AADT:</strong> {aadt:,}</p>
                        <p><strong>📊 V/C Ratio:</strong> {vc_ratio:.2f}</p>
                        <p><strong>🏢 District:</strong> {district}</p>
                    </div>
                    """,
                    "style": {"backgroundColor": "transparent", "border": "none"}
                }
            )
            
            logger.info(f"Created traffic roadway layer with {len(roadway_data)} segments")
            return layer
            
        except Exception as e:
            logger.error(f"Error creating traffic roadway layer: {e}")
            return None

    def _estimate_roadway_capacity(self, traffic_record) -> float:
        """
        Estimate roadway capacity based on traffic record properties
        
        Args:
            traffic_record: TrafficData object
            
        Returns:
            Estimated capacity (vehicles per day)
        """
        try:
            # Simplified capacity estimation based on typical roadway types
            # In a real implementation, you'd have actual capacity data
            
            # Default capacity for unknown roadways
            default_capacity = 20000  # vehicles per day
            
            # Estimate based on route description if available
            route = traffic_record.route or ""
            desc_to = traffic_record.desc_to or ""
            roadway = traffic_record.roadway or ""
            
            # Interstate highways
            if any(keyword in desc_to.upper() for keyword in ['I-', 'INTERSTATE', 'I95', 'I75', 'I4']):
                return 80000
            
            # US highways
            elif any(keyword in desc_to.upper() for keyword in ['US-', 'US ', 'US1', 'US27', 'US41']):
                return 40000
            
            # State roads
            elif any(keyword in desc_to.upper() for keyword in ['SR-', 'SR ', 'STATE', 'SR811', 'SR80']):
                return 30000
            
            # County roads
            elif any(keyword in desc_to.upper() for keyword in ['CR-', 'CR ', 'COUNTY']):
                return 15000
            
            # Local roads
            else:
                return 10000
                
        except Exception as e:
            logger.error(f"Error estimating roadway capacity: {e}")
            return 20000  # Default fallback

    def _get_vc_ratio_color(self, vc_ratio: float) -> List[int]:
        """
        Get color based on V/C ratio
        
        Args:
            vc_ratio: Volume/Capacity ratio
            
        Returns:
            RGBA color list
        """
        try:
            # Color coding based on V/C ratio:
            # Green: V/C < 0.5 (low congestion)
            # Yellow: 0.5 <= V/C < 0.8 (moderate congestion)
            # Orange: 0.8 <= V/C < 1.0 (high congestion)
            # Red: V/C >= 1.0 (over capacity)
            
            if vc_ratio < 0.5:
                return [0, 255, 0, 200]  # Green
            elif vc_ratio < 0.8:
                return [255, 255, 0, 200]  # Yellow
            elif vc_ratio < 1.0:
                return [255, 165, 0, 200]  # Orange
            else:
                return [255, 0, 0, 200]  # Red
                
        except Exception as e:
            logger.error(f"Error getting V/C ratio color: {e}")
            return [128, 128, 128, 200]  # Gray fallback
    


