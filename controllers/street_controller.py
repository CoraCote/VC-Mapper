"""
Street Controller - Handles street data operations and business logic
"""

from typing import List, Dict, Optional
import logging
import requests
import streamlit as st
from models.street_model import Street, StreetCollection
from models.city_model import City

logger = logging.getLogger(__name__)


class StreetController:
    """
    Controller for street-related operations
    """
    
    def __init__(self):
        """Initialize the street controller"""
        self.street_collection = StreetCollection()
    
    def get_overpass_streets(self, bbox: List[float], city_name: str = "") -> StreetCollection:
        """
        Get street data from OpenStreetMap Overpass API within a bounding box
        
        Args:
            bbox: [south, west, north, east] bounding box coordinates
            city_name: Name of the city for filtering (optional)
        
        Returns:
            StreetCollection with retrieved streets
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
            streets_data = []
            
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
                    streets_data.append(street_data)
            
            street_collection = StreetCollection(streets_data)
            logger.info(f"Retrieved {len(street_collection)} streets from OpenStreetMap for {city_name or 'specified area'}")
            return street_collection
            
        except Exception as e:
            logger.error(f"Error fetching streets from OpenStreetMap: {e}")
            return StreetCollection()
    
    def get_alternative_street_data(self, lat: float, lon: float, city_name: str = "") -> StreetCollection:
        """
        Try multiple methods to get street data for a city
        
        Args:
            lat: Latitude of the city center
            lon: Longitude of the city center  
            city_name: Name of the city
        
        Returns:
            StreetCollection with retrieved streets
        """
        # Method 1: OpenStreetMap Overpass API with smaller bounding box
        try:
            bbox_size = 0.02  # Start with smaller area
            bbox = [lat - bbox_size, lon - bbox_size, lat + bbox_size, lon + bbox_size]
            streets = self.get_overpass_streets(bbox, city_name)
            
            if streets.streets:
                logger.info(f"Retrieved {len(streets)} streets using OpenStreetMap Overpass API")
                return streets
        except Exception as e:
            logger.error(f"OpenStreetMap method failed: {e}")
        
        # Method 2: Try larger bounding box
        try:
            bbox_size = 0.05  # Larger area
            bbox = [lat - bbox_size, lon - bbox_size, lat + bbox_size, lon + bbox_size]
            streets = self.get_overpass_streets(bbox, city_name)
            
            if streets.streets:
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
                    streets_data = []
                    
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
                            streets_data.append(street_data)
                    
                    if streets_data:
                        street_collection = StreetCollection(streets_data)
                        logger.info(f"Retrieved {len(street_collection)} streets using alternative Overpass server: {overpass_url}")
                        return street_collection
                        
                except Exception as server_error:
                    logger.warning(f"Failed with server {overpass_url}: {server_error}")
                    continue
                    
        except Exception as e:
            logger.error(f"Alternative servers method failed: {e}")
        
        logger.warning(f"Could not retrieve street data for {city_name} using any method")
        return StreetCollection()
    
    def get_streets_for_city(self, city: City) -> StreetCollection:
        """
        Get street data for a specific city
        
        Args:
            city: City object to get streets for
            
        Returns:
            StreetCollection with city streets
        """
        if not city.has_valid_coordinates():
            logger.warning(f"City {city.name} does not have valid coordinates")
            return StreetCollection()
        
        return self.get_alternative_street_data(
            city.latitude, 
            city.longitude, 
            city.name
        )
    
    def filter_streets(self, streets: StreetCollection, filters: Dict) -> StreetCollection:
        """
        Apply filters to street collection
        
        Args:
            streets: Street collection to filter
            filters: Dictionary of filter criteria
            
        Returns:
            Filtered street collection
        """
        try:
            filtered_streets = streets.streets.copy()
            
            # Apply name filter
            if 'search_term' in filters and filters['search_term']:
                filtered_streets = [street for street in filtered_streets 
                                  if filters['search_term'].lower() in street.street_name.lower()]
            
            # Apply traffic level filter
            if 'traffic_level' in filters and filters['traffic_level'] != "All":
                filtered_streets = [street for street in filtered_streets 
                                  if street.get_traffic_level_display() == filters['traffic_level']]
            
            # Create new collection with filtered streets
            filtered_collection = StreetCollection()
            filtered_collection.streets = filtered_streets
            
            logger.info(f"Filtered {len(streets)} streets to {len(filtered_collection)} streets")
            return filtered_collection
            
        except Exception as e:
            logger.error(f"Error filtering streets: {e}")
            return streets
    
    def sort_streets(self, streets: StreetCollection, sort_by: str) -> StreetCollection:
        """
        Sort streets by specified criteria
        
        Args:
            streets: Street collection to sort
            sort_by: Field to sort by
            
        Returns:
            Sorted street collection
        """
        try:
            # Determine if we should sort in reverse order
            reverse = sort_by in ["Traffic Volume", "Length", "Speed Limit"]
            sorted_streets = streets.sort_streets(sort_by, reverse)
            
            sorted_collection = StreetCollection()
            sorted_collection.streets = sorted_streets
            
            logger.info(f"Sorted {len(streets)} streets by {sort_by}")
            return sorted_collection
            
        except Exception as e:
            logger.error(f"Error sorting streets: {e}")
            return streets
    
    def get_session_streets(self) -> Optional[StreetCollection]:
        """
        Get streets from session state
        
        Returns:
            StreetCollection from session state or None
        """
        if 'current_streets' in st.session_state and st.session_state.current_streets:
            return StreetCollection(st.session_state.current_streets)
        return None
    
    def save_to_session(self, streets: StreetCollection):
        """
        Save streets to session state
        
        Args:
            streets: Street collection to save
        """
        st.session_state.current_streets = streets.get_streets_as_dict_list()
        logger.info(f"Saved {len(streets)} streets to session state")
    
    def get_street_statistics(self, streets: StreetCollection) -> Dict:
        """
        Calculate statistics for street collection
        
        Args:
            streets: Street collection to analyze
            
        Returns:
            Dictionary of statistics
        """
        try:
            if not streets.streets:
                return {
                    'total_streets': 0,
                    'total_traffic_volume': 0,
                    'average_traffic_volume': 0,
                    'total_length': 0,
                    'traffic_distribution': {}
                }
            
            return {
                'total_streets': len(streets),
                'total_traffic_volume': streets.get_total_traffic_volume(),
                'average_traffic_volume': streets.get_average_traffic_volume(),
                'total_length': streets.get_total_length(),
                'traffic_distribution': streets.get_traffic_distribution()
            }
            
        except Exception as e:
            logger.error(f"Error calculating street statistics: {e}")
            return {}
    
    def load_streets_for_selected_city(self) -> Optional[StreetCollection]:
        """
        Load street data for the currently selected city
        
        Returns:
            StreetCollection if successful, None otherwise
        """
        try:
            # Check if there's a selected city in session state
            if 'selected_city' not in st.session_state or not st.session_state.selected_city:
                return None
            
            from models.city_model import City
            selected_city = City(st.session_state.selected_city)
            
            # Load street data
            streets = self.get_streets_for_city(selected_city)
            
            if streets.streets:
                self.save_to_session(streets)
                logger.info(f"Loaded {len(streets)} streets for {selected_city.name}")
                return streets
            else:
                logger.warning(f"No streets found for {selected_city.name}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading streets for selected city: {e}")
            return None