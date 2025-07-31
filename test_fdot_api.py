#!/usr/bin/env python3
"""
Test script for FDOT GIS API integration
"""

import unittest
from unittest.mock import patch, Mock
import json
from fdot_api import FDOTGISAPI

class TestFDOTGISAPI(unittest.TestCase):
    """Test cases for FDOT GIS API client"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.api = FDOTGISAPI()
        
        # Sample API response data
        self.sample_response = {
            "objectIdFieldName": "OBJECTID",
            "globalIdFieldName": "",
            "geometryType": "esriGeometryPolygon",
            "spatialReference": {"wkid": 26917, "latestWkid": 26917},
            "fields": [
                {"name": "OBJECTID", "alias": "OBJECTID", "type": "esriFieldTypeOID"},
                {"name": "NAME", "alias": "NAME", "type": "esriFieldTypeString", "length": 100},
                {"name": "GEOID", "alias": "GEOID", "type": "esriFieldTypeString", "length": 7},
                {"name": "INTPTLAT", "alias": "INTPTLAT", "type": "esriFieldTypeString", "length": 11},
                {"name": "INTPTLON", "alias": "INTPTLON", "type": "esriFieldTypeString", "length": 12},
                {"name": "POP", "alias": "POP", "type": "esriFieldTypeInteger"}
            ],
            "features": [
                {
                    "attributes": {
                        "OBJECTID": 1,
                        "NAME": "Satellite Beach",
                        "NAMELSAD": "Satellite Beach city",
                        "GEOID": "1264400",
                        "INTPTLAT": "+28.1787326",
                        "INTPTLON": "-080.5994021",
                        "POP": 10109,
                        "ALAND": 7561145.0,
                        "AWATER": 3547858.0,
                        "STATEFP": "12",
                        "PLACEFP": "64400",
                        "LSAD": "25",
                        "CLASSFP": "C1",
                        "FUNCSTAT": "A"
                    },
                    "geometry": {
                        "rings": [[[538195.45449999999, 3118001.8004999999]]]
                    }
                }
            ]
        }
    
    def test_init(self):
        """Test API client initialization"""
        self.assertEqual(
            self.api.base_url,
            "https://gis.fdot.gov/arcgis/rest/services/Admin_Boundaries/FeatureServer/7/query"
        )
        self.assertIsNotNone(self.api.session)
    
    @patch('requests.Session.get')
    def test_fetch_cities_success(self, mock_get):
        """Test successful city fetching"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = self.sample_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call the method
        cities = self.api.fetch_cities()
        
        # Verify results
        self.assertEqual(len(cities), 1)
        city = cities[0]
        self.assertEqual(city['name'], 'Satellite Beach')
        self.assertEqual(city['geoid'], '1264400')
        self.assertEqual(city['latitude'], 28.1787326)
        self.assertEqual(city['longitude'], -80.5994021)
        self.assertEqual(city['population'], 10109)
        
        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['params']['where'], '1=1')
        self.assertEqual(call_args[1]['params']['outFields'], '*')
    
    @patch('requests.Session.get')
    def test_fetch_cities_with_limit(self, mock_get):
        """Test city fetching with limit"""
        mock_response = Mock()
        mock_response.json.return_value = self.sample_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        cities = self.api.fetch_cities(limit=5)
        
        # Verify limit parameter was passed
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['params']['resultRecordCount'], 5)
    
    @patch('requests.Session.get')
    def test_fetch_cities_no_features(self, mock_get):
        """Test handling of response with no features"""
        mock_response = Mock()
        mock_response.json.return_value = {"features": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        cities = self.api.fetch_cities()
        self.assertEqual(cities, [])
    
    @patch('requests.Session.get')
    def test_fetch_cities_request_error(self, mock_get):
        """Test handling of request errors"""
        mock_get.side_effect = Exception("Network error")
        
        cities = self.api.fetch_cities()
        self.assertEqual(cities, [])
    
    def test_parse_coordinate_valid(self):
        """Test coordinate parsing with valid input"""
        self.assertEqual(self.api._parse_coordinate("+28.1787326"), 28.1787326)
        self.assertEqual(self.api._parse_coordinate("-080.5994021"), -80.5994021)
        self.assertEqual(self.api._parse_coordinate("0"), 0.0)
    
    def test_parse_coordinate_invalid(self):
        """Test coordinate parsing with invalid input"""
        self.assertIsNone(self.api._parse_coordinate(""))
        self.assertIsNone(self.api._parse_coordinate("invalid"))
        self.assertIsNone(self.api._parse_coordinate(None))
    
    def test_format_city_data_valid(self):
        """Test city data formatting with valid feature"""
        feature = self.sample_response['features'][0]
        city_data = self.api._format_city_data(feature)
        
        self.assertIsNotNone(city_data)
        self.assertEqual(city_data['name'], 'Satellite Beach')
        self.assertEqual(city_data['full_name'], 'Satellite Beach city')
        self.assertEqual(city_data['geoid'], '1264400')
        self.assertEqual(city_data['latitude'], 28.1787326)
        self.assertEqual(city_data['longitude'], -80.5994021)
        self.assertEqual(city_data['population'], 10109)
        self.assertEqual(city_data['land_area'], 7561145.0)
        self.assertEqual(city_data['water_area'], 3547858.0)
    
    def test_format_city_data_missing_required(self):
        """Test city data formatting with missing required fields"""
        feature = {
            "attributes": {
                "NAME": "",  # Missing name
                "GEOID": "1264400"
            }
        }
        
        city_data = self.api._format_city_data(feature)
        self.assertIsNone(city_data)
    
    @patch('requests.Session.get')
    def test_search_cities(self, mock_get):
        """Test city search functionality"""
        mock_response = Mock()
        mock_response.json.return_value = self.sample_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        cities = self.api.search_cities("Satellite", limit=5)
        
        # Verify search query was used
        call_args = mock_get.call_args
        self.assertIn("NAME LIKE '%Satellite%'", call_args[1]['params']['where'])
        self.assertEqual(call_args[1]['params']['resultRecordCount'], 5)
    
    @patch('requests.Session.get')
    def test_get_city_by_geoid(self, mock_get):
        """Test getting city by GEOID"""
        mock_response = Mock()
        mock_response.json.return_value = self.sample_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        city = self.api.get_city_by_geoid("1264400")
        
        # Verify GEOID query was used
        call_args = mock_get.call_args
        self.assertIn("GEOID = '1264400'", call_args[1]['params']['where'])
        
        self.assertIsNotNone(city)
        self.assertEqual(city['name'], 'Satellite Beach')
        self.assertEqual(city['geoid'], '1264400')
    
    @patch('requests.Session.get')
    def test_get_city_by_geoid_not_found(self, mock_get):
        """Test getting city by GEOID when not found"""
        mock_response = Mock()
        mock_response.json.return_value = {"features": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        city = self.api.get_city_by_geoid("9999999")
        self.assertIsNone(city)

if __name__ == "__main__":
    unittest.main() 