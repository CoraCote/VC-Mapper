"""
FDOT ArcGIS REST API Integration for V/C Ratio Calculator
"""

import requests
import pandas as pd
import logging
from typing import Optional, Dict, List
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FDOTArcGISAPI:
    """
    Class to handle FDOT Traffic Online API interactions using ArcGIS REST API
    """
    
    def __init__(self, base_url: str = "https://devgis.fdot.gov/arcgis/rest/services/fto/fto_DEV/MapServer"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VC-Ratio-Calculator/1.0'
        })
    
    def get_traffic_monitoring_sites(self, county: str = None, district: str = None) -> pd.DataFrame:
        """
        Fetch traffic monitoring sites data from FDOT ArcGIS REST API
        
        Args:
            county: County name filter
            district: FDOT district filter
            
        Returns:
            DataFrame with traffic monitoring sites data
        """
        try:
            # Layer 0 contains Traffic Monitoring Sites
            query_url = f"{self.base_url}/0/query"
            
            # Build where clause based on filters
            where_clause = "1=1"  # Default to all records
            if county:
                where_clause += f" AND COUNTY_NAME='{county}'"
            if district:
                where_clause += f" AND DISTRICT='{district}'"
            
            params = {
                'where': where_clause,
                'outFields': '*',
                'f': 'json',
                'returnGeometry': 'true'
            }
            
            logger.info(f"Fetching traffic monitoring sites for county: {county}, district: {district}")
            
            response = self.session.get(query_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if "features" not in data or not data["features"]:
                logger.warning("No traffic monitoring sites found")
                return pd.DataFrame()
            
            # Extract features and convert to DataFrame
            features = data["features"]
            records = []
            
            for feature in features:
                attributes = feature.get("attributes", {})
                geometry = feature.get("geometry", {})
                
                record = {
                    'site_id': attributes.get('SITE_ID', ''),
                    'site_name': attributes.get('SITE_NAME', ''),
                    'county': attributes.get('COUNTY_NAME', ''),
                    'district': attributes.get('DISTRICT', ''),
                    'route': attributes.get('ROUTE', ''),
                    'functional_class': attributes.get('FUNCTIONAL_CLASS', ''),
                    'latitude': geometry.get('y', 0),
                    'longitude': geometry.get('x', 0),
                    'aadt': attributes.get('AADT', 0),
                    'year': attributes.get('YEAR', 2023)
                }
                records.append(record)
            
            df = pd.DataFrame(records)
            
            # Clean and validate data
            df = self._clean_traffic_data(df)
            
            logger.info(f"Successfully fetched {len(df)} traffic monitoring sites")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching FDOT traffic data: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return pd.DataFrame()
    
    def get_aadt_data(self, county: str = None, year: int = 2023) -> pd.DataFrame:
        """
        Fetch AADT (Annual Average Daily Traffic) data from FDOT API
        
        Args:
            county: County name filter
            year: Year of data
            
        Returns:
            DataFrame with AADT data
        """
        try:
            # Layer 1 contains AADT data
            query_url = f"{self.base_url}/1/query"
            
            # Build where clause
            where_clause = f"YEAR={year}"
            if county:
                where_clause += f" AND COUNTY_NAME='{county}'"
            
            params = {
                'where': where_clause,
                'outFields': '*',
                'f': 'json',
                'returnGeometry': 'true'
            }
            
            logger.info(f"Fetching AADT data for county: {county}, year: {year}")
            
            response = self.session.get(query_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if "features" not in data or not data["features"]:
                logger.warning("No AADT data found")
                return pd.DataFrame()
            
            # Extract features and convert to DataFrame
            features = data["features"]
            records = []
            
            for feature in features:
                attributes = feature.get("attributes", {})
                geometry = feature.get("geometry", {})
                
                record = {
                    'segment_id': attributes.get('SEGMENT_ID', ''),
                    'road_name': attributes.get('ROAD_NAME', ''),
                    'county': attributes.get('COUNTY_NAME', ''),
                    'functional_class': attributes.get('FUNCTIONAL_CLASS', ''),
                    'aadt': attributes.get('AADT', 0),
                    'year': attributes.get('YEAR', year),
                    'latitude': geometry.get('y', 0),
                    'longitude': geometry.get('x', 0),
                    'geometry': f"POINT({geometry.get('x', 0)} {geometry.get('y', 0)})"
                }
                records.append(record)
            
            df = pd.DataFrame(records)
            
            # Clean and validate data
            df = self._clean_traffic_data(df)
            
            logger.info(f"Successfully fetched {len(df)} AADT records")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching AADT data: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return pd.DataFrame()
    
    def get_traffic_data(self, county: str = "Palm Beach", year: int = 2023) -> pd.DataFrame:
        """
        Fetch comprehensive traffic data from FDOT Traffic Online for a specific county
        
        Args:
            county: County name
            year: Year of traffic data
            
        Returns:
            DataFrame with traffic volume data
        """
        try:
            # Try to get AADT data first (more comprehensive)
            df = self.get_aadt_data(county, year)
            
            if df.empty:
                # Fallback to traffic monitoring sites
                logger.info("AADT data not available, falling back to traffic monitoring sites")
                df = self.get_traffic_monitoring_sites(county)
                
                # Rename columns to match expected format
                if not df.empty:
                    df = df.rename(columns={
                        'site_id': 'segment_id',
                        'site_name': 'road_name',
                        'aadt': 'current_volume'
                    })
            
            # If still empty, return empty DataFrame
            if df.empty:
                logger.warning("No real data available from FDOT API")
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching traffic data: {e}")
            return pd.DataFrame()
    
    def _clean_traffic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate traffic data
        
        Args:
            df: Raw DataFrame from API
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
        
        # Remove rows with missing critical data
        df = df.dropna(subset=['current_volume', 'road_name'])
        
        # Ensure current_volume is numeric
        df['current_volume'] = pd.to_numeric(df['current_volume'], errors='coerce')
        df = df.dropna(subset=['current_volume'])
        
        # Remove negative volumes
        df = df[df['current_volume'] > 0]
        
        # Ensure functional_class column exists and fill missing values
        if 'functional_class' not in df.columns:
            df['functional_class'] = 'Arterial'
        else:
            df['functional_class'] = df['functional_class'].fillna('Arterial')
        
        # Ensure segment_id exists
        if 'segment_id' not in df.columns:
            df['segment_id'] = range(1, len(df) + 1)
        
        return df


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


# Example usage function for Streamlit
def test_fdot_api():
    """
    Test function to demonstrate FDOT API integration
    """
    api = FDOTArcGISAPI()
    
    # Test traffic monitoring sites
    print("Testing traffic monitoring sites...")
    sites_df = api.get_traffic_monitoring_sites(county="Palm Beach")
    print(f"Found {len(sites_df)} traffic monitoring sites")
    
    # Test AADT data
    print("Testing AADT data...")
    aadt_df = api.get_aadt_data(county="Palm Beach", year=2023)
    print(f"Found {len(aadt_df)} AADT records")
    
    # Test comprehensive data
    print("Testing comprehensive traffic data...")
    traffic_df = api.get_traffic_data(county="Palm Beach", year=2023)
    print(f"Found {len(traffic_df)} traffic records")
    
    return traffic_df

if __name__ == "__main__":
    # Test the API integration
    test_fdot_api() 