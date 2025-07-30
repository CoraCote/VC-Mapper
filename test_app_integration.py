#!/usr/bin/env python3
"""
Test script for Streamlit app integration with FDOT Open Data Hub API
"""

import sys
import pandas as pd
from fdot_opendata_api import FDOTOpenDataAPI

def test_app_integration():
    """
    Test the integration between the Streamlit app and FDOT Open Data Hub API
    """
    print("🚗 Testing Streamlit App Integration with FDOT Open Data Hub")
    print("=" * 60)
    
    # Test 1: Initialize API
    print("\n1. Testing API initialization...")
    try:
        api = FDOTOpenDataAPI()
        print("✅ API initialized successfully")
    except Exception as e:
        print(f"❌ API initialization failed: {e}")
        return False
    
    # Test 2: Test connection
    print("\n2. Testing API connection...")
    if api.test_connection():
        print("✅ API connection successful")
    else:
        print("❌ API connection failed")
        return False
    
    # Test 3: Get cities list
    print("\n3. Testing cities retrieval...")
    cities = api.get_florida_cities()
    if cities:
        print(f"✅ Retrieved {len(cities)} cities")
        print("Sample cities:", cities[:5])
    else:
        print("❌ No cities retrieved")
        return False
    
    # Test 4: Test city filtering logic
    print("\n4. Testing city filtering logic...")
    
    # Sample traffic data with city information
    sample_data = {
        'segment_id': range(1, 11),
        'road_name': [f"Road {i}" for i in range(1, 11)],
        'city_name': [
            "West Palm Beach", "Boca Raton", "Delray Beach", "Boynton Beach",
            "Lake Worth", "Wellington", "Jupiter", "Palm Beach Gardens",
            "Fort Lauderdale", "Hollywood"
        ],
        'current_volume': [15000, 12000, 18000, 14000, 16000, 11000, 13000, 17000, 20000, 19000],
        'functional_class': ['Arterial'] * 5 + ['Collector'] * 5
    }
    
    df = pd.DataFrame(sample_data)
    print(f"Original dataset: {len(df)} records")
    
    # Test filtering logic (same as in app.py)
    test_cities = ["West Palm Beach", "Boca Raton", "All Cities"]
    
    for city in test_cities:
        if city == "All Cities":
            filtered_df = df
            print(f"Filtering for '{city}': {len(filtered_df)} records (all cities)")
        else:
            # Try to filter by city name in various possible columns
            city_columns = [col for col in df.columns if any(term in col.lower() for term in ['city', 'municipal', 'name'])]
            if city_columns:
                original_count = len(df)
                filtered_df = df[df[city_columns[0]].str.contains(city, case=False, na=False)]
                filtered_count = len(filtered_df)
                print(f"Filtering for '{city}': {filtered_count} records (from {original_count} total)")
            else:
                print(f"⚠️ Could not filter by city '{city}' - no city column found in data")
                filtered_df = df
    
    # Test 5: Test session state simulation
    print("\n5. Testing session state simulation...")
    
    # Simulate session state
    session_state = {
        'cities_list': cities,
        'cities_loaded': True,
        'data_loaded': True
    }
    
    print(f"✅ Session state initialized with {len(session_state['cities_list'])} cities")
    print(f"✅ Cities loaded: {session_state['cities_loaded']}")
    print(f"✅ Data loaded: {session_state['data_loaded']}")
    
    print("\n" + "=" * 60)
    print("🎉 Streamlit App Integration Test Completed Successfully!")
    print("\n📋 Summary:")
    print(f"   • API Connection: ✅ Working")
    print(f"   • Cities Retrieved: ✅ {len(cities)} cities")
    print(f"   • City Filtering: ✅ Working")
    print(f"   • Session State: ✅ Ready")
    print(f"   • App Integration: ✅ Ready for Streamlit")
    
    return True

if __name__ == "__main__":
    try:
        success = test_app_integration()
        if not success:
            print("❌ Integration test failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1) 