"""
FDOT GIS API Integration for City Data
"""

import requests
import logging
from typing import List, Dict, Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FDOTGISAPI:
    """
    FDOT GIS API client for fetching city boundary data
    """
    
    def __init__(self):
        """Initialize the FDOT GIS API client"""
        # City boundaries endpoint
        self.city_boundaries_url = "https://gis.fdot.gov/arcgis/rest/services/Admin_Boundaries/FeatureServer/7/query"
        
        # FLARIS street and road endpoints
        self.flaris_base_url = "https://gis.fdot.gov/arcgis/rest/services/sso/ssogis_flaris/FeatureServer"
        self.flaris_streets_url = f"{self.flaris_base_url}/0/query"  # ARBM Streets
        self.flaris_routes_url = f"{self.flaris_base_url}/1/query"   # ARBM Routes
        self.flaris_intersections_url = f"{self.flaris_base_url}/2/query"  # Intersections
        
        # Additional road data endpoints
        self.county_roads_url = "https://gis-fdot.opendata.arcgis.com/datasets/county-roads-tda/api"
        self.state_roads_url = "https://gis-fdot.opendata.arcgis.com/datasets/state-roads-tda/geoservice"
        self.roadways_local_name_url = "https://gis-fdot.opendata.arcgis.com/datasets/fdot::roadways-with-local-name-tda/about"
        
        # Keep the original base_url for backward compatibility
        self.base_url = self.city_boundaries_url
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VC-Mapper/1.0',
            'Accept': 'application/json'
        })
    
    def fetch_cities(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Fetch city data from FDOT GIS API
        
        Args:
            limit: Optional limit on number of cities to return
            
        Returns:
            List of city dictionaries with properties like name, geoid, coordinates, etc.
        """
        try:
            # Build query parameters
            params = {
                'where': '1=1',  # Get all records
                'outFields': '*',  # Get all fields
                'f': 'json',  # Return JSON format
                'returnGeometry': 'true'  # Include geometry data
            }
            
            if limit:
                params['resultRecordCount'] = limit
            
            logger.info(f"Fetching cities from FDOT GIS API with params: {params}")
            
            # Make the API request
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            if 'features' not in data:
                logger.error("No features found in API response")
                return []
            
            # Extract and format city data
            cities = []
            for feature in data['features']:
                if 'attributes' in feature:
                    city_data = self._format_city_data(feature)
                    if city_data:
                        cities.append(city_data)
            
            logger.info(f"Successfully fetched {len(cities)} cities from FDOT GIS API")
            return cities
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching cities from FDOT GIS API: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from FDOT GIS API: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching cities: {e}")
            return []
    
    def _format_city_data(self, feature: Dict) -> Optional[Dict]:
        """
        Format raw feature data into standardized city format
        
        Args:
            feature: Raw feature data from API
            
        Returns:
            Formatted city data dictionary or None if invalid
        """
        try:
            attributes = feature.get('attributes', {})
            geometry = feature.get('geometry', {})
            
            # Extract key city properties
            city_data = {
                'name': attributes.get('NAME', ''),
                'full_name': attributes.get('NAMELSAD', ''),
                'geoid': attributes.get('GEOID', ''),
                'state_fips': attributes.get('STATEFP', ''),
                'place_fips': attributes.get('PLACEFP', ''),
                'latitude': self._parse_coordinate(attributes.get('INTPTLAT', '')),
                'longitude': self._parse_coordinate(attributes.get('INTPTLON', '')),
                'population': attributes.get('POP', 0),
                'land_area': attributes.get('ALAND', 0),
                'water_area': attributes.get('AWATER', 0),
                'geometry': geometry,
                'lsad': attributes.get('LSAD', ''),  # Legal/Statistical Area Description
                'class_fp': attributes.get('CLASSFP', ''),  # Class FIPS code
                'func_stat': attributes.get('FUNCSTAT', '')  # Functional status
            }
            
            # Validate required fields
            if not city_data['name'] or not city_data['geoid']:
                logger.warning(f"Skipping city with missing required fields: {city_data}")
                return None
            
            return city_data
            
        except Exception as e:
            logger.error(f"Error formatting city data: {e}")
            return None
    
    def _parse_coordinate(self, coord_str: str) -> Optional[float]:
        """
        Parse coordinate string to float value
        
        Args:
            coord_str: Coordinate string (e.g., "+28.1787326")
            
        Returns:
            Float coordinate value or None if invalid
        """
        try:
            if not coord_str:
                return None
            return float(coord_str)
        except (ValueError, TypeError):
            logger.warning(f"Invalid coordinate format: {coord_str}")
            return None
    
    def search_cities(self, query: str, limit: Optional[int] = 10) -> List[Dict]:
        """
        Search for cities by name
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of matching cities
        """
        try:
            # Build search query
            search_where = f"NAME LIKE '%{query}%' OR NAMELSAD LIKE '%{query}%'"
            
            params = {
                'where': search_where,
                'outFields': '*',
                'f': 'json',
                'returnGeometry': 'true'
            }
            
            if limit:
                params['resultRecordCount'] = limit
            
            logger.info(f"Searching cities with query: {query}")
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'features' not in data:
                return []
            
            cities = []
            for feature in data['features']:
                if 'attributes' in feature:
                    city_data = self._format_city_data(feature)
                    if city_data:
                        cities.append(city_data)
            
            logger.info(f"Found {len(cities)} cities matching query: {query}")
            return cities
            
        except Exception as e:
            logger.error(f"Error searching cities: {e}")
            return []
    
    def get_city_by_geoid(self, geoid: str) -> Optional[Dict]:
        """
        Get specific city by GEOID
        
        Args:
            geoid: Geographic identifier for the city
            
        Returns:
            City data dictionary or None if not found
        """
        try:
            params = {
                'where': f"GEOID = '{geoid}'",
                'outFields': '*',
                'f': 'json',
                'returnGeometry': 'true'
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'features' in data and len(data['features']) > 0:
                feature = data['features'][0]
                return self._format_city_data(feature)
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching city by GEOID {geoid}: {e}")
            return None
    
    def get_city_boundary(self, city_geoid: str) -> Optional[Dict]:
        """
        Get city boundary geometry for a specific city
        
        Args:
            city_geoid: Geographic identifier for the city
            
        Returns:
            City boundary data with geometry or None if not found
        """
        try:
            params = {
                'where': f"GEOID = '{city_geoid}'",
                'outFields': '*',
                'f': 'json',
                'returnGeometry': 'true'
            }
            
            response = self.session.get(self.city_boundaries_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'features' in data and len(data['features']) > 0:
                feature = data['features'][0]
                boundary_data = {
                    'geoid': city_geoid,
                    'geometry': feature.get('geometry', {}),
                    'attributes': feature.get('attributes', {})
                }
                logger.info(f"Successfully fetched boundary for city {city_geoid}")
                return boundary_data
            
            logger.warning(f"No boundary found for city {city_geoid}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching city boundary for {city_geoid}: {e}")
            return None
    
    def fetch_streets_in_city(self, city_geoid: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Fetch street data for a specific city using FLARIS endpoints
        
        Args:
            city_geoid: Geographic identifier for the city
            limit: Optional limit on number of streets to return
            
        Returns:
            List of street dictionaries with geometry and attributes
        """
        try:
            # First get city boundary to create spatial filter
            city_boundary = self.get_city_boundary(city_geoid)
            if not city_boundary:
                logger.warning(f"Cannot fetch streets without city boundary for {city_geoid}")
                return []
            
            # Build spatial query using city boundary
            params = {
                'where': '1=1',  # Get all records within spatial filter
                'outFields': '*',
                'f': 'json',
                'returnGeometry': 'true',
                'spatialRel': 'esriSpatialRelIntersects'
            }
            
            # Add geometry filter if available
            if city_boundary.get('geometry'):
                params['geometry'] = json.dumps(city_boundary['geometry'])
                params['geometryType'] = 'esriGeometryPolygon'
            
            if limit:
                params['resultRecordCount'] = limit
            
            logger.info(f"Fetching streets for city {city_geoid} from FLARIS API")
            
            # Try FLARIS streets endpoint first
            response = self.session.get(self.flaris_streets_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'features' not in data:
                logger.warning("No street features found in API response")
                return []
            
            # Format street data
            streets = []
            for feature in data['features']:
                if 'attributes' in feature:
                    street_data = self._format_street_data(feature)
                    if street_data:
                        streets.append(street_data)
            
            logger.info(f"Successfully fetched {len(streets)} streets for city {city_geoid}")
            return streets
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching streets from FLARIS API: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from FLARIS API: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching streets: {e}")
            return []
    
    def _format_street_data(self, feature: Dict) -> Optional[Dict]:
        """
        Format raw street feature data into standardized format
        
        Args:
            feature: Raw street feature data from API
            
        Returns:
            Formatted street data dictionary or None if invalid
        """
        try:
            attributes = feature.get('attributes', {})
            geometry = feature.get('geometry', {})
            
            # Extract street properties (adapt field names based on FLARIS schema)
            street_data = {
                'street_id': attributes.get('OBJECTID', ''),
                'street_name': attributes.get('STREET_NAME', attributes.get('NAME', '')),
                'road_number': attributes.get('ROAD_NUMBER', ''),
                'route_id': attributes.get('ROUTE_ID', ''),
                'from_measure': attributes.get('FROM_MEASURE', 0),
                'to_measure': attributes.get('TO_MEASURE', 0),
                'length': attributes.get('LENGTH', 0),
                'county': attributes.get('COUNTY', ''),
                'district': attributes.get('DISTRICT', ''),
                'roadway_id': attributes.get('ROADWAY_ID', ''),
                'geometry': geometry,
                'traffic_volume': attributes.get('TRAFFIC_VOLUME', attributes.get('AADT', 0)),  # Annual Average Daily Traffic
                'traffic_level': self._classify_traffic_level(attributes.get('TRAFFIC_VOLUME', attributes.get('AADT', 0))),
                'functional_class': attributes.get('FUNCTIONAL_CLASS', ''),
                'surface_type': attributes.get('SURFACE_TYPE', ''),
                'lane_count': attributes.get('LANE_COUNT', 0),
                'speed_limit': attributes.get('SPEED_LIMIT', 0),
                'raw_attributes': attributes  # Keep all original attributes for reference
            }
            
            # Validate required fields
            if not street_data['street_name'] and not street_data['road_number']:
                logger.warning(f"Skipping street with missing name/number: {street_data}")
                return None
            
            return street_data
            
        except Exception as e:
            logger.error(f"Error formatting street data: {e}")
            return None
    
    def _classify_traffic_level(self, traffic_volume: int) -> str:
        """
        Classify traffic level based on volume
        
        Args:
            traffic_volume: Annual Average Daily Traffic (AADT) or similar metric
            
        Returns:
            Traffic level classification string
        """
        try:
            volume = int(traffic_volume) if traffic_volume else 0
            
            if volume >= 50000:
                return 'very_high'
            elif volume >= 25000:
                return 'high'
            elif volume >= 10000:
                return 'medium'
            elif volume >= 5000:
                return 'low'
            else:
                return 'very_low'
                
        except (ValueError, TypeError):
            return 'unknown'
    
    def get_traffic_color(self, traffic_level: str) -> str:
        """
        Get color code for traffic level visualization
        
        Args:
            traffic_level: Traffic level classification
            
        Returns:
            Hex color code for the traffic level
        """
        traffic_colors = {
            'very_high': '#FF0000',  # Red
            'high': '#FF6600',       # Orange
            'medium': '#FFFF00',     # Yellow
            'low': '#66FF00',        # Light Green
            'very_low': '#00FF00',   # Green
            'unknown': '#808080'     # Gray
        }
        return traffic_colors.get(traffic_level, '#808080') 