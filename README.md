# VC-Mapper - FDOT City Data Explorer

A Streamlit application for exploring city boundary data from the Florida Department of Transportation (FDOT) GIS API.

## Features

- **City Data Fetching**: Retrieve comprehensive city data from FDOT GIS API
- **City Search**: Search for cities by name with fuzzy matching
- **GEOID Lookup**: Get specific city data by Geographic Identifier (GEOID)
- **Data Visualization**: Display city data in formatted tables with summary statistics
- **Error Handling**: Robust error handling for API failures and data validation

## Data Source

This application uses the [FDOT GIS API](https://gis.fdot.gov/arcgis/rest/services/Admin_Boundaries/FeatureServer/7/query) to fetch city boundary data. The API provides:

- City names and full legal names
- Geographic identifiers (GEOID)
- Latitude and longitude coordinates
- Population data
- Land and water area measurements
- FIPS codes and administrative information
- Geometric boundary data

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd VC-Mapper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

## Usage

### Fetch All Cities
- Use the sidebar to select "Fetch All Cities"
- Set a limit on the number of cities to retrieve (1-1000)
- Click "Fetch Cities" to retrieve data from the FDOT GIS API

### Search Cities
- Select "Search Cities" from the sidebar
- Enter a city name to search for
- Set a limit on search results (1-50)
- Click "Search" to find matching cities

### Get City by GEOID
- Choose "Get City by GEOID" from the sidebar
- Enter a specific GEOID (e.g., 1264400 for Satellite Beach)
- Click "Get City" to retrieve the specific city data

## API Implementation

The application uses a custom `FDOTGISAPI` class (`fdot_api.py`) that provides:

### Core Methods

- `fetch_cities(limit=None)`: Retrieve all cities with optional limit
- `search_cities(query, limit=10)`: Search cities by name
- `get_city_by_geoid(geoid)`: Get specific city by GEOID

### Data Format

Each city object contains:
```python
{
    'name': 'City Name',
    'full_name': 'Full Legal Name',
    'geoid': 'Geographic Identifier',
    'latitude': 28.1787326,
    'longitude': -80.5994021,
    'population': 10109,
    'land_area': 7561145.0,
    'water_area': 3547858.0,
    'state_fips': '12',
    'place_fips': '64400',
    'lsad': '25',
    'class_fp': 'C1',
    'func_stat': 'A',
    'geometry': {...}  # ESRI geometry data
}
```

## Testing

Run the test suite to verify API functionality:

```bash
python -m pytest test_fdot_api.py -v
```

The tests cover:
- API client initialization
- City data fetching with and without limits
- Search functionality
- GEOID lookup
- Error handling
- Data formatting and validation

## Error Handling

The application includes comprehensive error handling for:
- Network connectivity issues
- API response parsing errors
- Invalid data formats
- Missing required fields
- Rate limiting and timeouts

## Dependencies

- `streamlit`: Web application framework
- `requests`: HTTP client for API calls
- `pandas`: Data manipulation and display
- `logging`: Application logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Data Attribution

City boundary data is provided by the Florida Department of Transportation GIS services. Please refer to their [terms of service](https://gis.fdot.gov/) for usage guidelines. 