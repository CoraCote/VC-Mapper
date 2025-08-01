"""
Florida Boundary Service - Fetches real Florida state boundary data from ArcGIS API
"""

import requests
import logging
from typing import Dict, Optional, List
import json

logger = logging.getLogger(__name__)


class FloridaBoundaryService:
    """
    Service to fetch Florida state boundary data from ArcGIS API
    """
    
    def __init__(self):
        """Initialize the Florida boundary service"""
        self.api_url = "https://services1.arcgis.com/O1JpcwDW8sjYuddV/arcgis/rest/services/Florida_County_Boundaries_with_FDOT_Districts/FeatureServer/13/query"
        self.default_params = {
            'outFields': '*',
            'where': '1=1',
            'f': 'geojson'
        }
    
    def fetch_florida_boundary(self) -> Optional[Dict]:
        """
        Fetch Florida state boundary data from ArcGIS API
        
        Returns:
            Dictionary containing GeoJSON data or None if error occurs
        """
        try:
            logger.info("Fetching Florida boundary data from ArcGIS API...")
            
            response = requests.get(
                self.api_url,
                params=self.default_params,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Parse the JSON response
            boundary_data = response.json()
            
            if not boundary_data or 'features' not in boundary_data:
                logger.error("Invalid response format from ArcGIS API")
                return None
            
            # Process the boundary data
            processed_data = self._process_boundary_data(boundary_data)
            
            logger.info(f"Successfully fetched Florida boundary data with {len(processed_data['features'])} features")
            return processed_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching Florida boundary data: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching Florida boundary data: {e}")
            return None
    
    def _process_boundary_data(self, raw_data: Dict) -> Dict:
        """
        Process the raw boundary data from ArcGIS API
        
        Args:
            raw_data: Raw GeoJSON data from API
            
        Returns:
            Processed GeoJSON data suitable for mapping
        """
        try:
            processed_features = []
            
            for feature in raw_data.get('features', []):
                # Extract geometry and properties
                geometry = feature.get('geometry', {})
                properties = feature.get('properties', {})
                
                # Create a processed feature
                processed_feature = {
                    "type": "Feature",
                    "properties": {
                        "name": properties.get('NAME', 'Florida County'),
                        "county": properties.get('COUNTY', 'Unknown'),
                        "district": properties.get('DISTRICT', 'Unknown'),
                        "objectid": properties.get('OBJECTID', 0)
                    },
                    "geometry": geometry
                }
                
                processed_features.append(processed_feature)
            
            # Create the final GeoJSON structure
            processed_data = {
                "type": "FeatureCollection",
                "features": processed_features
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing boundary data: {e}")
            return raw_data  # Return original data if processing fails
    
    def get_combined_florida_boundary(self) -> Optional[Dict]:
        """
        Get a combined Florida state boundary (union of all counties)
        
        Returns:
            Simplified GeoJSON with single Florida boundary or None if error
        """
        try:
            # Fetch the detailed boundary data
            detailed_data = self.fetch_florida_boundary()
            
            if not detailed_data:
                return None
            
            # For now, return the detailed data
            # In a production environment, you might want to use a geometry library
            # like Shapely to combine all county boundaries into a single state boundary
            return detailed_data
            
        except Exception as e:
            logger.error(f"Error creating combined Florida boundary: {e}")
            return None
    
    def validate_boundary_data(self, boundary_data: Dict) -> bool:
        """
        Validate the boundary data structure
        
        Args:
            boundary_data: GeoJSON data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not boundary_data:
                return False
            
            if boundary_data.get('type') != 'FeatureCollection':
                return False
            
            features = boundary_data.get('features', [])
            if not features:
                return False
            
            # Check if at least one feature has valid geometry
            for feature in features:
                geometry = feature.get('geometry', {})
                if geometry and geometry.get('type') and geometry.get('coordinates'):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating boundary data: {e}")
            return False


# Global instance for easy access
florida_boundary_service = FloridaBoundaryService()