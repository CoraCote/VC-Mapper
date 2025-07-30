#!/usr/bin/env python3
"""
Test script for FDOT ArcGIS REST API integration
"""

import sys
import pandas as pd

def test_fdot_api_integration():
    """
    Test the FDOT API integration
    """
    print("🚗 Testing FDOT ArcGIS REST API Integration")
    print("=" * 50)
    
    try:
        # Import our FDOT API module
        from fdot_api import FDOTArcGISAPI
        
        # Initialize API client
        print("📡 Initializing FDOT API client...")
        api = FDOTArcGISAPI()
        
        # Test 1: Traffic Monitoring Sites
        print("\n🔍 Test 1: Traffic Monitoring Sites")
        print("-" * 30)
        sites_df = api.get_traffic_monitoring_sites(county="Palm Beach")
        print(f"✅ Found {len(sites_df)} traffic monitoring sites")
        if not sites_df.empty:
            print("Data preview:")
            print(sites_df.head(3))
        
        # Test 2: AADT Data
        print("\n🔍 Test 2: AADT Data")
        print("-" * 30)
        aadt_df = api.get_aadt_data(county="Palm Beach", year=2023)
        print(f"✅ Found {len(aadt_df)} AADT records")
        if not aadt_df.empty:
            print("Data preview:")
            print(aadt_df.head(3))
        
        # Test 3: Comprehensive Traffic Data
        print("\n🔍 Test 3: Comprehensive Traffic Data")
        print("-" * 30)
        traffic_df = api.get_traffic_data(county="Palm Beach", year=2023)
        print(f"✅ Found {len(traffic_df)} traffic records")
        if not traffic_df.empty:
            print("Data preview:")
            print(traffic_df.head(3))
            
            # Show data types and info
            print("\n📊 Data Info:")
            print(f"Columns: {list(traffic_df.columns)}")
            print(f"Data types: {traffic_df.dtypes.to_dict()}")
            print(f"Missing values: {traffic_df.isnull().sum().to_dict()}")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install requests pandas numpy")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def test_streamlit_integration():
    """
    Test Streamlit integration
    """
    print("\n🎯 Testing Streamlit Integration")
    print("=" * 50)
    
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
        
        # Test if we can import our app functions
        from app import load_fdot_traffic_data
        print("✅ App functions imported successfully")
        
        # Test data loading
        print("📊 Testing data loading function...")
        test_data = load_fdot_traffic_data("Palm Beach")
        print(f"✅ Data loading successful: {len(test_data)} records")
        
        return True
        
    except ImportError as e:
        print(f"❌ Streamlit import error: {e}")
        print("Make sure Streamlit is installed:")
        print("pip install streamlit")
        return False
    except Exception as e:
        print(f"❌ Error during Streamlit testing: {e}")
        return False

if __name__ == "__main__":
    print("🚗 V/C Ratio Calculator - FDOT API Integration Test")
    print("=" * 60)
    
    # Test FDOT API
    api_success = test_fdot_api_integration()
    
    # Test Streamlit integration
    streamlit_success = test_streamlit_integration()
    
    print("\n" + "=" * 60)
    if api_success and streamlit_success:
        print("🎉 All tests passed! The application is ready to run.")
        print("\nTo run the application:")
        print("streamlit run app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1) 