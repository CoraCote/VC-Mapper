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
        self.base_url = "https://gis.fdot.gov/arcgis/rest/services/Admin_Boundaries/FeatureServer/7/query"
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