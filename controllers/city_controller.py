"""
City Controller - Handles city data operations and business logic
"""

from typing import List, Dict, Optional
import logging
import streamlit as st
from fdot_api import FDOTGISAPI
from models.city_model import City, CityCollection

logger = logging.getLogger(__name__)


class CityController:
    """
    Controller for city-related operations
    """
    
    def __init__(self):
        """Initialize the city controller with FDOT API client"""
        self.fdot_api = FDOTGISAPI()
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
            cities_data = self.fdot_api.fetch_cities(limit=limit)
            
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
            cities_data = self.fdot_api.search_cities(query, limit)
            
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
            city_data = self.fdot_api.get_city_by_geoid(geoid)
            
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
    
    def get_city_boundary(self, geoid: str) -> Optional[Dict]:
        """
        Get city boundary data
        
        Args:
            geoid: Geographic identifier
            
        Returns:
            Boundary data dictionary if found, None otherwise
        """
        try:
            logger.info(f"Fetching boundary for city with GEOID {geoid}")
            boundary_data = self.fdot_api.get_city_boundary(geoid)
            
            if boundary_data:
                logger.info(f"Successfully fetched boundary data for {geoid}")
                return boundary_data
            else:
                logger.warning(f"No boundary data found for GEOID {geoid}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching city boundary: {e}")
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