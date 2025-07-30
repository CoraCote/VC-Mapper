"""
Utility functions for V/C Ratio Calculator
"""

import pandas as pd
import geopandas as gpd
import numpy as np
import requests
import json
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FDOTTrafficAPI:
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
    


class CapacityCalculator:
    """
    Class to handle roadway capacity calculations
    """
    
    def __init__(self):
        # Standard capacity values by functional classification
        self.capacity_table = {
            'Freeway': {
                'capacity_veh_day': 50000,
                'capacity_veh_hour': 2500,
                'lanes': 4
            },
            'Arterial': {
                'capacity_veh_day': 25000,
                'capacity_veh_hour': 1250,
                'lanes': 2
            },
            'Collector': {
                'capacity_veh_day': 15000,
                'capacity_veh_hour': 750,
                'lanes': 2
            },
            'Local': {
                'capacity_veh_day': 8000,
                'capacity_veh_hour': 400,
                'lanes': 1
            }
        }
    
    def get_capacity(self, functional_class: str, time_period: str = 'day') -> float:
        """
        Get capacity for a given functional classification
        
        Args:
            functional_class: Roadway functional classification
            time_period: 'day' or 'hour'
            
        Returns:
            Capacity value
        """
        if functional_class in self.capacity_table:
            key = f'capacity_veh_{time_period}'
            return self.capacity_table[functional_class].get(key, 0)
        return 0
    
    def calculate_vc_ratio(self, volume: float, capacity: float) -> float:
        """
        Calculate Volume/Capacity ratio
        
        Args:
            volume: Traffic volume
            capacity: Roadway capacity
            
        Returns:
            V/C ratio
        """
        return volume / capacity if capacity > 0 else 0
    
    def get_vc_status(self, vc_ratio: float) -> Tuple[str, str]:
        """
        Get status and color class for V/C ratio
        
        Args:
            vc_ratio: Volume/Capacity ratio
            
        Returns:
            Tuple of (status, color_class)
        """
        if vc_ratio < 0.7:
            return "Good", "status-good"
        elif vc_ratio < 0.9:
            return "Fair", "status-warning"
        elif vc_ratio <= 1.0:
            return "Poor", "status-danger"
        else:
            return "Critical", "status-critical"

class GrowthProjector:
    """
    Class to handle growth projections and TAZ-based calculations
    """
    
    def __init__(self):
        self.taz_growth_factors = {}
    
    def load_taz_growth_factors(self, file_path: str) -> bool:
        """
        Load TAZ-based growth factors from spreadsheet
        
        Args:
            file_path: Path to TAZ growth factors file
            
        Returns:
            Success status
        """
        try:
            # This would load the actual TAZ growth factors spreadsheet
            # For now, using placeholder data
            self.taz_growth_factors = {
                'TAZ_001': 0.025,
                'TAZ_002': 0.030,
                'TAZ_003': 0.020,
                # ... more TAZs
            }
            logger.info(f"Loaded TAZ growth factors from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading TAZ growth factors: {e}")
            return False
    
    def apply_uniform_growth(self, base_volume: float, growth_rate: float, years: int) -> float:
        """
        Apply uniform growth rate to base volume
        
        Args:
            base_volume: Base traffic volume
            growth_rate: Annual growth rate (decimal)
            years: Number of years to project
            
        Returns:
            Projected volume
        """
        return base_volume * (1 + growth_rate) ** years
    
    def apply_taz_growth(self, base_volume: float, taz_id: str, years: int) -> float:
        """
        Apply TAZ-specific growth rate to base volume
        
        Args:
            base_volume: Base traffic volume
            taz_id: TAZ identifier
            years: Number of years to project
            
        Returns:
            Projected volume
        """
        if taz_id in self.taz_growth_factors:
            growth_rate = self.taz_growth_factors[taz_id]
            return self.apply_uniform_growth(base_volume, growth_rate, years)
        else:
            # Default to 2% if TAZ not found
            return self.apply_uniform_growth(base_volume, 0.02, years)

class DataProcessor:
    """
    Class to handle data processing and validation
    """
    
    @staticmethod
    def validate_csv_upload(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate uploaded CSV file format
        
        Args:
            df: Uploaded DataFrame
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        required_columns = ['road_name', 'current_volume']
        
        # Check required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
        
        # Check data types
        if 'current_volume' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['current_volume']):
                errors.append("'current_volume' column must contain numeric values")
        
        # Check for negative volumes
        if 'current_volume' in df.columns and pd.api.types.is_numeric_dtype(df['current_volume']):
            if (df['current_volume'] < 0).any():
                errors.append("Traffic volumes cannot be negative")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def process_placer_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Process Placer.ai CSV data to standard format
        
        Args:
            df: Raw Placer.ai DataFrame
            
        Returns:
            Processed DataFrame
        """
        # Standardize column names
        column_mapping = {
            'Road Name': 'road_name',
            'Traffic Volume': 'current_volume',
            'Functional Class': 'functional_class',
            'Segment ID': 'segment_id'
        }
        
        # Rename columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        # Add missing columns with defaults
        if 'functional_class' not in df.columns:
            df['functional_class'] = 'Arterial'  # Default classification
        
        if 'segment_id' not in df.columns:
            df['segment_id'] = range(1, len(df) + 1)
        
        return df
    
    @staticmethod
    def create_geodataframe(df: pd.DataFrame, geometry_column: str = 'geometry') -> gpd.GeoDataFrame:
        """
        Convert DataFrame to GeoDataFrame
        
        Args:
            df: Input DataFrame
            geometry_column: Name of geometry column
            
        Returns:
            GeoDataFrame
        """
        if geometry_column in df.columns:
            # Convert geometry strings to shapely objects
            from shapely import wkt
            df[geometry_column] = df[geometry_column].apply(wkt.loads)
            return gpd.GeoDataFrame(df, geometry=geometry_column)
        else:
            # Create point geometries from lat/lon if available
            if 'latitude' in df.columns and 'longitude' in df.columns:
                from shapely.geometry import Point
                geometry = [Point(lon, lat) for lon, lat in zip(df['longitude'], df['latitude'])]
                return gpd.GeoDataFrame(df, geometry=geometry)
            else:
                # Return regular DataFrame if no geometry available
                return df

def calculate_summary_statistics(df: pd.DataFrame, vc_column: str = 'vc_ratio_future') -> Dict:
    """
    Calculate summary statistics for V/C ratios
    
    Args:
        df: DataFrame with V/C ratios
        vc_column: Column name containing V/C ratios
        
    Returns:
        Dictionary of summary statistics
    """
    if vc_column not in df.columns:
        return {}
    
    vc_ratios = df[vc_column]
    
    stats = {
        'total_segments': len(df),
        'mean_vc': vc_ratios.mean(),
        'median_vc': vc_ratios.median(),
        'std_vc': vc_ratios.std(),
        'min_vc': vc_ratios.min(),
        'max_vc': vc_ratios.max(),
        'good_segments': len(vc_ratios[vc_ratios < 0.7]),
        'fair_segments': len(vc_ratios[(vc_ratios >= 0.7) & (vc_ratios < 0.9)]),
        'poor_segments': len(vc_ratios[(vc_ratios >= 0.9) & (vc_ratios <= 1.0)]),
        'critical_segments': len(vc_ratios[vc_ratios > 1.0])
    }
    
    return stats 