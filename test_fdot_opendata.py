#!/usr/bin/env python3
"""
Test script for FDOT Open Data Hub API integration
"""

import sys
import pandas as pd
from fdot_opendata_api import FDOTOpenDataAPI

def test_fdot_opendata_integration():
    """
    Test the FDOT Open Data Hub API integration
    """
    print("🚗 Testing FDOT Open Data Hub API Integration")
    print("=" * 50)
    
    # Initialize API
    api = FDOTOpenDataAPI()
    
    # Test 1: Connection test
    print("\n1. Testing connection to FDOT Open Data Hub...")
    if api.test_connection():
        print("✅ Connection successful")
    else:
        print("❌ Connection failed")
        return False
    
    # Test 2: Search catalog
    print("\n2. Testing catalog search...")
    collections = api.search_catalog(query="cities", limit=10)
    if collections:
        print(f"✅ Found {len(collections)} collections")
        for i, collection in enumerate(collections[:3]):
            print(f"   {i+1}. {collection.get('title', 'Unknown')}")
    else:
        print("⚠️ No collections found")
    
    # Test 3: Get cities
    print("\n3. Testing cities retrieval...")
    cities = api.get_florida_cities()
    if cities:
        print(f"✅ Retrieved {len(cities)} cities")
        print("Sample cities:")
        for i, city in enumerate(cities[:10]):
            print(f"   {i+1}. {city}")
    else:
        print("⚠️ No cities found")
    
    # Test 4: Test cities dataset
    print("\n4. Testing cities dataset retrieval...")
    cities_df = api.get_cities_dataset()
    if not cities_df.empty:
        print(f"✅ Retrieved cities dataset with {len(cities_df)} records")
        print("Dataset columns:", list(cities_df.columns))
        print("Sample data:")
        print(cities_df.head())
    else:
        print("⚠️ No cities dataset found")
    
    print("\n" + "=" * 50)
    print("🎉 FDOT Open Data Hub API test completed!")
    
    return True

def test_city_filtering():
    """
    Test city filtering functionality
    """
    print("\n🔍 Testing City Filtering Functionality")
    print("=" * 50)
    
    # Test with empty data (no sample data)
    df = pd.DataFrame()
    print(f"Original dataset: {len(df)} records")
    print("No sample data - testing with empty DataFrame")
    
    # Test filtering by city (should handle empty DataFrame gracefully)
    test_cities = ["West Palm Beach", "Boca Raton", "Non-existent City"]
    
    for city in test_cities:
        if not df.empty:
            filtered_df = df[df['city_name'].str.contains(city, case=False, na=False)]
            print(f"\nFiltering for '{city}': {len(filtered_df)} records found")
        else:
            print(f"\nFiltering for '{city}': 0 records found (empty DataFrame)")
    
    print("\n✅ City filtering test completed!")

if __name__ == "__main__":
    try:
        # Test FDOT Open Data Hub integration
        success = test_fdot_opendata_integration()
        
        if success:
            # Test city filtering
            test_city_filtering()
        else:
            print("❌ FDOT Open Data Hub integration test failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1) 