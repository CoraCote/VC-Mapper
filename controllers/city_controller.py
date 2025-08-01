"""
City Controller - Handles city data operations and business logic
"""

from typing import List, Dict, Optional
import logging
import streamlit as st
import requests
import json
from models.city_model import City, CityCollection

logger = logging.getLogger(__name__)


class CityController:
    """
    Controller for city-related operations with integrated FDOT GIS API functionality
    """
    
    def __init__(self):
        """Initialize the city controller with integrated API functionality"""
        # FDOT GIS API endpoints
        self.city_boundaries_url = "https://gis.fdot.gov/arcgis/rest/services/Admin_Boundaries/FeatureServer/7/query"
        
        # HTTP session for API calls
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VC-Mapper/1.0',
            'Accept': 'application/json'
        })
        
        self.city_collection = CityCollection()
    
    def fetch_all_cities(self, limit: int = 50) -> CityCollection:
        """
        Fetch all cities from FDOT API
        
        Args:
            limit: Maximum number of cities to fetch
            
        Returns:
            CityCollection object with fetched cities
        """
        try:
            logger.info(f"Fetching {limit} cities from FDOT API")
            cities_data = self._fetch_cities_from_api(limit=limit)
            
            if cities_data:
                self.city_collection = CityCollection(cities_data)
                logger.info(f"Successfully fetched {len(self.city_collection)} cities")
                return self.city_collection
            else:
                logger.warning("No cities data received from API")
                return CityCollection()
                
        except Exception as e:
            logger.error(f"Error fetching cities: {e}")
            return CityCollection()
    
    def search_cities(self, query: str, limit: int = 15) -> CityCollection:
        """
        Search for cities by name
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            CityCollection object with search results
        """
        try:
            logger.info(f"Searching for cities matching '{query}'")
            cities_data = self._search_cities_from_api(query, limit)
            
            if cities_data:
                self.city_collection = CityCollection(cities_data)
                logger.info(f"Found {len(self.city_collection)} cities matching '{query}'")
                return self.city_collection
            else:
                logger.warning(f"No cities found matching '{query}'")
                return CityCollection()
                
        except Exception as e:
            logger.error(f"Error searching cities: {e}")
            return CityCollection()
    
    def get_city_by_geoid(self, geoid: str) -> Optional[City]:
        """
        Get a specific city by GEOID
        
        Args:
            geoid: Geographic identifier
            
        Returns:
            City object if found, None otherwise
        """
        try:
            logger.info(f"Fetching city with GEOID {geoid}")
            city_data = self._get_city_by_geoid_from_api(geoid)
            
            if city_data:
                city = City(city_data)
                self.city_collection = CityCollection([city_data])
                logger.info(f"Found city: {city.name}")
                return city
            else:
                logger.warning(f"No city found with GEOID {geoid}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching city by GEOID: {e}")
            return None
    

    
    def filter_cities(self, cities: CityCollection, filters: Dict) -> CityCollection:
        """
        Apply filters to city collection
        
        Args:
            cities: City collection to filter
            filters: Dictionary of filter criteria
            
        Returns:
            Filtered city collection
        """
        try:
            filtered_cities = cities.cities.copy()
            
            # Apply population filter
            if 'min_population' in filters:
                filtered_cities = [city for city in filtered_cities 
                                 if city.population >= filters['min_population']]
            
            # Apply state FIPS filter
            if 'state_fips' in filters and filters['state_fips'] != "All":
                filtered_cities = [city for city in filtered_cities 
                                 if city.state_fips == filters['state_fips']]
            
            # Create new collection with filtered cities
            filtered_collection = CityCollection()
            filtered_collection.cities = filtered_cities
            
            logger.info(f"Filtered {len(cities)} cities to {len(filtered_collection)} cities")
            return filtered_collection
            
        except Exception as e:
            logger.error(f"Error filtering cities: {e}")
            return cities
    
    def sort_cities(self, cities: CityCollection, sort_by: str, reverse: bool = False) -> CityCollection:
        """
        Sort cities by specified criteria
        
        Args:
            cities: City collection to sort
            sort_by: Field to sort by
            reverse: Whether to sort in descending order
            
        Returns:
            Sorted city collection
        """
        try:
            sorted_cities = cities.sort_cities(sort_by, reverse)
            
            sorted_collection = CityCollection()
            sorted_collection.cities = sorted_cities
            
            logger.info(f"Sorted {len(cities)} cities by {sort_by}")
            return sorted_collection
            
        except Exception as e:
            logger.error(f"Error sorting cities: {e}")
            return cities
    
    def get_session_cities(self) -> Optional[CityCollection]:
        """
        Get cities from session state
        
        Returns:
            CityCollection from session state or None
        """
        if 'cities_data' in st.session_state and st.session_state.cities_data:
            return CityCollection(st.session_state.cities_data)
        return None
    
    def save_to_session(self, cities: CityCollection):
        """
        Save cities to session state
        
        Args:
            cities: City collection to save
        """
        st.session_state.cities_data = cities.get_cities_as_dict_list()
        logger.info(f"Saved {len(cities)} cities to session state")
    
    def get_selected_city(self) -> Optional[City]:
        """
        Get selected city from session state
        
        Returns:
            Selected city or None
        """
        if 'selected_city' in st.session_state and st.session_state.selected_city:
            return City(st.session_state.selected_city)
        return None
    
    def set_selected_city(self, city: Optional[City]):
        """
        Set selected city in session state
        
        Args:
            city: City to select or None to deselect
        """
        if city:
            st.session_state.selected_city = city.to_dict()
            logger.info(f"Selected city: {city.name}")
        else:
            st.session_state.selected_city = None
            logger.info("Deselected city")
    
    def get_city_statistics(self, cities: CityCollection) -> Dict:
        """
        Calculate statistics for city collection
        
        Args:
            cities: City collection to analyze
            
        Returns:
            Dictionary of statistics
        """
        try:
            if not cities.cities:
                return {
                    'total_cities': 0,
                    'total_population': 0,
                    'average_population': 0,
                    'median_population': 0,
                    'total_land_area_km2': 0,
                    'total_water_area_km2': 0,
                    'largest_city': None,
                    'smallest_city': None
                }
            
            return {
                'total_cities': len(cities),
                'total_population': cities.get_total_population(),
                'average_population': cities.get_average_population(),
                'median_population': cities.get_median_population(),
                'total_land_area_km2': cities.get_total_land_area() / 1000000,
                'total_water_area_km2': cities.get_total_water_area() / 1000000,
                'largest_city': cities.get_largest_city(),
                'smallest_city': cities.get_smallest_city()
            }
            
        except Exception as e:
            logger.error(f"Error calculating city statistics: {e}")
            return {}
    
    def handle_data_fetch_action(self, action: str, params: Dict) -> bool:
        """
        Handle data fetching based on action and parameters
        
        Args:
            action: The action to perform
            params: Action parameters
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if action == "🌍 Fetch All Cities" and params.get("button"):
                cities = self.fetch_all_cities(limit=params.get("limit", 50))
                if cities.cities:
                    self.save_to_session(cities)
                    st.success(f"✅ Successfully fetched {len(cities)} cities!")
                    return True
                else:
                    st.error("❌ Failed to fetch cities. Please check the API connection.")
                    return False
            
            elif action == "🔍 Search Cities" and params.get("button") and params.get("query"):
                cities = self.search_cities(params["query"], params.get("limit", 15))
                if cities.cities:
                    self.save_to_session(cities)
                    st.success(f"✅ Found {len(cities)} cities matching '{params['query']}'!")
                    return True
                else:
                    st.warning(f"⚠️ No cities found matching '{params['query']}'")
                    return False
            
            elif action == "📍 Get by GEOID" and params.get("button") and params.get("geoid"):
                city = self.get_city_by_geoid(params["geoid"])
                if city:
                    st.success(f"✅ Found city: {city.name}")
                    return True
                else:
                    st.error(f"❌ No city found with GEOID {params['geoid']}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error handling data fetch action: {e}")
            st.error(f"❌ Error: {str(e)}")
            return False
    
    # ===== INTEGRATED FDOT GIS API METHODS =====
    
    def _fetch_cities_from_api(self, limit: Optional[int] = None) -> List[Dict]:
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
            response = self.session.get(self.city_boundaries_url, params=params, timeout=30)
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
    
    def _search_cities_from_api(self, query: str, limit: Optional[int] = 10) -> List[Dict]:
        """
        Search for cities by name using FDOT GIS API with enhanced search capabilities
        
        Args:
            query: Search query string
            limit: Optional limit on number of results
            
        Returns:
            List of matching city dictionaries
        """
        try:
            # Clean and prepare search query
            query_clean = query.strip()
            if not query_clean:
                return []
            
            # Build multiple search patterns for better results
            # Try exact match first, then partial matches
            search_patterns = [
                f"NAME = '{query_clean.upper()}'",  # Exact match (case insensitive)
                f"FULLNAME = '{query_clean.upper()}'",  # Exact match on full name
                f"NAME LIKE '{query_clean.upper()}%'",  # Starts with query
                f"FULLNAME LIKE '{query_clean.upper()}%'",  # Starts with query in full name
                f"NAME LIKE '%{query_clean.upper()}%'",  # Contains query anywhere
                f"FULLNAME LIKE '%{query_clean.upper()}%'"  # Contains query anywhere in full name
            ]
            
            # Combine all patterns with OR
            where_clause = " OR ".join(search_patterns)
            
            params = {
                'where': where_clause,
                'outFields': '*',
                'f': 'json',
                'returnGeometry': 'true'
            }
            
            if limit:
                params['resultRecordCount'] = limit
            
            logger.info(f"Searching cities with query '{query_clean}' using enhanced search patterns")
            
            # Make the API request
            response = self.session.get(self.city_boundaries_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            if 'features' not in data:
                logger.warning(f"No features found for search query: {query_clean}")
                return []
            
            # Extract and format city data
            cities = []
            seen_geoids = set()  # Prevent duplicates
            
            for feature in data['features']:
                if 'attributes' in feature:
                    city_data = self._format_city_data(feature)
                    if city_data and city_data['geoid'] not in seen_geoids:
                        cities.append(city_data)
                        seen_geoids.add(city_data['geoid'])
            
            # Sort results by relevance - exact matches first, then partial matches
            cities_sorted = sorted(cities, key=lambda x: (
                # Primary sort: exact match gets priority
                0 if x['name'].upper() == query_clean.upper() else 1,
                # Secondary sort: starts with gets priority over contains
                0 if x['name'].upper().startswith(query_clean.upper()) else 1,
                # Tertiary sort: alphabetical
                x['name']
            ))
            
            logger.info(f"Found {len(cities_sorted)} unique cities matching '{query_clean}'")
            
            # Log first few results for debugging
            if cities_sorted:
                result_names = [city['name'] for city in cities_sorted[:5]]
                logger.info(f"Top results: {result_names}")
            
            return cities_sorted
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching cities: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing search response: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching cities: {e}")
            return []
    
    def _get_city_by_geoid_from_api(self, geoid: str) -> Optional[Dict]:
        """
        Get a specific city by GEOID using FDOT GIS API
        
        Args:
            geoid: Geographic identifier
            
        Returns:
            City data dictionary if found, None otherwise
        """
        try:
            params = {
                'where': f"GEOID = '{geoid}'",
                'outFields': '*',
                'f': 'json',
                'returnGeometry': 'true'
            }
            
            logger.info(f"Fetching city with GEOID {geoid}")
            
            # Make the API request
            response = self.session.get(self.city_boundaries_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            if 'features' not in data or len(data['features']) == 0:
                logger.warning(f"No city found with GEOID: {geoid}")
                return None
            
            # Get the first (and should be only) feature
            feature = data['features'][0]
            
            if 'attributes' in feature:
                city_data = self._format_city_data(feature)
                if city_data:
                    logger.info(f"Found city: {city_data.get('name', 'Unknown')}")
                    return city_data
            
            logger.warning(f"Invalid city data for GEOID: {geoid}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching city by GEOID: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing city response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching city by GEOID: {e}")
            return None
    
    def _format_city_data(self, feature: Dict) -> Optional[Dict]:
        """
        Format raw FDOT GIS API feature data into standardized city dictionary
        
        Args:
            feature: Raw feature data from FDOT GIS API
            
        Returns:
            Formatted city data dictionary or None if invalid
        """
        try:
            attrs = feature.get('attributes', {})
            geometry = feature.get('geometry', {})
            
            # Extract required fields
            name = attrs.get('NAME', '').strip()
            full_name = attrs.get('FULLNAME', name).strip()
            geoid = str(attrs.get('GEOID', ''))
            
            # Skip if no name or geoid
            if not name or not geoid:
                return None
            
            # Extract coordinates (convert from string if needed)
            try:
                lat_str = attrs.get('INTPTLAT', '0')
                lon_str = attrs.get('INTPTLON', '0')
                latitude = float(lat_str.replace('+', '')) if lat_str else 0.0
                longitude = float(lon_str.replace('+', '')) if lon_str else 0.0
            except (ValueError, TypeError):
                latitude = longitude = 0.0
            
            # Extract other fields with defaults
            population = attrs.get('POP', 0) or 0
            land_area = attrs.get('ALAND', 0) or 0.0
            water_area = attrs.get('AWATER', 0) or 0.0
            state_fips = attrs.get('STATEFP', '12')  # Florida is 12
            place_fips = attrs.get('PLACEFP', '')
            lsad = attrs.get('LSAD', '')
            class_fp = attrs.get('CLASSFP', '')
            func_stat = attrs.get('FUNCSTAT', '')
            
            # Create standardized city data dictionary
            city_data = {
                'name': name,
                'full_name': full_name,
                'geoid': geoid,
                'latitude': latitude,
                'longitude': longitude,
                'population': int(population),
                'land_area': float(land_area),
                'water_area': float(water_area),
                'state_fips': str(state_fips),
                'place_fips': str(place_fips),
                'lsad': str(lsad),
                'class_fp': str(class_fp),
                'func_stat': str(func_stat),
                'geometry': geometry
            }
            
            return city_data
            
        except Exception as e:
            logger.error(f"Error formatting city data: {e}")
            return None