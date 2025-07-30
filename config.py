"""
Configuration settings for V/C Ratio Calculator
"""

import os
from typing import Dict, List

# Application settings
APP_TITLE = "V/C Ratio Calculator"
APP_ICON = "🚗"
APP_LAYOUT = "wide"

# Florida counties with their coordinates
FLORIDA_COUNTIES = {
    "Palm Beach": {
        "name": "Palm Beach County",
        "lat": 26.7153,
        "lon": -80.0534,
        "zoom": 10,
        "fdot_district": "4"
    },
    "Broward": {
        "name": "Broward County", 
        "lat": 26.1901,
        "lon": -80.3656,
        "zoom": 10,
        "fdot_district": "4"
    },
    "Miami-Dade": {
        "name": "Miami-Dade County",
        "lat": 25.7617,
        "lon": -80.1918,
        "zoom": 10,
        "fdot_district": "6"
    },
    "Monroe": {
        "name": "Monroe County",
        "lat": 24.5557,
        "lon": -81.7826,
        "zoom": 9,
        "fdot_district": "6"
    }
}

# FDOT Traffic Online API settings
FDOT_API_CONFIG = {
    "base_url": "https://tdaappsprod.dot.state.fl.us/fto/",
    "timeout": 30,
    "max_retries": 3
}

# Capacity table by functional classification
CAPACITY_TABLE = {
    "Freeway": {
        "capacity_veh_day": 50000,
        "capacity_veh_hour": 2500,
        "lanes": 4,
        "description": "Limited access highways"
    },
    "Arterial": {
        "capacity_veh_day": 25000,
        "capacity_veh_hour": 1250,
        "lanes": 2,
        "description": "Major through streets"
    },
    "Collector": {
        "capacity_veh_day": 15000,
        "capacity_veh_hour": 750,
        "lanes": 2,
        "description": "Minor through streets"
    },
    "Local": {
        "capacity_veh_day": 8000,
        "capacity_veh_hour": 400,
        "lanes": 1,
        "description": "Local access streets"
    }
}

# V/C ratio thresholds and colors
VC_THRESHOLDS = {
    "good": {
        "max": 0.7,
        "color": "#28a745",
        "status": "Good",
        "description": "Adequate capacity"
    },
    "fair": {
        "min": 0.7,
        "max": 0.9,
        "color": "#ffc107", 
        "status": "Fair",
        "description": "Approaching capacity"
    },
    "poor": {
        "min": 0.9,
        "max": 1.0,
        "color": "#dc3545",
        "status": "Poor", 
        "description": "At or near capacity"
    },
    "critical": {
        "min": 1.0,
        "color": "#6f42c1",
        "status": "Critical",
        "description": "Over capacity"
    }
}

# Default growth rates by county (annual percentages)
DEFAULT_GROWTH_RATES = {
    "Palm Beach": 2.5,
    "Broward": 2.0,
    "Miami-Dade": 1.8,
    "Monroe": 1.2
}

# File upload settings
UPLOAD_CONFIG = {
    "max_file_size": 50,  # MB
    "allowed_types": ["csv", "xlsx", "xls"],
    "required_columns": ["road_name", "current_volume"],
    "optional_columns": ["functional_class", "segment_id", "latitude", "longitude"]
}

# Map visualization settings
MAP_CONFIG = {
    "default_tiles": "OpenStreetMap",
    "marker_radius": 10,
    "marker_opacity": 0.7,
    "popup_width": 300
}

# Chart and visualization settings
CHART_CONFIG = {
    "histogram_bins": 20,
    "color_scheme": "viridis",
    "figure_height": 400,
    "figure_width": 800
}

# Export settings
EXPORT_CONFIG = {
    "csv_encoding": "utf-8",
    "excel_engine": "openpyxl",
    "date_format": "%Y%m%d_%H%M%S"
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "vc_calculator.log"
}

# Development settings
DEV_CONFIG = {
    "debug_mode": os.getenv("DEBUG", "False").lower() == "true",
    "sample_data_size": 50,
    "cache_timeout": 3600  # 1 hour
}

# API rate limiting
RATE_LIMIT_CONFIG = {
    "requests_per_minute": 60,
    "requests_per_hour": 1000
}

# Error messages
ERROR_MESSAGES = {
    "file_upload": "Error uploading file. Please check the file format and try again.",
    "data_validation": "Data validation failed. Please check your input data.",
    "api_error": "Error connecting to FDOT API. Please try again later.",
    "calculation_error": "Error calculating V/C ratios. Please check your data.",
    "export_error": "Error exporting data. Please try again."
}

# Success messages
SUCCESS_MESSAGES = {
    "data_loaded": "Data loaded successfully!",
    "calculations_complete": "V/C ratio calculations completed!",
    "export_success": "Data exported successfully!"
}

# Help text for UI elements
HELP_TEXT = {
    "county_selection": "Select the county for which you want to analyze V/C ratios.",
    "growth_rate": "Annual growth rate as a percentage. This will be applied to project future traffic volumes.",
    "projection_years": "Number of years to project into the future for V/C ratio calculations.",
    "data_source": "Choose the source of traffic volume data: FDOT Traffic Online (automated), uploaded CSV file, or manual entry.",
    "vc_ratio": "Volume/Capacity ratio indicates how much of the roadway's capacity is being used. Values above 1.0 indicate over-capacity conditions.",
    "color_coding": "Green: Good (< 0.7), Yellow: Fair (0.7-0.9), Red: Poor (0.9-1.0), Purple: Critical (> 1.0)"
} 