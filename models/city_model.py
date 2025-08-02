"""
City Model - Handles city data structures and operations
"""

from typing import List, Dict, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class City:
    """
    City data model
    """
    
    def __init__(self, data: Dict):
        """
        Initialize a City object with data from API
        
        Args:
            data: Dictionary containing city data
        """
        self.geoid = data.get('geoid', '')
        self.name = data.get('name', '')
        self.full_name = data.get('full_name', '')
        self.latitude = data.get('latitude')
        self.longitude = data.get('longitude')
        self.population = data.get('population', 0)
        self.land_area = data.get('land_area', 0)
        self.water_area = data.get('water_area', 0)
        self.state_fips = data.get('state_fips', '')
        self.place_fips = data.get('place_fips', '')
        self.lsad = data.get('lsad', '')
        self.class_fp = data.get('class_fp', '')
        self.func_stat = data.get('func_stat', '')
    
    def to_dict(self) -> Dict:
        """Convert city object back to dictionary"""
        return {
            'geoid': self.geoid,
            'name': self.name,
            'full_name': self.full_name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'population': self.population,
            'land_area': self.land_area,
            'water_area': self.water_area,
            'state_fips': self.state_fips,
            'place_fips': self.place_fips,
            'lsad': self.lsad,
            'class_fp': self.class_fp,
            'func_stat': self.func_stat
        }
    
    def has_valid_coordinates(self) -> bool:
        """Check if city has valid latitude and longitude"""
        return (self.latitude is not None and 
                self.longitude is not None and
                isinstance(self.latitude, (int, float)) and
                isinstance(self.longitude, (int, float)))
    
    def get_display_name(self) -> str:
        """Get formatted display name with GEOID"""
        return f"{self.name} ({self.geoid})"
    
    def get_population_category(self) -> str:
        """Get population category for visualization"""
        if self.population > 100000:
            return "metropolis"
        elif self.population > 50000:
            return "large_city"
        elif self.population > 10000:
            return "medium_city"
        else:
            return "small_city"
    
    def get_marker_style(self) -> Dict:
        """Get marker style based on population"""
        category = self.get_population_category()
        
        styles = {
            "metropolis": {"color": "red", "icon": "star", "size": 12},
            "large_city": {"color": "orange", "icon": "info-sign", "size": 10},
            "medium_city": {"color": "blue", "icon": "record", "size": 8},
            "small_city": {"color": "green", "icon": "circle", "size": 6}
        }
        
        return styles.get(category, styles["small_city"])


class CityCollection:
    """
    Collection of cities with utility methods
    """
    
    def __init__(self, cities_data: List[Dict] = None):
        """
        Initialize collection with city data
        
        Args:
            cities_data: List of city dictionaries
        """
        self.cities = []
        if cities_data:
            self.cities = [City(data) for data in cities_data]
    
    def add_city(self, city_data: Dict):
        """Add a city to the collection"""
        self.cities.append(City(city_data))
    
    def get_valid_cities(self) -> List[City]:
        """Get cities with valid coordinates"""
        return [city for city in self.cities if city.has_valid_coordinates()]
    
    def get_cities_as_dict_list(self) -> List[Dict]:
        """Get all cities as list of dictionaries"""
        return [city.to_dict() for city in self.cities]
    
    def filter_by_population(self, min_population: int = 0) -> List[City]:
        """Filter cities by minimum population"""
        return [city for city in self.cities if city.population >= min_population]
    
    def filter_by_state_fips(self, state_fips: str) -> List[City]:
        """Filter cities by state FIPS"""
        if state_fips == "All":
            return self.cities
        return [city for city in self.cities if city.state_fips == state_fips]
    
    def sort_cities(self, sort_by: str, reverse: bool = False) -> List[City]:
        """Sort cities by specified field"""
        sort_mapping = {
            "Name": lambda x: x.name,
            "Population": lambda x: x.population,
            "Land Area": lambda x: x.land_area,
            "Water Area": lambda x: x.water_area
        }
        
        sort_func = sort_mapping.get(sort_by, sort_mapping["Name"])
        return sorted(self.cities, key=sort_func, reverse=reverse)
    
    def get_largest_city(self) -> Optional[City]:
        """Get city with largest population"""
        if not self.cities:
            return None
        return max(self.cities, key=lambda x: x.population)
    
    def get_smallest_city(self) -> Optional[City]:
        """Get city with smallest population"""
        if not self.cities:
            return None
        return min(self.cities, key=lambda x: x.population)
    
    def get_total_population(self) -> int:
        """Get total population of all cities"""
        return sum(city.population for city in self.cities)
    
    def get_total_land_area(self) -> float:
        """Get total land area of all cities in square meters"""
        return sum(city.land_area for city in self.cities)
    
    def get_total_water_area(self) -> float:
        """Get total water area of all cities in square meters"""
        return sum(city.water_area for city in self.cities)
    
    def get_average_population(self) -> float:
        """Get average population"""
        if not self.cities:
            return 0
        return self.get_total_population() / len(self.cities)
    
    def get_median_population(self) -> int:
        """Get median population"""
        if not self.cities:
            return 0
        populations = sorted([city.population for city in self.cities])
        return populations[len(populations) // 2]
    
    def get_top_cities(self, limit: int = 5) -> List[City]:
        """Get top cities by population"""
        return sorted(self.cities, key=lambda x: x.population, reverse=True)[:limit]
    
    def get_center_coordinates(self) -> tuple:
        """Get center coordinates of all valid cities"""
        valid_cities = self.get_valid_cities()
        if not valid_cities:
            return 27.8333, -81.717  # Default to Florida center
        
        center_lat = sum(city.latitude for city in valid_cities) / len(valid_cities)
        center_lon = sum(city.longitude for city in valid_cities) / len(valid_cities)
        return center_lat, center_lon
    
    def find_closest_city(self, lat: float, lon: float) -> Optional[City]:
        """Find closest city to given coordinates"""
        valid_cities = self.get_valid_cities()
        if not valid_cities:
            return None
        
        return min(valid_cities, 
                  key=lambda city: abs(city.latitude - lat) + abs(city.longitude - lon))
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert collection to pandas DataFrame"""
        data = []
        for city in self.cities:
            data.append({
                'Name': city.name,
                'Full Name': city.full_name,
                'GEOID': city.geoid,
                'Latitude': city.latitude,
                'Longitude': city.longitude,
                'Population': city.population,
                'Land Area (sq m)': city.land_area,
                'Water Area (sq m)': city.water_area,
                'State FIPS': city.state_fips,
                'Place FIPS': city.place_fips,
                'LSAD': city.lsad,
                'Class FP': city.class_fp,
                'Func Stat': city.func_stat
            })
        
        return pd.DataFrame(data)
    
    def __len__(self) -> int:
        """Return number of cities in collection"""
        return len(self.cities)
    
    def __iter__(self):
        """Make collection iterable"""
        return iter(self.cities)
    
    def __getitem__(self, index):
        """Make collection indexable"""
        return self.cities[index]


class TrafficData:
    """
    Traffic data model for Annual Average Daily Traffic (AADT) data
    """
    
    def __init__(self, feature_data: Dict):
        """
        Initialize a TrafficData object with GeoJSON feature data
        
        Args:
            feature_data: Dictionary containing traffic feature data from API
        """
        self.properties = feature_data.get('properties', {})
        self.geometry = feature_data.get('geometry', {})
        
        # Extract common traffic properties based on actual data structure
        self.objectid = self.properties.get('FID')
        self.roadway = self.properties.get('ROADWAY', '')
        self.county = self.properties.get('COUNTY', '')
        self.year = self.properties.get('YEAR_')
        self.aadt = self.properties.get('AADT', 0)  # Annual Average Daily Traffic
        self.peak_hour = self.properties.get('KFCTR', 0)  # K-Factor (peak hour factor)
        self.district = self.properties.get('DISTRICT', '')
        self.route = self.properties.get('DESC_TO', '')  # Route description
        self.desc_from = self.properties.get('DESC_FRM', '')
        self.desc_to = self.properties.get('DESC_TO', '')
        self.cosite = self.properties.get('COSITE', '')
        self.aadtflg = self.properties.get('AADTFLG', '')
        self.countydot = self.properties.get('COUNTYDOT', '')
        self.mng_dist = self.properties.get('MNG_DIST', '')
        self.begin_post = self.properties.get('BEGIN_POST', 0)
        self.end_post = self.properties.get('END_POST', 0)
        
    def to_dict(self) -> Dict:
        """Convert traffic data object back to dictionary"""
        return {
            'objectid': self.objectid,
            'roadway': self.roadway,
            'county': self.county,
            'year': self.year,
            'aadt': self.aadt,
            'peak_hour': self.peak_hour,
            'district': self.district,
            'route': self.route,
            'desc_from': self.desc_from,
            'desc_to': self.desc_to,
            'cosite': self.cosite,
            'aadtflg': self.aadtflg,
            'countydot': self.countydot,
            'mng_dist': self.mng_dist,
            'begin_post': self.begin_post,
            'end_post': self.end_post,
            'geometry': self.geometry,
            'properties': self.properties
        }


class TrafficDataCollection:
    """
    Collection of traffic data with utility methods
    """
    
    def __init__(self, traffic_geojson: Dict = None):
        """
        Initialize collection with traffic GeoJSON data
        
        Args:
            traffic_geojson: GeoJSON dictionary containing traffic features
        """
        self.traffic_data = []
        if traffic_geojson and 'features' in traffic_geojson:
            self.traffic_data = [TrafficData(feature) for feature in traffic_geojson['features']]
    
    def get_traffic_by_county(self, county: str) -> List[TrafficData]:
        """Get traffic data filtered by county"""
        return [td for td in self.traffic_data if td.county.upper() == county.upper()]
    
    def get_traffic_by_route(self, route: str) -> List[TrafficData]:
        """Get traffic data filtered by route"""
        return [td for td in self.traffic_data if route.upper() in td.route.upper()]
    
    def get_high_traffic_roads(self, min_aadt: int = 10000) -> List[TrafficData]:
        """Get roads with high traffic volume"""
        return [td for td in self.traffic_data if td.aadt >= min_aadt]
    
    def get_traffic_summary_stats(self) -> Dict:
        """Get summary statistics for traffic data"""
        if not self.traffic_data:
            return {}
        
        aadt_values = [td.aadt for td in self.traffic_data if td.aadt > 0]
        
        return {
            'total_records': len(self.traffic_data),
            'records_with_aadt': len(aadt_values),
            'avg_aadt': sum(aadt_values) / len(aadt_values) if aadt_values else 0,
            'max_aadt': max(aadt_values) if aadt_values else 0,
            'min_aadt': min(aadt_values) if aadt_values else 0,
            'unique_counties': len(set(td.county for td in self.traffic_data if td.county)),
            'unique_routes': len(set(td.route for td in self.traffic_data if td.route))
        }
    
    def get_vc_ratio_analytics(self) -> Dict:
        """
        Calculate V/C ratio analytics for each congestion level
        
        Returns:
            Dictionary with analytics for each V/C ratio category
        """
        if not self.traffic_data:
            return {}
        
        # Define V/C ratio categories
        categories = {
            'low': {'min': 0, 'max': 0.5, 'color': '🟢', 'name': 'Low Congestion'},
            'moderate': {'min': 0.5, 'max': 0.8, 'color': '🟡', 'name': 'Moderate Congestion'},
            'high': {'min': 0.8, 'max': 1.0, 'color': '🟠', 'name': 'High Congestion'},
            'over_capacity': {'min': 1.0, 'max': float('inf'), 'color': '🔴', 'name': 'Over Capacity'}
        }
        
        analytics = {}
        
        for category, config in categories.items():
            # Filter traffic data by V/C ratio
            category_data = []
            for td in self.traffic_data:
                if td.aadt > 0:
                    # Estimate capacity based on route type (simplified)
                    estimated_capacity = self._estimate_capacity(td)
                    vc_ratio = td.aadt / estimated_capacity if estimated_capacity > 0 else 0
                    
                    if config['min'] <= vc_ratio < config['max']:
                        category_data.append({
                            'traffic_data': td,
                            'vc_ratio': vc_ratio,
                            'estimated_capacity': estimated_capacity
                        })
            
            # Calculate analytics for this category
            if category_data:
                vc_ratios = [item['vc_ratio'] for item in category_data]
                aadt_values = [item['traffic_data'].aadt for item in category_data]
                counties = list(set(item['traffic_data'].county for item in category_data if item['traffic_data'].county))
                routes = list(set(item['traffic_data'].route for item in category_data if item['traffic_data'].route))
                
                analytics[category] = {
                    'count': len(category_data),
                    'percentage': (len(category_data) / len(self.traffic_data)) * 100,
                    'avg_vc_ratio': sum(vc_ratios) / len(vc_ratios),
                    'min_vc_ratio': min(vc_ratios),
                    'max_vc_ratio': max(vc_ratios),
                    'avg_aadt': sum(aadt_values) / len(aadt_values),
                    'min_aadt': min(aadt_values),
                    'max_aadt': max(aadt_values),
                    'unique_counties': len(counties),
                    'unique_routes': len(routes),
                    'top_counties': sorted(counties, key=lambda x: len([item for item in category_data if item['traffic_data'].county == x]), reverse=True)[:3],
                    'top_routes': sorted(routes, key=lambda x: len([item for item in category_data if item['traffic_data'].route == x]), reverse=True)[:3],
                    'color': config['color'],
                    'name': config['name']
                }
            else:
                analytics[category] = {
                    'count': 0,
                    'percentage': 0,
                    'avg_vc_ratio': 0,
                    'min_vc_ratio': 0,
                    'max_vc_ratio': 0,
                    'avg_aadt': 0,
                    'min_aadt': 0,
                    'max_aadt': 0,
                    'unique_counties': 0,
                    'unique_routes': 0,
                    'top_counties': [],
                    'top_routes': [],
                    'color': config['color'],
                    'name': config['name']
                }
        
        return analytics
    
    def _estimate_capacity(self, traffic_data: 'TrafficData') -> float:
        """
        Estimate roadway capacity based on route description
        
        Args:
            traffic_data: TrafficData object
            
        Returns:
            Estimated capacity (vehicles per day)
        """
        try:
            desc_to = traffic_data.desc_to or ""
            route = traffic_data.route or ""
            
            # Interstate highways
            if any(keyword in desc_to.upper() for keyword in ['I-', 'INTERSTATE', 'I95', 'I75', 'I4']):
                return 80000
            
            # US highways
            elif any(keyword in desc_to.upper() for keyword in ['US-', 'US ', 'US1', 'US27', 'US41']):
                return 40000
            
            # State roads
            elif any(keyword in desc_to.upper() for keyword in ['SR-', 'SR ', 'STATE', 'SR811', 'SR80']):
                return 30000
            
            # County roads
            elif any(keyword in desc_to.upper() for keyword in ['CR-', 'CR ', 'COUNTY']):
                return 15000
            
            # Local roads
            else:
                return 10000
                
        except Exception:
            return 20000  # Default fallback
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert collection to pandas DataFrame"""
        data = []
        for td in self.traffic_data:
            data.append({
                'Object ID': td.objectid,
                'Roadway': td.roadway,
                'County': td.county,
                'Year': td.year,
                'AADT': td.aadt,
                'Peak Hour': td.peak_hour,
                'District': td.district,
                'Route': td.route,
                'Description From': td.desc_from,
                'Description To': td.desc_to,
                'COSITE': td.cosite,
                'AADT Flag': td.aadtflg,
                'County DOT': td.countydot,
                'Management District': td.mng_dist,
                'Begin Post': td.begin_post,
                'End Post': td.end_post
            })
        
        return pd.DataFrame(data)
    
    def __len__(self) -> int:
        """Return number of traffic records in collection"""
        return len(self.traffic_data)
    
    def __iter__(self):
        """Make collection iterable"""
        return iter(self.traffic_data)
    
    def __getitem__(self, index):
        """Make collection indexable"""
        return self.traffic_data[index]