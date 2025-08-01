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
        Initialize traffic data from FDOT AADT GeoJSON feature
        
        Args:
            data: Dictionary containing traffic data from FDOT API (GeoJSON Feature format)
        """
        # Extract properties from GeoJSON response
        properties = data.get('properties', {})
        geometry = data.get('geometry', {})
        
        # Basic identification
        self.fid = properties.get('FID')
        self.objectid = self.fid  # For backward compatibility
        self.segment_id = f"{properties.get('ROADWAY', '')}-{properties.get('BEGIN_POST', 0)}-{properties.get('END_POST', 0)}"
        self.roadway_code = properties.get('ROADWAY', 'Unknown')
        self.roadway_name = f"{properties.get('DESC_FRM', '')} to {properties.get('DESC_TO', '')}"
        
        # FDOT specific fields
        self.year = properties.get('YEAR_', 2024)
        self.district = properties.get('DISTRICT', 'Unknown')
        self.cosite = properties.get('COSITE', 'Unknown')
        self.desc_from = properties.get('DESC_FRM', 'Unknown')
        self.desc_to = properties.get('DESC_TO', 'Unknown')
        
        # Traffic volume data (AADT = Annual Average Daily Traffic)
        self.aadt = properties.get('AADT', 0)
        self.traffic_volume = self.aadt  # For backward compatibility
        self.aadt_flag = properties.get('AADTFLG', 'Unknown')
        
        # Factor data for traffic analysis
        self.k_factor = properties.get('KFCTR', 0)  # Design hour factor
        self.k100_factor = properties.get('K100FCTR', 0)  # 100th hour factor
        self.d_factor = properties.get('DFCTR', 0)  # Directional factor
        self.t_factor = properties.get('TFCTR', 0)  # Truck factor
        
        # Flags for data quality
        self.k_flag = properties.get('KFLG', 'Unknown')
        self.k100_flag = properties.get('K100FLG', 'Unknown') 
        self.d_flag = properties.get('DFLG', 'Unknown')
        self.t_flag = properties.get('TFLG', 'Unknown')
        
        # Location information  
        self.county_dot = properties.get('COUNTYDOT', 'Unknown')
        self.county = properties.get('COUNTY', 'Unknown')
        self.mng_district = properties.get('MNG_DIST', 'Unknown')
        
        # Additional location data that might be missing
        if self.county == 'Unknown':
            # Try alternate county field names
            self.county = properties.get('COUNTY_DESC', properties.get('COUNTY_NAME', 'Unknown'))
        
        # Additional FDOT service fields that may not be in user's sample
        self.truck_per = properties.get('TRUCK_PER', 0)  # % of truck traffic per day
        self.tfctr_copy = properties.get('TFCTR_copy', 0)  # % truck volume per day
        
        # Milepost information
        self.begin_post = properties.get('BEGIN_POST', 0)
        self.end_post = properties.get('END_POST', 0)
        
        # Geometry and shape
        self.geometry = geometry
        self.shape_length = properties.get('Shape_Leng', 0)
        
        # Coordinates (extracted from geometry)
        self.coordinates = self._extract_coordinates(geometry)
        
        # Calculated fields for compatibility with existing code
        self.speed_limit = 0  # Not available in AADT data
        self.average_speed = 0  # Not available in AADT data  
        self.speed_ratio = 1.0  # Default to free flow
        self.direction = 'Both'  # AADT is typically bidirectional
        self.time_interval = 'Annual'
        self.data_timestamp = f"{self.year}-01-01"
        self.volume_category = self._categorize_aadt_volume()
        self.data_quality = self._determine_data_quality()
        self.confidence_level = self._calculate_confidence_level()
    
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
    
    def _categorize_aadt_volume(self) -> str:
        """
        Categorize AADT volume into descriptive categories
        
        Returns:
            Volume category based on AADT value
        """
        if self.aadt >= 50000:
            return "Very High"
        elif self.aadt >= 25000:
            return "High"
        elif self.aadt >= 10000:
            return "Moderate"
        elif self.aadt >= 5000:
            return "Low"
        else:
            return "Very Low"
    
    def _determine_data_quality(self) -> str:
        """
        Determine data quality based on FDOT flags
        
        Returns:
            Data quality indicator
        """
        # Check if any critical flags indicate issues
        problem_flags = ['E', 'P', 'Q']  # Error, Projected, Quality issue flags
        
        flags_to_check = [self.aadt_flag, self.k_flag, self.d_flag, self.t_flag]
        
        if any(flag in problem_flags for flag in flags_to_check if flag):
            return "Questionable"
        elif all(flag == 'C' for flag in flags_to_check if flag):  # 'C' typically means counted/actual
            return "Good"
        else:
            return "Fair"
    
    def _calculate_confidence_level(self) -> int:
        """
        Calculate confidence level based on data quality and flags
        
        Returns:
            Confidence level from 0-100
        """
        confidence = 100
        
        # Reduce confidence based on flags
        if self.aadt_flag in ['E', 'P']:
            confidence -= 30
        elif self.aadt_flag in ['Q']:
            confidence -= 15
        
        # Factor in other quality indicators
        quality_flags = [self.k_flag, self.d_flag, self.t_flag]
        problem_count = sum(1 for flag in quality_flags if flag in ['E', 'P', 'Q'])
        confidence -= problem_count * 10
        
        return max(0, min(100, confidence))
    
    def get_traffic_level(self) -> str:
        """
        Categorize traffic level based on AADT volume
        
        Returns:
            Traffic level category (Low, Moderate, High, Heavy)
        """
        if self.aadt >= 40000:
            return "Heavy"
        elif self.aadt >= 20000:
            return "High"
        elif self.aadt >= 8000:
            return "Moderate"
        else:
            return "Low"
    
    def get_color_by_traffic_level(self) -> List[int]:
        """
        Get color representation based on traffic level with enhanced AADT-based color mapping
        
        Returns:
            RGB color values [R, G, B, Alpha]
        """
        # Use more granular color mapping based on AADT values for better visualization
        if self.aadt >= 75000:
            return [139, 0, 0, 200]      # Dark Red - Very Heavy Traffic
        elif self.aadt >= 50000:
            return [255, 0, 0, 190]      # Red - Heavy Traffic
        elif self.aadt >= 35000:
            return [255, 69, 0, 180]     # Orange Red - High Traffic
        elif self.aadt >= 25000:
            return [255, 140, 0, 170]    # Dark Orange - High-Moderate Traffic
        elif self.aadt >= 15000:
            return [255, 165, 0, 160]    # Orange - Moderate-High Traffic
        elif self.aadt >= 10000:
            return [255, 215, 0, 150]    # Gold - Moderate Traffic
        elif self.aadt >= 5000:
            return [255, 255, 0, 140]    # Yellow - Low-Moderate Traffic
        elif self.aadt >= 2000:
            return [154, 205, 50, 130]   # Yellow Green - Low Traffic
        elif self.aadt >= 500:
            return [0, 255, 0, 120]      # Green - Very Low Traffic
        else:
            return [105, 105, 105, 100]  # Dim Gray - Minimal Traffic
    
    def get_line_width_by_volume(self) -> int:
        """
        Get line width based on AADT traffic volume with enhanced granularity
        
        Returns:
            Line width for map visualization
        """
        if self.aadt >= 75000:
            return 12      # Very thick for extremely high traffic
        elif self.aadt >= 50000:
            return 10      # Thick for very high traffic
        elif self.aadt >= 35000:
            return 8       # Medium-thick for high traffic
        elif self.aadt >= 25000:
            return 6       # Medium for moderate-high traffic
        elif self.aadt >= 15000:
            return 5       # Medium for moderate traffic
        elif self.aadt >= 10000:
            return 4       # Medium-thin for low-moderate traffic
        elif self.aadt >= 5000:
            return 3       # Thin for low traffic
        elif self.aadt >= 1000:
            return 2       # Very thin for very low traffic
        else:
            return 1       # Minimal width for extremely low traffic
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert traffic data to dictionary format"""
        return {
            # Basic identification
            'fid': self.fid,
            'objectid': self.objectid,
            'segment_id': self.segment_id,
            'roadway_code': self.roadway_code,
            'roadway_name': self.roadway_name,
            
            # FDOT specific fields
            'year': self.year,
            'district': self.district,
            'cosite': self.cosite,
            'desc_from': self.desc_from,
            'desc_to': self.desc_to,
            
            # Traffic volume data
            'aadt': self.aadt,
            'traffic_volume': self.traffic_volume,
            'aadt_flag': self.aadt_flag,
            'volume_category': self.volume_category,
            
            # Traffic factors
            'k_factor': self.k_factor,
            'k100_factor': self.k100_factor,
            'd_factor': self.d_factor,
            't_factor': self.t_factor,
            
            # Quality flags
            'k_flag': self.k_flag,
            'k100_flag': self.k100_flag,
            'd_flag': self.d_flag,
            't_flag': self.t_flag,
            
            # Location information
            'county_dot': self.county_dot,
            'county': self.county,
            'mng_district': self.mng_district,
            
            # Milepost information
            'begin_post': self.begin_post,
            'end_post': self.end_post,
            
            # Additional FDOT service fields
            'truck_per': self.truck_per,
            'tfctr_copy': self.tfctr_copy,
            
            # Geometry
            'shape_length': self.shape_length,
            'coordinates': self.coordinates,
            
            # Derived/compatibility fields
            'speed_limit': self.speed_limit,
            'average_speed': self.average_speed,
            'speed_ratio': self.speed_ratio,
            'direction': self.direction,
            'time_interval': self.time_interval,
            'data_timestamp': self.data_timestamp,
            'traffic_level': self.get_traffic_level(),
            'data_quality': self.data_quality,
            'confidence_level': self.confidence_level
        }
    
    def __str__(self) -> str:
        """String representation of traffic data"""
        return (f"TrafficData(roadway={self.roadway_name}, "
                f"aadt={self.aadt}, "
                f"county={self.county}, "
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
        Get segments with high AADT traffic volume
        
        Args:
            threshold: AADT threshold for high traffic
            
        Returns:
            List of high traffic segments
        """
        return [data for data in self.traffic_data if data.aadt >= threshold]
    
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
        
        total_volume = sum(data.aadt for data in self.traffic_data)
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