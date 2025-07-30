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
    Class to handle FDOT Traffic Online API interactions
    """
    
    def __init__(self, base_url: str = "https://tdaappsprod.dot.state.fl.us/fto/"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_traffic_data(self, county: str, year: int = 2023) -> pd.DataFrame:
        """
        Fetch traffic data from FDOT Traffic Online for a specific county
        
        Args:
            county: County name
            year: Year of traffic data
            
        Returns:
            DataFrame with traffic volume data
        """
        try:
            # This is a placeholder implementation
            # In real implementation, you would:
            # 1. Authenticate with FDOT API
            # 2. Query the appropriate endpoints
            # 3. Parse the response
            
            logger.info(f"Fetching traffic data for {county} county, year {year}")
            
            # Placeholder response structure
            sample_data = {
                'segment_id': range(1, 51),
                'road_name': [f"{county} Road {i}" for i in range(1, 51)],
                'functional_class': ['Arterial'] * 20 + ['Collector'] * 20 + ['Local'] * 10,
                'current_volume': np.random.randint(2000, 30000, 50),
                'geometry': [f"POINT({-80.1 + i*0.005} {26.7 + i*0.005})" for i in range(50)],
                'county': [county] * 50,
                'year': [year] * 50
            }
            
            return pd.DataFrame(sample_data)
            
        except Exception as e:
            logger.error(f"Error fetching FDOT traffic data: {e}")
            return pd.DataFrame()

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