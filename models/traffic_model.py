"""
Traffic Model - Data structures for real-time traffic volume and speed data
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TrafficData:
    """
    Model for individual traffic data point with volume and speed information
    """
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize traffic data from ArcGIS feature properties
        
        Args:
            data: Dictionary containing traffic data from ArcGIS API
        """
        # Extract properties from ArcGIS response
        properties = data.get('properties', {})
        geometry = data.get('geometry', {})
        
        # Basic identification
        self.objectid = properties.get('OBJECTID')
        self.segment_id = properties.get('SEGMENT_ID')
        self.roadway_name = properties.get('ROADWAY_NAME', 'Unknown')
        
        # Traffic volume data
        self.traffic_volume = properties.get('TRAFFIC_VOLUME', 0)
        self.volume_category = properties.get('VOLUME_CATEGORY', 'Unknown')
        
        # Speed data
        self.speed_limit = properties.get('SPEED_LIMIT', 0)
        self.average_speed = properties.get('AVERAGE_SPEED', 0)
        self.speed_ratio = properties.get('SPEED_RATIO', 0.0)
        
        # Time and direction information
        self.direction = properties.get('DIRECTION', 'Unknown')
        self.time_interval = properties.get('TIME_INTERVAL', 'Unknown')
        self.data_timestamp = properties.get('DATA_TIMESTAMP')
        
        # Location and geometry
        self.county = properties.get('COUNTY', 'Unknown')
        self.district = properties.get('DISTRICT', 'Unknown')
        self.geometry = geometry
        
        # Coordinates (extracted from geometry)
        self.coordinates = self._extract_coordinates(geometry)
        
        # Quality indicators
        self.data_quality = properties.get('DATA_QUALITY', 'Unknown')
        self.confidence_level = properties.get('CONFIDENCE_LEVEL', 0)
    
    def _extract_coordinates(self, geometry: Dict[str, Any]) -> Optional[List[List[float]]]:
        """
        Extract coordinates from geometry object
        
        Args:
            geometry: GeoJSON geometry object
            
        Returns:
            List of coordinate pairs or None if invalid
        """
        try:
            if geometry.get('type') == 'LineString':
                return geometry.get('coordinates', [])
            elif geometry.get('type') == 'MultiLineString':
                # Flatten MultiLineString coordinates
                coords = []
                for line in geometry.get('coordinates', []):
                    coords.extend(line)
                return coords
            else:
                return None
        except Exception as e:
            logger.warning(f"Error extracting coordinates: {e}")
            return None
    
    def get_start_point(self) -> Optional[tuple]:
        """Get the starting point of the traffic segment"""
        if self.coordinates and len(self.coordinates) > 0:
            return tuple(self.coordinates[0])
        return None
    
    def get_end_point(self) -> Optional[tuple]:
        """Get the ending point of the traffic segment"""
        if self.coordinates and len(self.coordinates) > 0:
            return tuple(self.coordinates[-1])
        return None
    
    def get_midpoint(self) -> Optional[tuple]:
        """Get the midpoint of the traffic segment"""
        if self.coordinates and len(self.coordinates) > 0:
            mid_idx = len(self.coordinates) // 2
            return tuple(self.coordinates[mid_idx])
        return None
    
    def get_traffic_level(self) -> str:
        """
        Categorize traffic level based on volume and speed ratio
        
        Returns:
            Traffic level category (Low, Moderate, High, Heavy)
        """
        if self.speed_ratio >= 0.8:
            return "Low"
        elif self.speed_ratio >= 0.6:
            return "Moderate"
        elif self.speed_ratio >= 0.4:
            return "High"
        else:
            return "Heavy"
    
    def get_color_by_traffic_level(self) -> List[int]:
        """
        Get color representation based on traffic level
        
        Returns:
            RGB color values [R, G, B, Alpha]
        """
        traffic_level = self.get_traffic_level()
        
        color_map = {
            "Low": [0, 255, 0, 180],      # Green
            "Moderate": [255, 255, 0, 180], # Yellow
            "High": [255, 165, 0, 180],    # Orange
            "Heavy": [255, 0, 0, 180]      # Red
        }
        
        return color_map.get(traffic_level, [128, 128, 128, 180])  # Gray default
    
    def get_line_width_by_volume(self) -> int:
        """
        Get line width based on traffic volume
        
        Returns:
            Line width for map visualization
        """
        if self.traffic_volume >= 50000:
            return 8
        elif self.traffic_volume >= 30000:
            return 6
        elif self.traffic_volume >= 15000:
            return 4
        elif self.traffic_volume >= 5000:
            return 3
        else:
            return 2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert traffic data to dictionary format"""
        return {
            'objectid': self.objectid,
            'segment_id': self.segment_id,
            'roadway_name': self.roadway_name,
            'traffic_volume': self.traffic_volume,
            'volume_category': self.volume_category,
            'speed_limit': self.speed_limit,
            'average_speed': self.average_speed,
            'speed_ratio': self.speed_ratio,
            'direction': self.direction,
            'time_interval': self.time_interval,
            'data_timestamp': self.data_timestamp,
            'county': self.county,
            'district': self.district,
            'coordinates': self.coordinates,
            'traffic_level': self.get_traffic_level(),
            'data_quality': self.data_quality,
            'confidence_level': self.confidence_level
        }
    
    def __str__(self) -> str:
        """String representation of traffic data"""
        return (f"TrafficData(roadway={self.roadway_name}, "
                f"volume={self.traffic_volume}, "
                f"avg_speed={self.average_speed}, "
                f"level={self.get_traffic_level()})")


class TrafficCollection:
    """
    Collection class for managing multiple traffic data points
    """
    
    def __init__(self):
        """Initialize empty traffic collection"""
        self.traffic_data: List[TrafficData] = []
        self.last_updated: Optional[str] = None
        self.total_segments: int = 0
    
    def add_traffic_data(self, traffic_data: TrafficData) -> None:
        """
        Add traffic data to collection
        
        Args:
            traffic_data: TrafficData instance to add
        """
        self.traffic_data.append(traffic_data)
        self.total_segments = len(self.traffic_data)
    
    def get_traffic_by_county(self, county: str) -> List[TrafficData]:
        """
        Get traffic data filtered by county
        
        Args:
            county: County name to filter by
            
        Returns:
            List of traffic data for specified county
        """
        return [data for data in self.traffic_data if data.county.lower() == county.lower()]
    
    def get_traffic_by_roadway(self, roadway_name: str) -> List[TrafficData]:
        """
        Get traffic data filtered by roadway name
        
        Args:
            roadway_name: Roadway name to filter by
            
        Returns:
            List of traffic data for specified roadway
        """
        return [data for data in self.traffic_data 
                if roadway_name.lower() in data.roadway_name.lower()]
    
    def get_traffic_by_level(self, traffic_level: str) -> List[TrafficData]:
        """
        Get traffic data filtered by traffic level
        
        Args:
            traffic_level: Traffic level to filter by (Low, Moderate, High, Heavy)
            
        Returns:
            List of traffic data for specified level
        """
        return [data for data in self.traffic_data 
                if data.get_traffic_level() == traffic_level]
    
    def get_high_traffic_segments(self, threshold: int = 30000) -> List[TrafficData]:
        """
        Get segments with high traffic volume
        
        Args:
            threshold: Volume threshold for high traffic
            
        Returns:
            List of high traffic segments
        """
        return [data for data in self.traffic_data if data.traffic_volume >= threshold]
    
    def get_congested_segments(self, speed_ratio_threshold: float = 0.5) -> List[TrafficData]:
        """
        Get congested segments based on speed ratio
        
        Args:
            speed_ratio_threshold: Speed ratio threshold for congestion
            
        Returns:
            List of congested segments
        """
        return [data for data in self.traffic_data if data.speed_ratio <= speed_ratio_threshold]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get traffic collection statistics
        
        Returns:
            Dictionary containing collection statistics
        """
        if not self.traffic_data:
            return {
                'total_segments': 0,
                'avg_volume': 0,
                'avg_speed': 0,
                'traffic_levels': {'Low': 0, 'Moderate': 0, 'High': 0, 'Heavy': 0}
            }
        
        total_volume = sum(data.traffic_volume for data in self.traffic_data)
        total_speed = sum(data.average_speed for data in self.traffic_data)
        
        # Count traffic levels
        level_counts = {'Low': 0, 'Moderate': 0, 'High': 0, 'Heavy': 0}
        for data in self.traffic_data:
            level_counts[data.get_traffic_level()] += 1
        
        return {
            'total_segments': len(self.traffic_data),
            'avg_volume': total_volume / len(self.traffic_data),
            'avg_speed': total_speed / len(self.traffic_data),
            'total_volume': total_volume,
            'traffic_levels': level_counts,
            'last_updated': self.last_updated
        }
    
    def get_unique_counties(self) -> List[str]:
        """Get list of unique counties in the collection"""
        counties = set(data.county for data in self.traffic_data if data.county != 'Unknown')
        return sorted(list(counties))
    
    def get_unique_roadways(self) -> List[str]:
        """Get list of unique roadways in the collection"""
        roadways = set(data.roadway_name for data in self.traffic_data if data.roadway_name != 'Unknown')
        return sorted(list(roadways))
    
    def to_geojson(self) -> Dict[str, Any]:
        """
        Convert traffic collection to GeoJSON format for map visualization
        
        Returns:
            GeoJSON FeatureCollection
        """
        features = []
        
        for data in self.traffic_data:
            if data.coordinates:
                feature = {
                    "type": "Feature",
                    "geometry": data.geometry,
                    "properties": data.to_dict()
                }
                features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    def __len__(self) -> int:
        """Return number of traffic data points"""
        return len(self.traffic_data)
    
    def __iter__(self):
        """Iterator for traffic data"""
        return iter(self.traffic_data)
    
    def __str__(self) -> str:
        """String representation of traffic collection"""
        stats = self.get_statistics()
        return (f"TrafficCollection(segments={stats['total_segments']}, "
                f"avg_volume={stats['avg_volume']:.0f}, "
                f"avg_speed={stats['avg_speed']:.1f})")