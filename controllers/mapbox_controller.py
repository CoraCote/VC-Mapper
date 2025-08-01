"""
Mapbox Controller - Handles Mapbox map operations and data visualization
"""

from typing import List, Dict, Optional, Tuple, Any
import logging
import pydeck as pdk
import pandas as pd
from models.city_model import City, CityCollection
from models.street_model import Street, StreetCollection
from models.traffic_model import TrafficData, TrafficCollection
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
    
    def _get_fallback_florida_boundary_layer(self) -> pdk.Layer:
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
        Create a layer for city markers
        
        Args:
            cities: Collection of cities to display
            selected_city: Currently selected city for highlighting
            
        Returns:
            PyDeck ScatterplotLayer for city markers
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
                    'full_name': city.full_name
                })
            
            # Convert to DataFrame for pydeck
            df = pd.DataFrame(city_data)
            
            # Create scatterplot layer
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position=['longitude', 'latitude'],
                get_color='color',
                get_radius='size',
                radius_scale=1000,
                radius_min_pixels=5,
                radius_max_pixels=50,
                pickable=True,
                auto_highlight=True,
                tooltip={
                    "html": """
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                color: white; padding: 15px; border-radius: 10px; font-family: Arial;">
                        <h3 style="margin: 0 0 10px 0;">{name}</h3>
                        <p><strong>📍 Full Name:</strong> {full_name}</p>
                        <p><strong>🆔 GEOID:</strong> {geoid}</p>
                        <p><strong>👥 Population:</strong> {population:,}</p>
                    </div>
                    """,
                    "style": {"backgroundColor": "transparent", "border": "none"}
                }
            )
            
            logger.info(f"Created city markers layer with {len(valid_cities)} cities")
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
                return [255, 107, 53, 255], 25  # Orange, larger size
            
            # Color based on population
            population = city.population
            
            if population >= 100000:
                return [255, 68, 68, 200], 20  # Red for metropolis
            elif population >= 50000:
                return [255, 136, 0, 200], 18   # Orange for large city
            elif population >= 10000:
                return [68, 136, 255, 200], 15  # Blue for medium city
            else:
                return [68, 255, 68, 200], 12   # Green for small city
                
        except Exception as e:
            logger.error(f"Error getting city marker style: {e}")
            return [128, 128, 128, 200], 10  # Gray fallback
    
    def get_streets_layer(self, streets: StreetCollection, 
                         show_traffic: bool = True, 
                         city_selected: bool = False) -> Optional[pdk.Layer]:
        """
        Create a layer for street data
        
        Args:
            streets: Collection of streets to display
            show_traffic: Whether to show traffic-based coloring
            city_selected: Whether this is for a selected city
            
        Returns:
            PyDeck PathLayer for streets
        """
        try:
            valid_streets = streets.get_valid_streets()
            
            if not valid_streets:
                logger.warning("No valid streets to display")
                return None
            
            # Prepare street data
            street_data = []
            for street in valid_streets:
                coords = street.get_coordinates()
                if not coords:
                    continue
                
                # Get color based on traffic or selection
                if city_selected:
                    color = [0, 116, 217, 200]  # Blue for selected city
                    width = 3
                elif show_traffic:
                    color = self._get_traffic_color_rgba(street.traffic_level)
                    width = 4
                else:
                    color = [0, 116, 217, 150]  # Default blue
                    width = 2
                
                # Convert coordinates to the format expected by PathLayer
                path_coords = []
                if isinstance(coords[0][0], list):  # MultiLineString
                    for line in coords:
                        path_coords.extend([[coord[1], coord[0]] for coord in line])
                else:  # LineString
                    path_coords = [[coord[1], coord[0]] for coord in coords]  # Swap to [lat, lon]
                
                street_data.append({
                    'path': path_coords,
                    'name': street.street_name,
                    'traffic_level': street.get_traffic_level_display(),
                    'color': color,
                    'width': width
                })
            
            # Convert to DataFrame
            df = pd.DataFrame(street_data)
            
            # Create path layer
            layer = pdk.Layer(
                "PathLayer",
                data=df,
                get_path='path',
                get_color='color',
                get_width='width',
                width_scale=1,
                width_min_pixels=1,
                pickable=True,
                auto_highlight=True
            )
            
            logger.info(f"Created streets layer with {len(valid_streets)} streets")
            return layer
            
        except Exception as e:
            logger.error(f"Error creating streets layer: {e}")
            return None
    
    def _get_traffic_color_rgba(self, traffic_level: str) -> List[int]:
        """
        Get RGBA color for traffic level
        
        Args:
            traffic_level: Traffic level string
            
        Returns:
            RGBA color as list [r, g, b, a]
        """
        traffic_colors = {
            'very_high': [255, 0, 0, 200],    # Red
            'high': [255, 102, 0, 200],       # Orange
            'medium': [255, 255, 0, 200],     # Yellow
            'low': [102, 255, 0, 200],        # Light Green
            'very_low': [0, 255, 0, 200],     # Green
            'unknown': [128, 128, 128, 200]   # Gray
        }
        
        return traffic_colors.get(traffic_level, [128, 128, 128, 200])
    
    def create_florida_map(self, cities: Optional[CityCollection] = None,
                          selected_city: Optional[City] = None,
                          streets: Optional[StreetCollection] = None,
                          traffic_data: Optional[TrafficCollection] = None,
                          show_traffic: bool = True,
                          show_traffic_heatmap: bool = False,
                          traffic_filter_level: Optional[str] = None,
                          show_only_selected: bool = False,
                          map_style: str = 'mapbox://styles/mapbox/streets-v11') -> pdk.Deck:
        """
        Create a complete Florida map with all layers
        
        Args:
            cities: Collection of cities to display
            selected_city: Currently selected city
            streets: Collection of streets to display
            traffic_data: Collection of real-time traffic data to display
            show_traffic: Whether to show traffic coloring
            show_traffic_heatmap: Whether to show traffic volume heatmap
            traffic_filter_level: Optional traffic level filter
            show_only_selected: Whether to show only selected city
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
            
            # Add city markers if provided
            if cities:
                city_layer = self.get_city_markers_layer(cities, selected_city)
                if city_layer:
                    layers.append(city_layer)
            
            # Add streets if provided
            if streets:
                streets_layer = self.get_streets_layer(
                    streets, show_traffic, selected_city is not None
                )
                if streets_layer:
                    layers.append(streets_layer)
            
            # Add traffic data layers if provided
            if traffic_data and show_traffic:
                # Add traffic volume heatmap first (background layer)
                if show_traffic_heatmap:
                    heatmap_layer = self.get_traffic_volume_heatmap_layer(traffic_data)
                    if heatmap_layer:
                        layers.append(heatmap_layer)
                
                # Add traffic path layer
                traffic_layer = self.get_traffic_layer(
                    traffic_data, 
                    show_volume=True, 
                    show_speed=True,
                    filter_level=traffic_filter_level
                )
                if traffic_layer:
                    layers.append(traffic_layer)
            
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
    
    def get_traffic_layer(self, traffic_collection: TrafficCollection,
                         show_volume: bool = True,
                         show_speed: bool = True,
                         filter_level: Optional[str] = None) -> Optional[pdk.Layer]:
        """
        Create a layer for real-time traffic data visualization
        
        Args:
            traffic_collection: Collection of traffic data to display
            show_volume: Whether to show volume-based visualization
            show_speed: Whether to show speed-based visualization
            filter_level: Optional traffic level filter (Low, Moderate, High, Heavy)
            
        Returns:
            PyDeck PathLayer for traffic data
        """
        try:
            if not traffic_collection or len(traffic_collection) == 0:
                logger.warning("No traffic data to display")
                return None
            
            # Filter traffic data if level filter is specified
            traffic_data = traffic_collection.traffic_data
            if filter_level and filter_level != 'All':
                traffic_data = [data for data in traffic_data 
                              if data.get_traffic_level() == filter_level]
            
            if not traffic_data:
                logger.warning(f"No traffic data matching filter: {filter_level}")
                return None
            
            # Prepare traffic visualization data
            traffic_viz_data = []
            for traffic in traffic_data:
                if not traffic.coordinates or len(traffic.coordinates) < 2:
                    continue
                
                # Convert coordinates to [lat, lon] format for PyDeck
                path_coords = [[coord[1], coord[0]] for coord in traffic.coordinates]
                
                # Get visualization properties based on V/C ratio for better traffic analysis
                color = traffic.get_color_by_vc_ratio()
                width = traffic.get_line_width_by_vc_ratio() if show_volume else 3
                vc_ratio = traffic.calculate_vc_ratio()
                vc_level = traffic.get_vc_ratio_level()
                
                # Create data point for visualization with enhanced AADT and V/C ratio information
                traffic_viz_data.append({
                    'path': path_coords,
                    'roadway_name': traffic.roadway_name,
                    'traffic_volume': traffic.aadt,  # Use AADT value
                    'aadt': traffic.aadt,
                    'vc_ratio': vc_ratio,
                    'vc_level': vc_level,
                    'average_speed': traffic.average_speed,
                    'speed_limit': traffic.speed_limit,
                    'speed_ratio': traffic.speed_ratio,
                    'traffic_level': traffic.get_traffic_level(),
                    'direction': traffic.direction,
                    'county': traffic.county,
                    'color': color,
                    'width': width,
                    'volume_category': traffic.volume_category,
                    'data_timestamp': str(traffic.year),  # Show year instead of timestamp
                    'data_quality': traffic.data_quality,
                    'confidence_level': traffic.confidence_level,
                    'year': traffic.year,
                    'district': traffic.district,
                    'desc_from': traffic.desc_from,
                    'desc_to': traffic.desc_to
                })
            
            if not traffic_viz_data:
                logger.warning("No valid traffic paths to display")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(traffic_viz_data)
            
            # Create enhanced tooltip for AADT data with V/C ratio information
            tooltip_html = """
            <b>🛣️ {roadway_name}</b><br/>
            <b>📊 Level of Service:</b> {vc_level}<br/>
            <b>⚖️ V/C Ratio:</b> {vc_ratio:.2f}<br/>
            <b>🚗 AADT:</b> {traffic_volume:,} vehicles/day<br/>
            <b>📈 Volume Category:</b> {volume_category}<br/>
            <b>📍 County:</b> {county}<br/>
            <b>📅 Year:</b> {data_timestamp}<br/>
            <b>ℹ️ Data Quality:</b> {data_quality}
            """
            
            # Create path layer with enhanced styling
            layer = pdk.Layer(
                "PathLayer",
                data=df,
                get_path='path',
                get_color='color',
                get_width='width',
                width_scale=1,
                width_min_pixels=2,
                width_max_pixels=12,
                pickable=True,
                auto_highlight=True,
                highlight_color=[255, 255, 255, 80]
            )
            
            logger.info(f"Created traffic layer with {len(traffic_viz_data)} traffic segments")
            return layer
            
        except Exception as e:
            logger.error(f"Error creating traffic layer: {e}")
            return None
    
    def get_traffic_volume_heatmap_layer(self, traffic_collection: TrafficCollection) -> Optional[pdk.Layer]:
        """
        Create a heatmap layer for traffic volume visualization
        
        Args:
            traffic_collection: Collection of traffic data
            
        Returns:
            PyDeck HeatmapLayer for traffic volume
        """
        try:
            if not traffic_collection or len(traffic_collection) == 0:
                logger.warning("No traffic data for heatmap")
                return None
            
            # Prepare heatmap data using midpoints of traffic segments
            heatmap_data = []
            for traffic in traffic_collection.traffic_data:
                midpoint = traffic.get_midpoint()
                if midpoint and traffic.traffic_volume > 0:
                    heatmap_data.append({
                        'position': [midpoint[1], midpoint[0]],  # [lat, lon]
                        'weight': traffic.traffic_volume / 1000,  # Scale down for better visualization
                        'roadway_name': traffic.roadway_name,
                        'traffic_volume': traffic.traffic_volume
                    })
            
            if not heatmap_data:
                logger.warning("No valid traffic volume data for heatmap")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(heatmap_data)
            
            # Create heatmap layer
            layer = pdk.Layer(
                "HeatmapLayer",
                data=df,
                get_position='position',
                get_weight='weight',
                radius_pixels=100,
                intensity=1,
                threshold=0.05,
                pickable=False
            )
            
            logger.info(f"Created traffic volume heatmap with {len(heatmap_data)} points")
            return layer
            
        except Exception as e:
            logger.error(f"Error creating traffic heatmap layer: {e}")
            return None