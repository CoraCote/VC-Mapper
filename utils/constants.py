"""
Constants - Application constants and configuration
"""

# Florida state boundary GeoJSON (simplified coordinates)
FLORIDA_BOUNDARY = {
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "properties": {"name": "Florida"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-87.634896, 30.997536],  # Northwest corner
                [-87.427917, 30.997536], 
                [-86.913892, 30.997536],
                [-85.497137, 30.997536],
                [-84.319447, 30.676609],
                [-82.879938, 30.564875],
                [-82.190083, 30.564875],
                [-81.24069, 30.564875],
                [-80.915156, 31.068903],
                [-80.565487, 31.068903],
                [-80.381653, 30.997536],
                [-80.08183, 30.997536],
                [-80.031983, 30.564875],
                [-80.031983, 29.229735],
                [-80.031983, 28.128005],
                [-80.031983, 26.994637],
                [-80.031983, 25.729595],
                [-80.218695, 25.204941],
                [-80.748177, 25.204941],
                [-81.092673, 24.411089],
                [-81.755371, 24.411089],
                [-82.650513, 24.568745],
                [-83.351287, 25.204941],
                [-84.02832, 25.573047],
                [-84.319447, 25.573047],
                [-85.064697, 25.890106],
                [-85.872803, 26.994637],
                [-86.462402, 28.128005],
                [-87.017822, 28.902305],
                [-87.459717, 29.675867],
                [-87.634896, 30.997536]   # Closing coordinate
            ]]
        }
    }]
}

# Traffic level color mapping
TRAFFIC_COLORS = {
    'very_high': '#FF0000',  # Red
    'high': '#FF6600',       # Orange
    'medium': '#FFFF00',     # Yellow
    'low': '#66FF00',        # Light Green
    'very_low': '#00FF00',   # Green
    'unknown': '#808080'     # Gray
}

# Population category definitions
POPULATION_CATEGORIES = {
    'metropolis': {
        'min_population': 100000,
        'color': 'red',
        'icon': 'star',
        'size': 12,
        'label': 'Metropolis (> 100,000)'
    },
    'large_city': {
        'min_population': 50000,
        'max_population': 100000,
        'color': 'orange',
        'icon': 'info-sign',
        'size': 10,
        'label': 'Large City (50,000 - 100,000)'
    },
    'medium_city': {
        'min_population': 10000,
        'max_population': 50000,
        'color': 'blue',
        'icon': 'record',
        'size': 8,
        'label': 'Medium City (10,000 - 50,000)'
    },
    'small_city': {
        'min_population': 0,
        'max_population': 10000,
        'color': 'green',
        'icon': 'circle',
        'size': 6,
        'label': 'Small City (< 10,000)'
    }
}

# Map configuration
MAP_CONFIG = {
    'florida_center': {
        'lat': 27.8333,
        'lon': -81.717
    },
    'default_zoom': {
        'state': 7,
        'city': 10,
        'selected': 12
    },
    'tile_layers': [
        {
            'name': 'Street Map',
            'tiles': 'OpenStreetMap'
        },
        {
            'name': 'Satellite',
            'tiles': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            'attr': 'Esri'
        },
        {
            'name': 'Light Mode',
            'tiles': 'CartoDB positron',
            'attr': 'CartoDB'
        },
        {
            'name': 'Dark Mode',
            'tiles': 'CartoDB dark_matter',
            'attr': 'CartoDB'
        }
    ]
}

# API configuration
API_CONFIG = {
    'overpass_urls': [
        "http://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://z.overpass-api.de/api/interpreter"
    ],
    'timeout': 30,
    'bbox_sizes': [0.02, 0.03, 0.05]  # Different bounding box sizes to try
}

# UI configuration
UI_CONFIG = {
    'page_title': "FDOT City Data Explorer",
    'page_icon': "🗺️",
    'layout': "wide",
    'sidebar_state': "expanded",
    'map_height': 600,
    'table_height': 400,
    'max_cities_default': 50,
    'max_search_results': 15
}

# Data validation
DATA_VALIDATION = {
    'required_city_fields': ['geoid', 'name', 'latitude', 'longitude'],
    'required_street_fields': ['street_id', 'street_name', 'geometry'],
    'coordinate_bounds': {
        'florida': {
            'lat_min': 24.0,
            'lat_max': 31.5,
            'lon_min': -88.0,
            'lon_max': -79.5
        }
    }
}

# Export configuration
EXPORT_CONFIG = {
    'csv_encoding': 'utf-8',
    'json_indent': 2,
    'file_extensions': {
        'csv': '.csv',
        'json': '.json',
        'excel': '.xlsx'
    }
}

# Error messages
ERROR_MESSAGES = {
    'no_data': "No data available",
    'invalid_coordinates': "Invalid coordinates provided",
    'api_error': "API connection error",
    'data_processing_error': "Error processing data",
    'file_error': "Error reading file",
    'network_error': "Network connection error"
}

# Success messages
SUCCESS_MESSAGES = {
    'data_loaded': "Data loaded successfully",
    'export_complete': "Export completed successfully",
    'search_complete': "Search completed",
    'update_complete': "Update completed"
}

# Info messages
INFO_MESSAGES = {
    'loading': "Loading data...",
    'processing': "Processing data...",
    'searching': "Searching...",
    'exporting': "Exporting data...",
    'select_city': "Please select a city to view details",
    'fetch_data': "Press 'FETCH CITY' button to load data"
}