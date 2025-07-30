# 🚗 V/C Ratio Calculator

A comprehensive web-based dashboard tool for calculating and visualizing Volume/Capacity (V/C) ratios for roadway segments in Florida counties. This tool automates the process of traffic analysis and growth projections for transportation planning.

## 📋 Project Overview

This application is designed for mobility planning and transportation consulting firms to:

- **Automatically pull traffic volume data** from FDOT Traffic Online
- **Allow manual upload** of Placer.ai traffic volume data (CSV format)
- **Apply user-supplied growth rates** from TAZ spreadsheets to project 20-year future traffic
- **Calculate current and future V/C ratios** using roadway classification capacities
- **Display color-coded maps and tables** showing roadway segment performance

## ✨ Key Features

### 🔄 Data Integration
- **FDOT Traffic Online API** integration for automated data retrieval
- **Real-time data display** with detailed statistics and metadata
- **TAZ-based growth projections** with customizable rates
- **Shapefile/geodatabase support** for roadway segment data

### 📊 Analysis & Visualization
- **Raw FDOT data display** with detailed data information
- **Interactive maps** with color-coded V/C ratios
- **Statistical analysis** with summary metrics and distributions
- **Growth projections** with customizable time horizons
- **Real-time calculations** and updates

### 🎨 Color-Coded Results
- 🟢 **Green**: V/C < 0.7 (Good - Adequate capacity)
- 🟡 **Yellow**: V/C 0.7-0.9 (Fair - Approaching capacity)
- 🔴 **Red**: V/C 0.9-1.0 (Poor - At or near capacity)
- 🟣 **Purple**: V/C > 1.0 (Critical - Over capacity)

### 💾 Export Capabilities
- **CSV export** of detailed results
- **Excel export** with multiple worksheets
- **Interactive charts** and visualizations
- **Downloadable reports** with timestamps

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Windows, macOS, or Linux

### Installation

#### Option 1: Using Python venv + pip

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd VC-Mapper
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - **Windows:**
     ```bash
     .\venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application:**
   ```bash
   streamlit run app.py
   ```

#### Option 2: Using Conda/Mamba

1. **Create the environment:**
   ```bash
   conda env create -f environment.yml
   # or, if using mamba
   mamba env create -f environment.yml
   ```

2. **Activate the environment:**
   ```bash
   conda activate vc-mapper
   ```

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```

### Usage

1. **Open your web browser** and navigate to `http://localhost:8501`
2. **Configure settings** in the sidebar:
   - Select your target county
   - Set growth rate and projection years
   - Choose data source (FDOT API or manual entry)
3. **Test FDOT API** (optional): Click "Test FDOT API" to verify connection
4. **Click "Load Data"** to begin analysis
5. **Review raw FDOT data** displayed in the dashboard
6. **Explore V/C analysis** through interactive maps, charts, and tables
7. **Export results** in your preferred format

### Testing the Application

You can test the FDOT API integration using the provided test script:

```bash
python test_fdot_api.py
```

This will verify:
- ✅ FDOT API connectivity
- ✅ Data retrieval and processing
- ✅ Streamlit integration
- ✅ Error handling and fallbacks

## 📁 Project Structure

```
VC-Mapper/
├── app.py                 # Main Streamlit application
├── utils.py              # Utility functions and classes
├── config.py             # Configuration settings
├── fdot_api.py           # FDOT ArcGIS REST API integration
├── test_fdot_api.py      # API testing script
├── requirements.txt      # Python dependencies
├── environment.yml       # Conda environment
├── README.md            # This file
└── venv/                # Virtual environment (created during setup)
```

## 🔧 Configuration

### County Settings
The application supports multiple Florida counties:
- **Palm Beach County** (default)
- **Broward County**
- **Miami-Dade County**
- **Monroe County**

### Growth Projections
- **Uniform growth rates**: Apply the same growth rate to all segments
- **TAZ-based growth**: Use Transportation Analysis Zone specific rates
- **Customizable time horizons**: 5-30 year projections

### Data Sources
- **FDOT Traffic Online**: Automated data retrieval from ArcGIS REST API
- **Manual Entry**: For testing and small datasets

## 📊 Data Requirements

### Required Data
- **Roadway segment data** (shapefile or geodatabase)
- **Traffic volume data** (FDOT or Placer.ai format)
- **Capacity tables** by functional classification
- **TAZ growth factors** (optional, for advanced projections)

### Supported Formats
- **CSV files** with traffic volume data
- **Excel files** (.xlsx, .xls)
- **Shapefiles** (.shp) for geographic data
- **GeoJSON** files for web-based mapping

## 🔌 API Integration

### FDOT Traffic Online
The application integrates with FDOT's Traffic Online system using their ArcGIS REST API:
- **Base URL**: `https://devgis.fdot.gov/arcgis/rest/services/fto/fto_DEV/MapServer`
- **Layers**: 
  - Layer 0: Traffic Monitoring Sites
  - Layer 1: AADT (Annual Average Daily Traffic) Data
- **Authentication**: Public API, no authentication required
- **Rate limiting**: Configured for API compliance
- **Fallback**: Sample data when API is unavailable

### FDOT API Features
- **Real-time data**: Live traffic volume data from FDOT
- **County filtering**: Filter data by specific counties
- **Year selection**: Choose data from different years
- **Geographic data**: Includes latitude/longitude coordinates
- **Error handling**: Graceful fallback to sample data

### Placer.ai Integration
Support for Placer.ai traffic data:
- **CSV format** with standardized column names
- **Automatic validation** of data quality
- **Processing pipeline** for data standardization

## 🛠️ Development

### Adding New Counties
1. Update `config.py` with county coordinates and settings
2. Add county-specific growth rates
3. Configure FDOT district mapping

### Customizing Capacity Tables
1. Modify `CAPACITY_TABLE` in `config.py`
2. Add new functional classifications as needed
3. Update capacity values based on local standards

### Extending Analysis
1. Add new calculation methods in `utils.py`
2. Create additional visualization components
3. Implement new export formats

## 📈 Methodology

### V/C Ratio Calculation
```
V/C Ratio = Current Traffic Volume / Roadway Capacity
```

### Growth Projections
```
Future Volume = Current Volume × (1 + Growth Rate)^Years
```

### Status Classification
- **Good**: V/C < 0.7 (adequate capacity)
- **Fair**: 0.7 ≤ V/C < 0.9 (approaching capacity)
- **Poor**: 0.9 ≤ V/C ≤ 1.0 (at or near capacity)
- **Critical**: V/C > 1.0 (over capacity)

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-feature`
3. **Make your changes** and add tests
4. **Commit your changes**: `git commit -am 'Add new feature'`
5. **Push to the branch**: `git push origin feature/new-feature`
6. **Submit a pull request**

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- **Documentation**: Check this README and inline code comments
- **Issues**: Create an issue in the repository
- **Email**: Contact the development team

## 🔄 Version History

- **v1.0.0**: Initial release with basic V/C ratio calculation
- **v1.1.0**: Added interactive mapping and export capabilities
- **v1.2.0**: Enhanced with TAZ-based growth projections
- **v1.3.0**: Improved UI and added comprehensive documentation

---

**Note**: This tool is designed for transportation planning professionals. Always validate results and consult with local transportation authorities for official analysis. 