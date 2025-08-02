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
    
    def fetch_all_cities(self, limit: Optional[int] = None, save_to_file: bool = False) -> CityCollection:
        """
        Fetch all cities from FDOT API
        
        Args:
            limit: Maximum number of cities to fetch (None for unlimited)
            save_to_file: Whether to save the data to a local JSON file
            
        Returns:
            CityCollection object with fetched cities
        """
        try:
            if limit is None:
                logger.info("Fetching ALL cities from FDOT API (no limit)")
            else:
                logger.info(f"Fetching {limit} cities from FDOT API")
            
            cities_data = self._fetch_cities_from_api(limit=limit)
            
            if cities_data:
                self.city_collection = CityCollection(cities_data)
                logger.info(f"Successfully fetched {len(self.city_collection)} cities")
                
                # Save to JSON file if requested
                if save_to_file:
                    self._save_cities_to_json(self.city_collection)
                
                return self.city_collection
            else:
                logger.warning("No cities data received from API")
                return CityCollection()
                
        except Exception as e:
            logger.error(f"Error fetching cities: {e}")
            return CityCollection()
    

    
    def search_cities(self, query: str) -> CityCollection:
        """
        Search for cities by name using FDOT API
        
        Args:
            query: Search query (city name)
            
        Returns:
            CityCollection with matching cities
        """
        try:
            logger.info(f"Starting search for cities matching '{query}' (no limit)")
            
            # Clean and escape the query
            clean_query = query.strip()
            if not clean_query:
                logger.warning("Empty search query provided")
                return CityCollection()
            
            escaped_query = clean_query.replace("'", "''")  # Escape single quotes for SQL
            logger.info(f"Searching cities with query '{query}' (escaped: '{escaped_query}')")
            
            # Try multiple search strategies
            search_strategies = [
                ("exact", f"NAME = '{escaped_query}'"),
                ("starts_with", f"NAME LIKE '{escaped_query}%'"),
                ("contains", f"NAME LIKE '%{escaped_query}%'"),
                ("fuzzy", f"UPPER(NAME) LIKE '%{escaped_query.upper()}%'")
            ]
            
            for strategy_name, where_clause in search_strategies:
                try:
                    cities_data = self._search_cities_from_api(where_clause)
                    if cities_data:
                        city_collection = CityCollection(cities_data)
                        logger.info(f"Found {len(city_collection)} cities using {strategy_name} search")
                        return city_collection
                except Exception as e:
                    logger.error(f"FDOT API error for {strategy_name} search '{query}': {e}")
                    continue
            
            logger.warning(f"No cities found for any search strategy with query: '{query}'")
            return CityCollection()
            
        except Exception as e:
            logger.error(f"Error searching for cities: {e}")
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
            from utils.loading_utils import DataLoadingIndicators, create_multi_step_progress
            
            if action == "🌍 Fetch All Cities" and params.get("button"):
                # Determine if we should fetch all cities (no limit)
                fetch_all = params.get("fetch_all", False)
                limit = None if fetch_all else params.get("limit", 50)
                save_to_file = params.get("save_to_file", False)
                
                # Create multi-step progress tracker
                steps = ["Fetching cities", "Processing data", "Saving to session"]
                if params.get("fetch_traffic", False):
                    steps.extend(["Fetching traffic data", "Processing traffic data", "Saving traffic data"])
                if save_to_file:
                    steps.append("Saving to JSON file")
                
                progress = create_multi_step_progress("Data Fetch Operation", steps)
                
                try:
                    # Step 1: Fetch cities
                    progress.step("Fetching cities")
                    with DataLoadingIndicators.fetch_cities_loading():
                        cities = self.fetch_all_cities(limit=limit, save_to_file=save_to_file)
                    
                    if not cities.cities:
                        progress.error("Failed to fetch cities. Please check the API connection.")
                        return False
                    
                    # Step 2: Process data
                    progress.step("Processing data")
                    with DataLoadingIndicators.process_data_loading():
                        # Process cities data
                        pass
                    
                    # Step 3: Save to session
                    progress.step("Saving to session")
                    self.save_to_session(cities)
                    
                    # Fetch traffic data if requested
                    if params.get("fetch_traffic", False):
                        # Step 4: Fetch traffic data
                        progress.step("Fetching traffic data")
                        with DataLoadingIndicators.fetch_traffic_loading():
                            traffic_data = self.fetch_traffic_data_with_pagination()
                        
                        if traffic_data:
                            # Step 5: Process traffic data
                            progress.step("Processing traffic data")
                            with DataLoadingIndicators.process_data_loading():
                                # Process traffic data
                                pass
                            
                            # Step 6: Save traffic data
                            progress.step("Saving traffic data")
                            with DataLoadingIndicators.save_data_loading():
                                self.save_traffic_data_to_json(traffic_data)
                                st.session_state.traffic_data = traffic_data
                            
                            record_count = len(traffic_data.get('features', []))
                            progress.complete(f"Successfully fetched {len(cities)} cities and {record_count} traffic records!")
                        else:
                            progress.error("Cities fetched successfully, but traffic data failed to load.")
                            return False
                    else:
                        # Save to file if requested
                        if save_to_file:
                            progress.step("Saving to JSON file")
                            with DataLoadingIndicators.save_data_loading():
                                # File saving is handled in fetch_all_cities
                                pass
                        
                        progress.complete(f"Successfully fetched {len(cities)} cities!")
                    
                    return True
                    
                except Exception as e:
                    progress.error(f"Error during data fetch: {str(e)}")
                    return False
            
            elif action == "🔍 Search Cities" and params.get("button") and params.get("query"):
                with DataLoadingIndicators.search_cities_loading():
                    cities = self.search_cities(params["query"])
                    
                if cities.cities:
                    with DataLoadingIndicators.save_data_loading():
                        self.save_to_session(cities)
                    st.success(f"✅ Found {len(cities)} cities matching '{params['query']}'!")
                    return True
                else:
                    st.warning(f"⚠️ No cities found matching '{params['query']}'")
                    return False

            elif action == "📍 Get by GEOID" and params.get("button") and params.get("geoid"):
                with DataLoadingIndicators.search_cities_loading():
                    city = self.get_city_by_geoid(params["geoid"])
                
                if city:
                    # Auto-select the found city for automatic scaling
                    st.session_state.selected_city = city.to_dict()
                    st.session_state.auto_scaled_city = True  # Flag for auto-scaling
                    st.success(f"✅ Found city: **{city.name}** - Auto-zooming to city area!")
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

    def _save_cities_to_json(self, cities: CityCollection) -> bool:
        """
        Save cities data to a local JSON file (overwrites existing file)
        
        Args:
            cities: CityCollection to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import json
            import os
            from datetime import datetime
            
            # Create data directory if it doesn't exist
            data_dir = "data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # Use fixed filename (overwrites existing file)
            filename = f"{data_dir}/cities_data.json"
            
            # Prepare data for JSON serialization
            cities_data = {
                "metadata": {
                    "total_cities": len(cities),
                    "fetch_timestamp": datetime.now().isoformat(),
                    "source": "FDOT GIS API"
                },
                "cities": cities.get_cities_as_dict_list()
            }
            
            # Save to JSON file (overwrites if exists)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cities_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved {len(cities)} cities to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving cities to JSON: {e}")
            return False

    def fetch_traffic_data(self, limit: Optional[int] = None) -> Dict:
        """
        Fetch traffic data from the Annual Average Daily Traffic API
        
        Args:
            limit: Maximum number of records to fetch (None for all available)
            
        Returns:
            Dictionary containing traffic data
        """
        try:
            traffic_url = "https://services1.arcgis.com/O1JpcwDW8sjYuddV/arcgis/rest/services/Annual_Average_Daily_Traffic_TDA/FeatureServer/0/query"
            
            params = {
                'outFields': '*',
                'where': '1=1',
                'f': 'geojson'
            }
            
            # Add limit if specified
            if limit:
                params['resultRecordCount'] = limit
                logger.info(f"Fetching traffic data with limit of {limit} records...")
            else:
                logger.info("Fetching ALL traffic data (no limit)...")
            
            # Increase timeout for large datasets
            timeout = 120 if limit is None else 60
            
            response = self.session.get(traffic_url, params=params, timeout=timeout)
            response.raise_for_status()
            
            # Parse GeoJSON response
            traffic_data = response.json()
            
            if 'features' in traffic_data:
                record_count = len(traffic_data['features'])
                logger.info(f"Successfully fetched {record_count} traffic records")
                
                # Check if we got all records (if no limit was set)
                if limit is None and record_count > 0:
                    # Check if there might be more records (ArcGIS often limits to 1000-2000)
                    if record_count >= 1000:
                        logger.warning(f"Fetched {record_count} records. ArcGIS APIs often have default limits. Consider using pagination for complete dataset.")
                
                return traffic_data
            else:
                logger.warning("No features found in traffic data response")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching traffic data: {e}")
            return {}

    def save_traffic_data_to_json(self, traffic_data: Dict) -> bool:
        """
        Save traffic data to a local JSON file (overwrites existing file)
        
        Args:
            traffic_data: Traffic data dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import json
            import os
            from datetime import datetime
            
            # Create data directory if it doesn't exist
            data_dir = "data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # Use fixed filename (overwrites existing file)
            filename = f"{data_dir}/traffic_data.json"
            
            # Prepare data with metadata
            data_to_save = {
                "metadata": {
                    "total_records": len(traffic_data.get('features', [])),
                    "fetch_timestamp": datetime.now().isoformat(),
                    "source": "Annual Average Daily Traffic TDA API"
                },
                "traffic_data": traffic_data
            }
            
            # Save to JSON file (overwrites if exists)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved traffic data to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving traffic data to JSON: {e}")
            return False

    def load_cities_from_json(self) -> Optional[CityCollection]:
        """
        Load cities data from saved JSON file (fixed filename)
        
        Returns:
            CityCollection if successful, None otherwise
        """
        try:
            import json
            import os
            
            # Look for cities data file in the data directory
            data_dir = "data"
            cities_file = os.path.join(data_dir, "cities_data.json")
            
            if not os.path.exists(cities_file):
                return None
            
            # Load cities data from fixed filename
            with open(cities_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'cities' in data:
                    cities_data = data['cities']
                    city_collection = CityCollection(cities_data)
                    logger.info(f"Loaded {len(city_collection)} cities from {cities_file}")
                    return city_collection
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading cities from JSON: {e}")
            return None

    def load_traffic_data_from_json(self) -> Optional[Dict]:
        """
        Load traffic data from saved JSON file (fixed filename)
        
        Returns:
            Traffic data dictionary if successful, None otherwise
        """
        try:
            import json
            import os
            
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
            logger.error(f"Error loading traffic data from JSON: {e}")
            return None

    def fetch_traffic_data_with_pagination(self, max_records: Optional[int] = None) -> Dict:
        """
        Fetch traffic data with pagination to handle large datasets
        
        Args:
            max_records: Maximum total records to fetch (None for all available)
            
        Returns:
            Dictionary containing complete traffic data
        """
        try:
            from utils.loading_utils import DataLoadingIndicators, create_multi_step_progress
            
            traffic_url = "https://services1.arcgis.com/O1JpcwDW8sjYuddV/arcgis/rest/services/Annual_Average_Daily_Traffic_TDA/FeatureServer/0/query"
            
            # Create progress tracker for pagination
            progress = create_multi_step_progress("Traffic Data Fetch", [
                "Initializing connection",
                "Fetching data batches", 
                "Processing records",
                "Finalizing data"
            ])
            
            try:
                # Step 1: Initialize connection
                progress.step("Initializing connection")
                
                all_features = []
                offset = 0
                batch_size = 1000  # ArcGIS default limit
                batch_count = 0
                
                logger.info("Fetching traffic data with pagination...")
                
                # Step 2: Fetch data batches
                progress.step("Fetching data batches")
                
                with DataLoadingIndicators.fetch_traffic_loading():
                    while True:
                        params = {
                            'outFields': '*',
                            'where': '1=1',
                            'f': 'geojson',
                            'resultOffset': offset,
                            'resultRecordCount': batch_size
                        }
                        
                        response = self.session.get(traffic_url, params=params, timeout=60)
                        response.raise_for_status()
                        
                        traffic_data = response.json()
                        
                        if 'features' not in traffic_data or not traffic_data['features']:
                            break
                        
                        features = traffic_data['features']
                        all_features.extend(features)
                        batch_count += 1
                        
                        logger.info(f"Fetched batch: {len(features)} records (total: {len(all_features)})")
                        
                        # Check if we've reached the limit
                        if max_records and len(all_features) >= max_records:
                            all_features = all_features[:max_records]
                            break
                        
                        # Check if we got fewer records than requested (end of data)
                        if len(features) < batch_size:
                            break
                        
                        offset += batch_size
                        
                        # Safety check to prevent infinite loops
                        if offset > 50000:  # Maximum reasonable offset
                            logger.warning("Reached maximum offset limit, stopping pagination")
                            break
                
                # Step 3: Process records
                progress.step("Processing records")
                with DataLoadingIndicators.process_data_loading():
                    # Process the fetched data
                    pass
                
                # Step 4: Finalize data
                progress.step("Finalizing data")
                
                if all_features:
                    complete_data = {
                        'type': 'FeatureCollection',
                        'features': all_features
                    }
                    logger.info(f"Successfully fetched {len(all_features)} traffic records with pagination")
                    progress.complete(f"Successfully fetched {len(all_features)} traffic records in {batch_count} batches!")
                    return complete_data
                else:
                    logger.warning("No traffic records found")
                    progress.error("No traffic records found")
                    return {}
                    
            except Exception as e:
                progress.error(f"Error during traffic data fetch: {str(e)}")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching traffic data with pagination: {e}")
            return {}

    
    def _search_cities_from_api(self, where_clause: str) -> List[Dict]:
        """
        Search for cities using FDOT GIS API with a custom WHERE clause
        
        Args:
            where_clause: SQL WHERE clause for the search
            
        Returns:
            List of city dictionaries
        """
        try:
            params = {
                'where': where_clause,
                'outFields': '*',
                'f': 'json',
                'returnGeometry': 'true'
            }
            
            # Make the API request
            response = self.session.get(self.city_boundaries_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            if 'features' not in data:
                return []
            
            # Extract and format city data
            cities = []
            for feature in data['features']:
                if 'attributes' in feature:
                    city_data = self._format_city_data(feature)
                    if city_data:
                        cities.append(city_data)
            
            return cities
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching cities from FDOT GIS API: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing search response from FDOT GIS API: {e}")
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