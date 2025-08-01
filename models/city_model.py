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