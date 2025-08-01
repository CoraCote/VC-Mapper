"""
Street Model - Handles street data structures and operations
"""

from typing import List, Dict, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class Street:
    """
    Street data model
    """
    
    def __init__(self, data: Dict):
        """
        Initialize a Street object with data from API
        
        Args:
            data: Dictionary containing street data
        """
        self.street_id = data.get('street_id')
        self.street_name = data.get('street_name', 'Unnamed Street')
        self.road_number = data.get('road_number', 'N/A')
        self.highway_type = data.get('highway_type', 'unknown')
        self.geometry = data.get('geometry', {})
        self.lanes = data.get('lanes')
        self.maxspeed = data.get('maxspeed')
        self.surface = data.get('surface')
        self.traffic_volume = data.get('traffic_volume', 0)
        self.traffic_level = data.get('traffic_level', 'unknown')
        self.length = data.get('length', 0)
        self.lane_count = data.get('lane_count', 'N/A')
        self.speed_limit = data.get('speed_limit', 'N/A')
        self.county = data.get('county', 'N/A')
        self.surface_type = data.get('surface_type', 'N/A')
        self.functional_class = data.get('functional_class', 'N/A')
        self.raw_tags = data.get('raw_tags', {})
    
    def to_dict(self) -> Dict:
        """Convert street object back to dictionary"""
        return {
            'street_id': self.street_id,
            'street_name': self.street_name,
            'road_number': self.road_number,
            'highway_type': self.highway_type,
            'geometry': self.geometry,
            'lanes': self.lanes,
            'maxspeed': self.maxspeed,
            'surface': self.surface,
            'traffic_volume': self.traffic_volume,
            'traffic_level': self.traffic_level,
            'length': self.length,
            'lane_count': self.lane_count,
            'speed_limit': self.speed_limit,
            'county': self.county,
            'surface_type': self.surface_type,
            'functional_class': self.functional_class,
            'raw_tags': self.raw_tags
        }
    
    def has_valid_geometry(self) -> bool:
        """Check if street has valid geometry"""
        return (self.geometry and 
                self.geometry.get('type') in ['LineString', 'MultiLineString'] and
                self.geometry.get('coordinates'))
    
    def get_display_name(self) -> str:
        """Get formatted display name"""
        if self.road_number and self.road_number != 'N/A':
            return f"{self.street_name} ({self.road_number})"
        return self.street_name
    
    def get_traffic_color(self) -> str:
        """Get color based on traffic level"""
        traffic_colors = {
            'very_high': '#FF0000',  # Red
            'high': '#FF6600',       # Orange
            'medium': '#FFFF00',     # Yellow
            'low': '#66FF00',        # Light Green
            'very_low': '#00FF00',   # Green
            'unknown': '#808080'     # Gray
        }
        return traffic_colors.get(self.traffic_level, '#808080')
    
    def get_traffic_level_display(self) -> str:
        """Get formatted traffic level for display"""
        return self.traffic_level.replace('_', ' ').title()
    
    def get_folium_coordinates(self) -> List[List[float]]:
        """Convert coordinates to folium format (lat, lng)"""
        if not self.has_valid_geometry():
            return []
        
        coords = []
        geometry_type = self.geometry.get('type')
        
        if geometry_type == 'LineString':
            coordinates = self.geometry.get('coordinates', [])
            coords = [[coord[1], coord[0]] for coord in coordinates]  # Swap x,y to lat,lng
        elif geometry_type == 'MultiLineString':
            coordinate_arrays = self.geometry.get('coordinates', [])
            coords = []
            for line_coords in coordinate_arrays:
                if line_coords:
                    coords.append([[coord[1], coord[0]] for coord in line_coords])
        
        return coords
    
    def create_popup_html(self) -> str:
        """Create HTML popup content for map display"""
        return f"""
        <div style="font-family: Arial, sans-serif; width: 250px;">
            <h4 style="margin: 0 0 8px 0; color: #333;">{self.street_name}</h4>
            <p style="margin: 2px 0;"><strong>Type:</strong> {self.highway_type.replace('_', ' ').title()}</p>
            <p style="margin: 2px 0;"><strong>Road Number:</strong> {self.road_number}</p>
            <p style="margin: 2px 0;"><strong>Traffic Volume:</strong> {self.traffic_volume:,}/day</p>
            <p style="margin: 2px 0;"><strong>Traffic Level:</strong> {self.get_traffic_level_display()}</p>
            <p style="margin: 2px 0;"><strong>Length:</strong> {self.length:.2f} units</p>
            <p style="margin: 2px 0;"><strong>Lanes:</strong> {self.lanes or self.lane_count}</p>
            <p style="margin: 2px 0;"><strong>Speed Limit:</strong> {self.maxspeed or self.speed_limit} mph</p>
            <p style="margin: 2px 0;"><strong>Surface:</strong> {self.surface or self.surface_type}</p>
            <p style="margin: 2px 0;"><strong>County:</strong> {self.county}</p>
        </div>
        """


class StreetCollection:
    """
    Collection of streets with utility methods
    """
    
    def __init__(self, streets_data: List[Dict] = None):
        """
        Initialize collection with street data
        
        Args:
            streets_data: List of street dictionaries
        """
        self.streets = []
        if streets_data:
            self.streets = [Street(data) for data in streets_data]
    
    def add_street(self, street_data: Dict):
        """Add a street to the collection"""
        self.streets.append(Street(street_data))
    
    def get_valid_streets(self) -> List[Street]:
        """Get streets with valid geometry"""
        return [street for street in self.streets if street.has_valid_geometry()]
    
    def get_streets_as_dict_list(self) -> List[Dict]:
        """Get all streets as list of dictionaries"""
        return [street.to_dict() for street in self.streets]
    
    def filter_by_name(self, search_term: str) -> List[Street]:
        """Filter streets by name"""
        if not search_term:
            return self.streets
        return [street for street in self.streets 
                if search_term.lower() in street.street_name.lower()]
    
    def filter_by_traffic_level(self, traffic_level: str) -> List[Street]:
        """Filter streets by traffic level"""
        if traffic_level == "All":
            return self.streets
        return [street for street in self.streets 
                if street.get_traffic_level_display() == traffic_level]
    
    def sort_streets(self, sort_by: str, reverse: bool = False) -> List[Street]:
        """Sort streets by specified field"""
        sort_mapping = {
            "Street Name": lambda x: x.street_name,
            "Traffic Volume": lambda x: x.traffic_volume,
            "Length": lambda x: x.length,
            "Speed Limit": lambda x: self._extract_speed_limit(x)
        }
        
        sort_func = sort_mapping.get(sort_by, sort_mapping["Street Name"])
        return sorted(self.streets, key=sort_func, reverse=reverse)
    
    def _extract_speed_limit(self, street: Street) -> float:
        """Extract numeric speed limit for sorting"""
        try:
            speed = street.speed_limit or street.maxspeed or '0'
            if isinstance(speed, str):
                import re
                match = re.search(r'\d+', speed)
                return float(match.group()) if match else 0
            return float(speed)
        except (ValueError, AttributeError):
            return 0
    
    def get_traffic_distribution(self) -> Dict[str, int]:
        """Get distribution of streets by traffic level"""
        distribution = {}
        for street in self.streets:
            level = street.get_traffic_level_display()
            distribution[level] = distribution.get(level, 0) + 1
        return distribution
    
    def get_total_traffic_volume(self) -> int:
        """Get total traffic volume of all streets"""
        return sum(street.traffic_volume for street in self.streets)
    
    def get_average_traffic_volume(self) -> float:
        """Get average traffic volume"""
        if not self.streets:
            return 0
        return self.get_total_traffic_volume() / len(self.streets)
    
    def get_total_length(self) -> float:
        """Get total length of all streets"""
        return sum(street.length for street in self.streets)
    
    def get_unique_traffic_levels(self) -> List[str]:
        """Get unique traffic levels for filtering"""
        levels = set(street.get_traffic_level_display() for street in self.streets)
        return sorted(list(levels))
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert collection to pandas DataFrame"""
        data = []
        for street in self.streets:
            data.append({
                'Street Name': street.street_name,
                'Road Number': street.road_number,
                'Traffic Volume': f"{street.traffic_volume:,}",
                'Traffic Level': street.get_traffic_level_display(),
                'Length': f"{street.length:.2f}",
                'Lanes': street.lanes or street.lane_count,
                'Speed Limit': f"{street.maxspeed or street.speed_limit} mph" if (street.maxspeed or street.speed_limit) else 'N/A',
                'County': street.county,
                'Surface Type': street.surface or street.surface_type,
                'Functional Class': street.functional_class
            })
        
        return pd.DataFrame(data)
    
    def __len__(self) -> int:
        """Return number of streets in collection"""
        return len(self.streets)
    
    def __iter__(self):
        """Make collection iterable"""
        return iter(self.streets)
    
    def __getitem__(self, index):
        """Make collection indexable"""
        return self.streets[index]