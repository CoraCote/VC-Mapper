"""
Map Controller - Handles map-related operations and data
"""

from typing import List, Dict, Optional, Tuple
import logging
import folium
from models.city_model import City, CityCollection
from models.street_model import Street, StreetCollection

logger = logging.getLogger(__name__)


class MapController:
    """
    Controller for map-related operations
    """
    
    def __init__(self):
        """Initialize the map controller"""
        # Florida state boundary GeoJSON (simplified coordinates)
        self.florida_boundary = {
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
    
    def create_base_map(self, center_lat: float = 27.8333, center_lon: float = -81.717, 
                       zoom_level: int = 7) -> folium.Map:
        """
        Create a base Folium map with multiple tile layers
        
        Args:
            center_lat: Latitude for map center
            center_lon: Longitude for map center
            zoom_level: Initial zoom level
            
        Returns:
            Folium map object
        """
        try:
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
            folium.TileLayer(
                tiles='CartoDB dark_matter', 
                name='Dark Mode',
                attr='CartoDB'
            ).add_to(m)
            
            logger.info(f"Created base map centered at ({center_lat}, {center_lon}) with zoom {zoom_level}")
            return m
            
        except Exception as e:
            logger.error(f"Error creating base map: {e}")
            # Return a simple map if the enhanced version fails
            return folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level)
    
    def add_florida_boundary(self, m: folium.Map) -> None:
        """
        Add Florida state boundary to the map
        
        Args:
            m: Folium map object
        """
        try:
            folium.GeoJson(
                self.florida_boundary,
                style_function=lambda feature: {
                    'fillColor': 'transparent',
                    'color': '#ff0000',
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
    
    def add_city_markers(self, m: folium.Map, cities: CityCollection, 
                        selected_city: Optional[City] = None) -> None:
        """
        Add city markers to the map
        
        Args:
            m: Folium map object
            cities: Collection of cities to add
            selected_city: Currently selected city for highlighting
        """
        try:
            valid_cities = cities.get_valid_cities()
            
            for city in valid_cities:
                population = city.population
                marker_style = city.get_marker_style()
                
                # Enhanced popup with better styling
                popup_html = f"""
                <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; width: 280px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; padding: 15px; margin: -10px;">
                    <h3 style="margin: 0 0 10px 0; text-align: center; font-size: 18px;">{city.name}</h3>
                    <div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin: 10px 0;">
                        <p style="margin: 3px 0;"><strong>📍 Full Name:</strong> {city.full_name}</p>
                        <p style="margin: 3px 0;"><strong>🆔 GEOID:</strong> {city.geoid}</p>
                        <p style="margin: 3px 0;"><strong>👥 Population:</strong> {population:,}</p>
                        <p style="margin: 3px 0;"><strong>🏞️ Land Area:</strong> {city.land_area:,.0f} sq m</p>
                        <p style="margin: 3px 0;"><strong>🌊 Water Area:</strong> {city.water_area:,.0f} sq m</p>
                        <p style="margin: 3px 0;"><strong>📊 Coordinates:</strong> {city.latitude:.4f}, {city.longitude:.4f}</p>
                    </div>
                </div>
                """
                
                # Add enhanced marker
                folium.Marker(
                    location=[city.latitude, city.longitude],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"<b>{city.name}</b><br/>Population: {population:,}",
                    icon=folium.Icon(color=marker_style['color'], icon=marker_style['icon'], prefix='glyphicon')
                ).add_to(m)
                
                # Add circle marker for better visibility
                folium.CircleMarker(
                    location=[city.latitude, city.longitude],
                    radius=marker_style['size'],
                    popup=folium.Popup(popup_html, max_width=300),
                    color='white',
                    weight=2,
                    fillColor=marker_style['color'],
                    fillOpacity=0.7
                ).add_to(m)
            
            logger.info(f"Added {len(valid_cities)} city markers to map")
            
        except Exception as e:
            logger.error(f"Error adding city markers to map: {e}")
    
    def add_city_boundaries(self, m: folium.Map, cities: CityCollection, 
                           selected_city: Optional[City] = None, 
                           boundary_data_func=None) -> None:
        """
        Add city boundaries to the map
        
        Args:
            m: Folium map object
            cities: Collection of cities
            selected_city: Currently selected city for highlighting
            boundary_data_func: Function to get boundary data for a city
        """
        try:
            if not boundary_data_func:
                logger.warning("No boundary data function provided")
                return
            
            valid_cities = cities.get_valid_cities()
            
            for city in valid_cities:
                is_selected_city = selected_city and city.geoid == selected_city.geoid
                
                try:
                    boundary_data = boundary_data_func(city.geoid)
                    if boundary_data:
                        self._add_city_boundary_to_map(m, city, boundary_data, is_selected_city)
                except Exception as e:
                    logger.error(f"Error adding boundary for city {city.name}: {e}")
            
            logger.info(f"Added boundaries for cities")
            
        except Exception as e:
            logger.error(f"Error adding city boundaries: {e}")
    
    def _add_city_boundary_to_map(self, m: folium.Map, city: City, 
                                 boundary_data: Dict, is_selected: bool = False) -> None:
        """
        Add a single city boundary to the map
        
        Args:
            m: Folium map object
            city: City object
            boundary_data: Boundary geometry data
            is_selected: Whether this is the selected city
        """
        try:
            geometry = boundary_data.get('geometry', {})
            if not geometry:
                logger.warning(f"No geometry data for city {city.name}")
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
                            {'🎯 ' if is_selected else '🏢 '}{city.name}
                        </h4>
                        <p style="margin: 2px 0;"><strong>Status:</strong> {'Selected City' if is_selected else 'City Boundary'}</p>
                        <p style="margin: 2px 0;"><strong>Population:</strong> {city.population:,}</p>
                        <p style="margin: 2px 0;"><strong>GEOID:</strong> {city.geoid}</p>
                    </div>
                    """
                    
                    # Add polygon to map
                    polygon = folium.Polygon(
                        locations=folium_coords,
                        popup=folium.Popup(popup_content, max_width=250),
                        tooltip=f"{'🎯 Selected: ' if is_selected else '🏢 '}{city.name}",
                        color=color,
                        weight=weight,
                        fillColor=fillColor,
                        fillOpacity=fillOpacity,
                        dashArray=dash_array
                    )
                    polygon.add_to(m)
                    
                    logger.info(f"Added {'highlighted' if is_selected else 'regular'} boundary for city {city.name}")
            
        except Exception as e:
            logger.error(f"Error adding city boundary to map: {e}")
    
    def add_streets_to_map(self, m: folium.Map, streets: StreetCollection, 
                          show_traffic: bool = True, city_selected: bool = False) -> None:
        """
        Add street data to the map
        
        Args:
            m: Folium map object
            streets: Collection of streets to add
            show_traffic: Whether to show traffic-based coloring
            city_selected: Whether this is for a selected city (use blue highlighting)
        """
        try:
            valid_streets = streets.get_valid_streets()
            if not valid_streets:
                return
            
            if city_selected:
                # For selected city, highlight streets in blue
                street_group = folium.FeatureGroup(name='🔵 City Streets').add_to(m)
                
                for street in valid_streets:
                    coords = street.get_folium_coordinates()
                    if coords:
                        # Create blue polyline for city streets
                        line = folium.PolyLine(
                            locations=coords,
                            popup=folium.Popup(street.create_popup_html(), max_width=300),
                            tooltip=f"{street.street_name} - {street.get_traffic_level_display()}",
                            color='#0074D9',  # Blue color for city streets
                            weight=3,
                            opacity=0.8
                        )
                        line.add_to(street_group)
                
                logger.info(f"Added {len(valid_streets)} city streets highlighted in blue")
            
            else:
                # Original traffic-based coloring
                self._add_traffic_based_streets(m, valid_streets, show_traffic)
            
        except Exception as e:
            logger.error(f"Error adding streets to map: {e}")
    
    def _add_traffic_based_streets(self, m: folium.Map, streets: List[Street], 
                                  show_traffic: bool) -> None:
        """
        Add streets with traffic-based coloring
        
        Args:
            m: Folium map object
            streets: List of valid streets
            show_traffic: Whether to show traffic colors
        """
        try:
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
                traffic_level = street.traffic_level
                traffic_color = street.get_traffic_color() if show_traffic else '#0074D9'
                coords = street.get_folium_coordinates()
                
                if coords:
                    if isinstance(coords[0][0], list):  # MultiLineString
                        for line_coords in coords:
                            line = folium.PolyLine(
                                locations=line_coords,
                                popup=folium.Popup(street.create_popup_html(), max_width=300),
                                tooltip=f"{street.street_name} - {street.get_traffic_level_display()} Traffic",
                                color=traffic_color,
                                weight=4 if show_traffic else 2,
                                opacity=0.8
                            )
                            line.add_to(traffic_groups[traffic_level])
                    else:  # LineString
                        line = folium.PolyLine(
                            locations=coords,
                            popup=folium.Popup(street.create_popup_html(), max_width=300),
                            tooltip=f"{street.street_name} - {street.get_traffic_level_display()} Traffic",
                            color=traffic_color,
                            weight=4 if show_traffic else 2,
                            opacity=0.8
                        )
                        line.add_to(traffic_groups[traffic_level])
            
            # Add traffic legend
            if show_traffic:
                self._add_traffic_legend(m)
            
            logger.info(f"Added {len(streets)} streets to map with traffic visualization")
            
        except Exception as e:
            logger.error(f"Error adding traffic-based streets: {e}")
    
    def _add_traffic_legend(self, m: folium.Map) -> None:
        """Add traffic legend to the map"""
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
    
    def add_population_legend(self, m: folium.Map) -> None:
        """Add population legend to the map"""
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
    
    def add_layer_control(self, m: folium.Map) -> None:
        """Add layer control to the map"""
        folium.LayerControl().add_to(m)
    
    def calculate_map_center_and_zoom(self, cities: CityCollection, 
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
            valid_cities = cities.get_valid_cities()
            if valid_cities:
                center_lat, center_lon = cities.get_center_coordinates()
                return center_lat, center_lon, 7
            
            # Default to Florida center
            return 27.8333, -81.717, 7
            
        except Exception as e:
            logger.error(f"Error calculating map center and zoom: {e}")
            return 27.8333, -81.717, 7