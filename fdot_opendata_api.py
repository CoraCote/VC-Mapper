"""
FDOT Open Data Hub API Integration for V/C Ratio Calculator
"""

import requests
import pandas as pd
import logging
from typing import Optional, Dict, List, Any
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FDOTOpenDataAPI:
    """
    Class to handle FDOT Open Data Hub API interactions
    """
    
    def __init__(self, base_url: str = "https://gis-fdot.opendata.arcgis.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VC-Ratio-Calculator/1.0',
            'Accept': 'application/json'
        })
    
    def search_catalog(self, query: str = None, limit: int = 100) -> List[Dict]:
        """
        Search the FDOT Open Data Hub catalog
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of catalog items
        """
        try:
            url = f"{self.base_url}/api/search/v1/catalog"
            params = {
                'limit': limit
            }
            
            if query:
                params['q'] = query
            
            logger.info(f"Searching FDOT Open Data Hub catalog with query: {query}")
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if "collections" in data:
                return data["collections"]
            else:
                logger.warning("No collections found in catalog search")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching FDOT Open Data Hub catalog: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in catalog search: {e}")
            return []
    
    def get_collection_items(self, collection_id: str, limit: int = 1000) -> pd.DataFrame:
        """
        Get items from a specific collection
        
        Args:
            collection_id: The collection ID
            limit: Maximum number of items to return
            
        Returns:
            DataFrame with collection items
        """
        try:
            url = f"{self.base_url}/api/search/v1/collections/{collection_id}/items"
            params = {
                'limit': limit,
                'f': 'json'
            }
            
            logger.info(f"Fetching items from collection: {collection_id}")
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if "features" not in data or not data["features"]:
                logger.warning(f"No features found in collection {collection_id}")
                return pd.DataFrame()
            
            # Extract features and convert to DataFrame
            features = data["features"]
            records = []
            
            for feature in features:
                properties = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                
                record = {
                    'id': feature.get('id', ''),
                    'type': feature.get('type', ''),
                    'properties': properties,
                    'geometry': geometry
                }
                records.append(record)
            
            df = pd.DataFrame(records)
            
            # Flatten properties if they exist
            if not df.empty and 'properties' in df.columns:
                properties_df = pd.json_normalize(df['properties'])
                df = pd.concat([df.drop('properties', axis=1), properties_df], axis=1)
            
            logger.info(f"Successfully fetched {len(df)} items from collection {collection_id}")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching collection items: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching collection items: {e}")
            return pd.DataFrame()
    
    def get_cities_dataset(self) -> pd.DataFrame:
        """
        Search for and fetch cities dataset from FDOT Open Data Hub
        
        Returns:
            DataFrame with cities data
        """
        try:
            # Search for cities-related datasets
            logger.info("Searching for cities datasets in FDOT Open Data Hub...")
            
            # Try different search terms for cities
            search_terms = [
                "cities",
                "municipalities", 
                "incorporated areas",
                "city limits",
                "municipal boundaries"
            ]
            
            for search_term in search_terms:
                collections = self.search_catalog(query=search_term, limit=20)
                
                for collection in collections:
                    collection_id = collection.get('id', '')
                    if not collection_id:  # Skip if no collection ID
                        continue
                        
                    title = collection.get('title', '').lower()
                    description = collection.get('description', '').lower()
                    
                    # Check if this collection contains city data
                    if any(term in title or term in description for term in ['city', 'municipal', 'incorporated']):
                        logger.info(f"Found potential cities dataset: {collection.get('title', 'Unknown')}")
                        
                        # Try to fetch items from this collection
                        df = self.get_collection_items(collection_id)
                        
                        if not df.empty:
                            # Check if the data looks like cities
                            if self._is_cities_data(df):
                                logger.info(f"Successfully found cities dataset: {collection.get('title', 'Unknown')}")
                                return self._process_cities_data(df)
            
            # If no specific cities dataset found, try to find any dataset with city names
            logger.info("No specific cities dataset found, searching for any dataset with city names...")
            
            # Search for datasets that might contain city information
            collections = self.search_catalog(query="boundaries", limit=50)
            
            for collection in collections:
                collection_id = collection.get('id', '')
                if not collection_id:  # Skip if no collection ID
                    continue
                    
                df = self.get_collection_items(collection_id, limit=100)
                
                if not df.empty and self._is_cities_data(df):
                    logger.info(f"Found cities data in dataset: {collection.get('title', 'Unknown')}")
                    return self._process_cities_data(df)
            
            logger.warning("No cities dataset found in FDOT Open Data Hub")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error searching for cities dataset: {e}")
            return pd.DataFrame()
    
    def _is_cities_data(self, df: pd.DataFrame) -> bool:
        """
        Check if the DataFrame contains cities data
        
        Args:
            df: DataFrame to check
            
        Returns:
            True if the data appears to be cities data
        """
        if df.empty:
            return False
        
        # Look for columns that might indicate cities data
        columns = df.columns.str.lower()
        
        city_indicators = [
            'city', 'municipal', 'incorporated', 'name', 'title',
            'population', 'area', 'boundary', 'geometry'
        ]
        
        # Check if any city indicators are in column names
        has_city_columns = any(indicator in ' '.join(columns) for indicator in city_indicators)
        
        # Check if we have reasonable number of records (cities are typically 100-500 for a state)
        reasonable_count = 50 <= len(df) <= 1000
        
        return has_city_columns and reasonable_count
    
    def _process_cities_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process and standardize cities data
        
        Args:
            df: Raw cities DataFrame
            
        Returns:
            Processed cities DataFrame
        """
        try:
            # Create a standardized cities DataFrame
            cities_df = pd.DataFrame()
            
            # Try to extract city name from various possible column names
            name_columns = [col for col in df.columns if any(term in col.lower() for term in ['name', 'title', 'city'])]
            
            if name_columns:
                cities_df['city_name'] = df[name_columns[0]]
            else:
                # If no name column found, use the first string column
                string_columns = df.select_dtypes(include=['object']).columns
                if len(string_columns) > 0:
                    cities_df['city_name'] = df[string_columns[0]]
                else:
                    cities_df['city_name'] = f"City_{range(len(df))}"
            
            # Try to extract county information
            county_columns = [col for col in df.columns if 'county' in col.lower()]
            if county_columns:
                cities_df['county'] = df[county_columns[0]]
            else:
                cities_df['county'] = 'Unknown'
            
            # Try to extract population if available
            pop_columns = [col for col in df.columns if 'pop' in col.lower()]
            if pop_columns:
                cities_df['population'] = pd.to_numeric(df[pop_columns[0]], errors='coerce')
            else:
                cities_df['population'] = None
            
            # Try to extract geometry if available
            if 'geometry' in df.columns:
                cities_df['geometry'] = df['geometry']
            
            # Clean and sort the data
            cities_df = cities_df.dropna(subset=['city_name'])
            cities_df = cities_df.sort_values('city_name')
            
            # Remove duplicates
            cities_df = cities_df.drop_duplicates(subset=['city_name'])
            
            logger.info(f"Processed {len(cities_df)} cities from FDOT Open Data Hub")
            return cities_df
            
        except Exception as e:
            logger.error(f"Error processing cities data: {e}")
            return pd.DataFrame()
    
    def get_florida_cities(self) -> List[str]:
        """
        Get a list of Florida cities from FDOT Open Data Hub
        
        Returns:
            List of city names
        """
        try:
            cities_df = self.get_cities_dataset()
            
            if not cities_df.empty and 'city_name' in cities_df.columns:
                cities = cities_df['city_name'].tolist()
                logger.info(f"Retrieved {len(cities)} Florida cities from FDOT Open Data Hub")
                return cities
            else:
                logger.warning("No cities data available from FDOT Open Data Hub, using comprehensive Florida cities list")
                # Comprehensive list of Florida cities as fallback
                florida_cities = [
                    # Palm Beach County
                    "West Palm Beach", "Boca Raton", "Delray Beach", "Boynton Beach", 
                    "Lake Worth", "Wellington", "Jupiter", "Palm Beach Gardens",
                    "Riviera Beach", "Greenacres", "Royal Palm Beach", "Lantana",
                    "Palm Springs", "Lake Park", "Hypoluxo", "Gulf Stream",
                    "Ocean Ridge", "Manalapan", "South Palm Beach", "Palm Beach",
                    "North Palm Beach", "Palm Beach Shores", "Tequesta", "Juno Beach",
                    
                    # Broward County
                    "Fort Lauderdale", "Hollywood", "Pompano Beach", "Coral Springs",
                    "Plantation", "Sunrise", "Tamarac", "Lauderhill", "Margate",
                    "Deerfield Beach", "Pembroke Pines", "Miramar", "Coconut Creek",
                    "North Lauderdale", "Oakland Park", "Wilton Manors", "Lauderdale Lakes",
                    "Cooper City", "Dania Beach", "Hallandale Beach", "Pembroke Park",
                    "Weston", "Davie", "Parkland", "Lighthouse Point", "Sea Ranch Lakes",
                    
                    # Miami-Dade County
                    "Miami", "Hialeah", "Miami Beach", "Coral Gables", "Miami Gardens",
                    "Aventura", "North Miami", "North Miami Beach", "Doral",
                    "Miami Lakes", "Hialeah Gardens", "Sweetwater", "Miami Springs",
                    "Cutler Bay", "Palmetto Bay", "Pinecrest", "Key Biscayne",
                    "Homestead", "Florida City", "South Miami", "West Miami",
                    "El Portal", "Virginia Gardens", "Medley", "Doral",
                    
                    # Monroe County
                    "Key West", "Marathon", "Key Largo", "Islamorada", "Big Pine Key",
                    "Tavernier", "Summerland Key", "Cudjoe Key", "Sugarloaf Key",
                    "Key Colony Beach", "Layton", "Ocean Reef", "Plantation Key",
                    
                    # Other Major Florida Cities
                    "Orlando", "Tampa", "Jacksonville", "St. Petersburg", "Gainesville",
                    "Tallahassee", "Fort Myers", "Sarasota", "Clearwater", "Lakeland",
                    "Cape Coral", "Port St. Lucie", "Naples", "Melbourne", "Daytona Beach",
                    "Pensacola", "Fort Pierce", "Kissimmee", "Bradenton", "Vero Beach",
                    "Panama City", "Ocala", "Gulfport", "St. Augustine", "Winter Haven"
                ]
                return florida_cities
                
        except Exception as e:
            logger.error(f"Error getting Florida cities: {e}")
            # Return comprehensive fallback list
            florida_cities = [
                "West Palm Beach", "Boca Raton", "Delray Beach", "Boynton Beach", 
                "Lake Worth", "Wellington", "Jupiter", "Palm Beach Gardens",
                "Fort Lauderdale", "Hollywood", "Pompano Beach", "Coral Springs",
                "Miami", "Hialeah", "Miami Beach", "Coral Gables", "Key West"
            ]
            return florida_cities
    
    def test_connection(self) -> bool:
        """
        Test the connection to FDOT Open Data Hub
        
        Returns:
            True if connection is successful
        """
        try:
            url = f"{self.base_url}/api/search/v1"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            logger.info("FDOT Open Data Hub connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"FDOT Open Data Hub connection test failed: {e}")
            return False

def test_fdot_opendata_api():
    """
    Test function for FDOT Open Data Hub API
    
    Returns:
        DataFrame with test results
    """
    try:
        api = FDOTOpenDataAPI()
        
        # Test connection
        if not api.test_connection():
            return pd.DataFrame()
        
        # Get cities
        cities = api.get_florida_cities()
        
        if cities:
            return pd.DataFrame({
                'city_name': cities,
                'source': 'FDOT Open Data Hub'
            })
        else:
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"FDOT Open Data Hub API test failed: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Test the API
    api = FDOTOpenDataAPI()
    
    print("Testing FDOT Open Data Hub API...")
    
    if api.test_connection():
        print("✅ Connection successful")
        
        cities = api.get_florida_cities()
        if cities:
            print(f"✅ Found {len(cities)} cities")
            print("Sample cities:", cities[:10])
        else:
            print("⚠️ No cities found")
    else:
        print("❌ Connection failed") 