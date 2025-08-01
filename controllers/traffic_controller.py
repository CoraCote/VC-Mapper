"""
Traffic Controller - Handles fetching and managing FDOT Annual Average Daily Traffic (AADT) data
"""

import requests
import logging
import streamlit as st
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

from models.traffic_model import TrafficData, TrafficCollection

logger = logging.getLogger(__name__)


class TrafficController:
    """
    Controller for managing FDOT Annual Average Daily Traffic (AADT) data from FDOT GIS services
    """
    
    def __init__(self):
        """Initialize the traffic controller with FDOT AADT service configuration"""
        self.base_url = "https://services1.arcgis.com/O1JpcwDW8sjYuddV/arcgis/rest/services/Annual_Average_Daily_Traffic_TDA/FeatureServer/0/query"
        self.default_params = {
            'outFields': '*',
            'where': '1=1',
            'f': 'geojson',
            'returnGeometry': 'true'
        }
        self.cache_duration = 300  # 5 minutes cache
        self._last_fetch_time = None
        self._cached_data = None
    
    def fetch_traffic_data(self, 
                          county_filter: Optional[str] = None,
                          roadway_filter: Optional[str] = None,
                          max_records: Optional[int] = None,
                          use_cache: bool = True,
                          most_recent_only: bool = True) -> Optional[TrafficCollection]:
        """
        Fetch FDOT Annual Average Daily Traffic (AADT) data from FDOT GIS service
        
        Args:
            county_filter: Optional county name to filter results
            roadway_filter: Optional roadway description to filter results  
            max_records: Maximum number of records to fetch
            use_cache: Whether to use cached data if available
            most_recent_only: Whether to fetch only the most recent year of data
            
        Returns:
            TrafficCollection with fetched AADT data or None if error
        """
        try:
            # Check cache first
            if use_cache and self._is_cache_valid():
                logger.info("Using cached traffic data")
                return self._cached_data
            
            # Get the most recent year available if requested
            most_recent_year = None
            if most_recent_only:
                most_recent_year = self._get_most_recent_year()
                if most_recent_year:
                    logger.info(f"Fetching most recent AADT data for year: {most_recent_year}")
                else:
                    logger.warning("Could not determine most recent year, fetching all available data")
            
            # Build query parameters
            params = self.default_params.copy()
            # Only set record count if max_records is specified
            if max_records is not None:
                params['resultRecordCount'] = max_records
            
            # Add filters if specified
            where_clauses = ['1=1']
            
            # Filter by most recent year if available
            if most_recent_year:
                where_clauses.append(f"YEAR_ = {most_recent_year}")
            
            if county_filter:
                where_clauses.append(f"COUNTY LIKE '%{county_filter}%'")
            
            if roadway_filter:
                # Filter on both description fields for better coverage
                where_clauses.append(f"(DESC_FRM LIKE '%{roadway_filter}%' OR DESC_TO LIKE '%{roadway_filter}%')")
            
            params['where'] = ' AND '.join(where_clauses)
            
            logger.info(f"Fetching FDOT AADT data with params: {params}")
            
            # Make API request with timeout and error handling
            response = requests.get(
                self.base_url, 
                params=params, 
                timeout=30,
                headers={'User-Agent': 'VC-Mapper-FDOT-AADT/1.0'}
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Parse response into TrafficCollection
            traffic_collection = self._parse_traffic_response(data)
            
            # Update cache
            self._cached_data = traffic_collection
            self._last_fetch_time = datetime.now()
            
            # Log year information
            if traffic_collection and len(traffic_collection) > 0:
                years_in_data = set(td.year for td in traffic_collection.traffic_data)
                logger.info(f"Successfully fetched {len(traffic_collection)} traffic segments from years: {sorted(years_in_data)}")
            
            return traffic_collection
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching traffic data: {e}")
            self._handle_fetch_error("Network error", str(e))
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            self._handle_fetch_error("Data parsing error", str(e))
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error fetching traffic data: {e}")
            self._handle_fetch_error("Unexpected error", str(e))
            return None
    
    def _parse_traffic_response(self, data: Dict[str, Any]) -> TrafficCollection:
        """
        Parse FDOT GIS API response into TrafficCollection
        
        Args:
            data: Raw GeoJSON response data from FDOT GIS API
            
        Returns:
            TrafficCollection with parsed AADT data
        """
        traffic_collection = TrafficCollection()
        
        try:
            features = data.get('features', [])
            
            for feature in features:
                try:
                    # Create TrafficData from feature
                    traffic_data = TrafficData(feature)
                    traffic_collection.add_traffic_data(traffic_data)
                    
                except Exception as e:
                    logger.warning(f"Error parsing traffic feature: {e}")
                    continue
            
            # Set collection metadata
            traffic_collection.last_updated = datetime.now().isoformat()
            
            logger.info(f"Parsed {len(traffic_collection)} traffic segments successfully")
            
        except Exception as e:
            logger.error(f"Error parsing traffic response: {e}")
            raise
        
        return traffic_collection
    
    def _get_most_recent_year(self) -> Optional[int]:
        """
        Get the most recent year available in the FDOT AADT data
        
        Returns:
            Most recent year as integer, or None if unable to determine
        """
        try:
            # Query for distinct years to find the most recent
            params = {
                'where': '1=1',
                'returnDistinctValues': 'true',
                'outFields': 'YEAR_',
                'f': 'json'
            }
            
            response = requests.get(
                self.base_url, 
                params=params, 
                timeout=15,
                headers={'User-Agent': 'VC-Mapper-FDOT-AADT/1.0'}
            )
            
            response.raise_for_status()
            data = response.json()
            
            if 'features' in data:
                years = []
                for feature in data['features']:
                    year_val = feature['attributes']['YEAR_']
                    if year_val and isinstance(year_val, int):
                        years.append(year_val)
                
                if years:
                    most_recent = max(years)
                    logger.info(f"Found {len(years)} distinct years in AADT data. Most recent: {most_recent}")
                    return most_recent
                    
        except Exception as e:
            logger.warning(f"Could not determine most recent year: {e}")
            
        return None
    
    def _is_cache_valid(self) -> bool:
        """
        Check if cached data is still valid
        
        Returns:
            True if cache is valid, False otherwise
        """
        if not self._last_fetch_time or not self._cached_data:
            return False
        
        time_diff = datetime.now() - self._last_fetch_time
        return time_diff.total_seconds() < self.cache_duration
    
    def _handle_fetch_error(self, error_type: str, error_message: str) -> None:
        """
        Handle fetch errors with user-friendly messages
        
        Args:
            error_type: Type of error
            error_message: Detailed error message
        """
        st.error(f"❌ {error_type} while fetching traffic data")
        
        with st.expander("🔧 Error Details"):
            st.write(f"**Error Type:** {error_type}")
            st.write(f"**Details:** {error_message}")
            st.write(f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.write("**Suggestions:**")
            st.write("- Check your internet connection")
            st.write("- Try reducing the number of records")
            st.write("- The service might be temporarily unavailable")
    
    def get_traffic_statistics(self, traffic_collection: TrafficCollection) -> Dict[str, Any]:
        """
        Get comprehensive traffic statistics
        
        Args:
            traffic_collection: TrafficCollection to analyze
            
        Returns:
            Dictionary with traffic statistics
        """
        if not traffic_collection or len(traffic_collection) == 0:
            return {}
        
        base_stats = traffic_collection.get_statistics()
        
        # Additional statistics
        volumes = [data.aadt for data in traffic_collection.traffic_data]
        speeds = [data.average_speed for data in traffic_collection.traffic_data]
        speed_ratios = [data.speed_ratio for data in traffic_collection.traffic_data]
        
        enhanced_stats = {
            **base_stats,
            'volume_stats': {
                'min': min(volumes) if volumes else 0,
                'max': max(volumes) if volumes else 0,
                'median': sorted(volumes)[len(volumes)//2] if volumes else 0
            },
            'speed_stats': {
                'min': min(speeds) if speeds else 0,
                'max': max(speeds) if speeds else 0,
                'median': sorted(speeds)[len(speeds)//2] if speeds else 0
            },
            'congestion_stats': {
                'avg_speed_ratio': sum(speed_ratios) / len(speed_ratios) if speed_ratios else 0,
                'congested_segments': len([r for r in speed_ratios if r < 0.5]),
                'free_flow_segments': len([r for r in speed_ratios if r > 0.8])
            }
        }
        
        return enhanced_stats
    
    def get_session_traffic_data(self) -> Optional[TrafficCollection]:
        """
        Get traffic data from Streamlit session state
        
        Returns:
            TrafficCollection from session or None
        """
        if 'traffic_data' in st.session_state:
            return st.session_state.traffic_data
        return None
    
    def save_traffic_data_to_session(self, traffic_collection: TrafficCollection) -> None:
        """
        Save traffic data to Streamlit session state
        
        Args:
            traffic_collection: TrafficCollection to save
        """
        st.session_state.traffic_data = traffic_collection
        logger.info(f"Saved {len(traffic_collection)} traffic segments to session")
    
    def clear_traffic_data_from_session(self) -> None:
        """Clear traffic data from session state"""
        if 'traffic_data' in st.session_state:
            del st.session_state.traffic_data
            logger.info("Cleared traffic data from session")
    
    def fetch_and_cache_traffic_data(self, 
                                   county_filter: Optional[str] = None,
                                   roadway_filter: Optional[str] = None,
                                   max_records: Optional[int] = None,
                                   force_refresh: bool = False) -> Optional[TrafficCollection]:
        """
        Fetch traffic data and cache it in session state
        
        Args:
            county_filter: Optional county name to filter results
            roadway_filter: Optional roadway name to filter results
            max_records: Maximum number of records to fetch
            force_refresh: Force refresh of cached data
            
        Returns:
            TrafficCollection with fetched data or None if error
        """
        # Check session cache first unless force refresh
        if not force_refresh:
            session_data = self.get_session_traffic_data()
            if session_data and self._is_cache_valid():
                return session_data
        
        # Fetch new data (always fetch most recent data by default)
        traffic_collection = self.fetch_traffic_data(
            county_filter=county_filter,
            roadway_filter=roadway_filter,
            max_records=max_records,
            use_cache=not force_refresh,
            most_recent_only=True
        )
        
        # Save to session if successful
        if traffic_collection:
            self.save_traffic_data_to_session(traffic_collection)
        
        return traffic_collection
    
    def get_filtered_traffic_data(self, 
                                 traffic_collection: TrafficCollection,
                                 filters: Dict[str, Any]) -> TrafficCollection:
        """
        Apply filters to traffic collection
        
        Args:
            traffic_collection: Original traffic collection
            filters: Dictionary of filter criteria
            
        Returns:
            Filtered TrafficCollection
        """
        filtered_collection = TrafficCollection()
        
        for traffic_data in traffic_collection.traffic_data:
            include = True
            
            # County filter
            if filters.get('county') and filters['county'] != 'All':
                if traffic_data.county.lower() != filters['county'].lower():
                    include = False
            
            # Roadway filter (check both description fields)
            if filters.get('roadway') and filters['roadway'] != 'All':
                roadway_match = (filters['roadway'].lower() in traffic_data.roadway_name.lower() or
                               filters['roadway'].lower() in traffic_data.desc_from.lower() or
                               filters['roadway'].lower() in traffic_data.desc_to.lower())
                if not roadway_match:
                    include = False
            
            # Traffic level filter
            if filters.get('traffic_level') and filters['traffic_level'] != 'All':
                if traffic_data.get_traffic_level() != filters['traffic_level']:
                    include = False
            
            # AADT volume range filter
            if filters.get('min_volume') is not None:
                if traffic_data.aadt < filters['min_volume']:
                    include = False
            
            if filters.get('max_volume') is not None:
                if traffic_data.aadt > filters['max_volume']:
                    include = False
            
            # Speed ratio filter
            if filters.get('min_speed_ratio') is not None:
                if traffic_data.speed_ratio < filters['min_speed_ratio']:
                    include = False
            
            if include:
                filtered_collection.add_traffic_data(traffic_data)
        
        return filtered_collection
    
    def export_traffic_data(self, 
                           traffic_collection: TrafficCollection,
                           format_type: str = 'geojson') -> str:
        """
        Export traffic data in specified format
        
        Args:
            traffic_collection: TrafficCollection to export
            format_type: Export format ('geojson', 'json', 'csv')
            
        Returns:
            Exported data as string
        """
        try:
            if format_type.lower() == 'geojson':
                return json.dumps(traffic_collection.to_geojson(), indent=2)
            
            elif format_type.lower() == 'json':
                data = [traffic_data.to_dict() for traffic_data in traffic_collection.traffic_data]
                return json.dumps(data, indent=2)
            
            elif format_type.lower() == 'csv':
                # Convert to CSV format
                import csv
                import io
                
                output = io.StringIO()
                
                if traffic_collection.traffic_data:
                    fieldnames = traffic_collection.traffic_data[0].to_dict().keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for traffic_data in traffic_collection.traffic_data:
                        # Handle coordinate serialization for CSV
                        row = traffic_data.to_dict()
                        row['coordinates'] = str(row['coordinates'])
                        writer.writerow(row)
                
                return output.getvalue()
            
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            logger.error(f"Error exporting traffic data: {e}")
            raise