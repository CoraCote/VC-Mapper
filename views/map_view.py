"""
Map View - UI components for map visualization using Mapbox
"""

from typing import Optional, Dict, Any
import streamlit as st
import pydeck as pdk
import logging
from models.city_model import City, CityCollection
from models.street_model import StreetCollection
from models.traffic_model import TrafficCollection
from controllers.mapbox_controller import MapboxController
from controllers.city_controller import CityController
from controllers.traffic_controller import TrafficController

logger = logging.getLogger(__name__)


class MapView:
    """
    View component for map visualization using Mapbox
    """
    
    def __init__(self, mapbox_token: str = "pk.eyJ1IjoiZGFuaWVsMDkyNyIsImEiOiJjbWRtNWQ4aWEwMTM1MmpxNGZxd2E0bmpnIn0.iwPMtSv1shtLXBi8WdxfgA"):
        """
        Initialize the map view with Mapbox integration
        
        Args:
            mapbox_token: Mapbox API token for map rendering
        """
        self.mapbox_controller = MapboxController(mapbox_token)
        self.city_controller = CityController()
        self.traffic_controller = TrafficController()
    
    def display_florida_only_map(self) -> None:
        """
        Display a map showing only the Florida state boundary using Mapbox
        """
        try:
            # Create Florida map with real boundary data
            deck = self.mapbox_controller.create_florida_map()
            
            # Display the map
            with st.container():
                st.markdown('<div class="map-container">', unsafe_allow_html=True)
                st.info("📍 Now showing Florida with **real boundary data** from ArcGIS API! Press the 'FETCH CITY' button from the sidebar to load city data and explore specific locations.")
                
                # Display map style selector
                col1, col2 = st.columns([3, 1])
                with col2:
                    map_style = st.selectbox(
                        "Map Style",
                        options=[
                            'mapbox://styles/mapbox/streets-v11',
                            'mapbox://styles/mapbox/satellite-v9',
                            'mapbox://styles/mapbox/light-v10',
                            'mapbox://styles/mapbox/dark-v10'
                        ],
                        format_func=lambda x: {
                            'mapbox://styles/mapbox/streets-v11': 'Streets',
                            'mapbox://styles/mapbox/satellite-v9': 'Satellite',
                            'mapbox://styles/mapbox/light-v10': 'Light',
                            'mapbox://styles/mapbox/dark-v10': 'Dark'
                        }[x],
                        key="florida_map_style"
                    )
                
                # Update deck with selected style if changed
                if hasattr(st.session_state, 'florida_map_style') and st.session_state.florida_map_style != deck.map_style:
                    deck.map_style = map_style
                
                # Display the Mapbox map using PyDeck
                st.pydeck_chart(deck, use_container_width=True, height=600)
                
                # Show data source info
                st.success("🌍 **Real-time Florida boundary data** fetched from ArcGIS API")
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            logger.error(f"Error displaying Florida only map: {e}")
            st.error("❌ Error displaying map. Please try refreshing the page.")
            st.error(f"Details: {str(e)}")
    
    def display_cities_on_map(self, cities: CityCollection) -> None:
        """
        Display cities on an enhanced interactive Mapbox map with options
        
        Args:
            cities: Collection of cities to display
        """
        try:
            if not cities or len(cities) == 0:
                st.error("🚫 No city data available to display on map")
                return
            
            # Filter cities with valid coordinates
            valid_cities = CityCollection()
            valid_cities.cities = cities.get_valid_cities()
            
            if len(valid_cities) == 0:
                st.error("🚫 No cities with valid coordinates found")
                return
            
            # Initialize session state for selected city
            if 'selected_city' not in st.session_state:
                st.session_state.selected_city = None
            
            # Map configuration options
            selected_city, show_only_selected, show_streets, map_style, traffic_options = self._render_mapbox_controls(valid_cities)
            
            # Get streets data if needed
            streets = None
            if show_streets and selected_city:
                from controllers.street_controller import StreetController
                street_controller = StreetController()
                streets = street_controller.get_streets_for_city(selected_city)
            
            # Get traffic data if needed
            traffic_data = None
            if traffic_options['show_traffic_data']:
                traffic_data = self._get_or_fetch_traffic_data(
                    county_filter=traffic_options.get('county_filter'),
                    roadway_filter=traffic_options.get('roadway_filter'),
                    max_records=traffic_options.get('max_records', 1000),
                    force_refresh=traffic_options.get('force_refresh', False)
                )
            
            # Create Mapbox map
            deck = self.mapbox_controller.create_florida_map(
                cities=valid_cities,
                selected_city=selected_city,
                streets=streets,
                traffic_data=traffic_data,
                show_traffic=traffic_options['show_traffic_data'],
                show_traffic_heatmap=traffic_options.get('show_heatmap', False),
                traffic_filter_level=traffic_options.get('traffic_level_filter'),
                show_only_selected=show_only_selected,
                map_style=map_style
            )
            
            # Display map with statistics
            self._display_mapbox_with_stats(deck, valid_cities, selected_city)
            
        except Exception as e:
            logger.error(f"Error displaying cities on map: {e}")
            st.error("❌ Error displaying map. Please try refreshing the page.")
            st.error(f"Details: {str(e)}")
    
    def _render_mapbox_controls(self, valid_cities: CityCollection) -> tuple:
        """
        Render Mapbox map control options including traffic data controls
        
        Args:
            valid_cities: Collection of valid cities
            
        Returns:
            Tuple of (selected_city, show_only_selected, show_streets, map_style, traffic_options)
        """
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # City selector
            city_options = ["View All Cities"] + [city.get_display_name() for city in valid_cities.cities]
            selected_option = st.selectbox(
                "🎯 Select View",
                city_options,
                index=0,
                help="Choose 'View All Cities' or select a specific city for detailed view"
            )
            
            if selected_option == "View All Cities":
                st.session_state.selected_city = None
                selected_city = None
                show_only_selected = False
            else:
                # Find the selected city
                selected_index = city_options.index(selected_option) - 1
                selected_city = valid_cities.cities[selected_index]
                st.session_state.selected_city = selected_city.to_dict()
                show_only_selected = True
        
        with col2:
            if selected_city:
                show_streets = st.checkbox("🛣️ Show Streets", value=True, help="Display street network for selected city")
            else:
                show_streets = False
                st.info("📍 Select a specific city to view streets")
        
        with col3:
            # Map style selector
            map_style = st.selectbox(
                "🗺️ Map Style",
                options=[
                    'mapbox://styles/mapbox/streets-v11',
                    'mapbox://styles/mapbox/satellite-v9',
                    'mapbox://styles/mapbox/light-v10',
                    'mapbox://styles/mapbox/dark-v10'
                ],
                format_func=lambda x: {
                    'mapbox://styles/mapbox/streets-v11': 'Streets',
                    'mapbox://styles/mapbox/satellite-v9': 'Satellite',
                    'mapbox://styles/mapbox/light-v10': 'Light',
                    'mapbox://styles/mapbox/dark-v10': 'Dark'
                }[x],
                index=0,
                help="Select Mapbox map style"
            )
        
        with col4:
            # Traffic data controls
            show_traffic_data = st.checkbox("🚦 Show Traffic", value=False, 
                                           help="Display FDOT Annual Average Daily Traffic (AADT) data")
        
        # Initialize traffic options with default values
        traffic_options = {
            'show_traffic_data': show_traffic_data,
            'show_heatmap': False,
            'traffic_level_filter': None,
            'county_filter': None,
            'roadway_filter': None,
            'max_records': 1000,
            'force_refresh': False
        }
        
        if show_traffic_data:
            st.markdown("### 🚦 Traffic Data Controls")
            
            # Create traffic control columns
            traffic_col1, traffic_col2, traffic_col3, traffic_col4 = st.columns(4)
            
            with traffic_col1:
                show_heatmap = st.checkbox("🌡️ AADT Heatmap", value=False,
                                         help="Show Annual Average Daily Traffic as heatmap overlay")
                
                traffic_level_filter = st.selectbox(
                    "📊 Traffic Level Filter",
                    options=['All', 'Low', 'Moderate', 'High', 'Heavy'],
                    index=0,
                    help="Filter traffic data by congestion level"
                )
            
            with traffic_col2:
                county_filter = st.text_input("🏢 County Filter", 
                                            placeholder="e.g., Miami-Dade",
                                            help="Filter by county name (optional)")
                
                roadway_filter = st.text_input("🛣️ Roadway Filter",
                                             placeholder="e.g., I-95",
                                             help="Filter by roadway name (optional)")
            
            with traffic_col3:
                max_records = st.number_input("📊 Max Records", 
                                            min_value=100, max_value=5000, 
                                            value=1000, step=100,
                                            help="Maximum number of traffic segments to load")
                
                force_refresh = st.button("🔄 Refresh Traffic Data",
                                        help="Force refresh of traffic data from server")
            
            with traffic_col4:
                # Traffic data status and info
                traffic_data = self.traffic_controller.get_session_traffic_data()
                if traffic_data:
                    stats = self.traffic_controller.get_traffic_statistics(traffic_data)
                    st.metric("📍 Traffic Segments", stats.get('total_segments', 0))
                    st.metric("🚗 Avg Volume", f"{stats.get('avg_volume', 0):,.0f}")
                else:
                    st.info("👆 Enable traffic data above to load FDOT AADT information")
            
            # Update traffic options
            traffic_options.update({
                'show_heatmap': show_heatmap,
                'traffic_level_filter': traffic_level_filter if traffic_level_filter != 'All' else None,
                'county_filter': county_filter if county_filter.strip() else None,
                'roadway_filter': roadway_filter if roadway_filter.strip() else None,
                'max_records': max_records,
                'force_refresh': force_refresh
            })
        
        return selected_city, show_only_selected, show_streets, map_style, traffic_options
    
    def _display_mapbox_with_stats(self, deck: pdk.Deck, valid_cities: CityCollection, selected_city: Optional[City]) -> None:
        """
        Display Mapbox map with statistics and interaction
        
        Args:
            deck: PyDeck map object
            valid_cities: Collection of valid cities
            selected_city: Currently selected city
        """
        try:
            # Display map in container with custom styling
            with st.container():
                st.markdown('<div class="map-container">', unsafe_allow_html=True)
                
                # Map header with statistics
                self._display_map_statistics(valid_cities)
                
                st.markdown("---")
                
                # Display the Mapbox map using PyDeck
                st.pydeck_chart(deck, use_container_width=True, height=600)
                
                # Show selected city details
                if selected_city:
                    self._display_selected_city_details(selected_city)
                
                # Show data source info
                st.success("🌍 **Enhanced with Mapbox** - Real-time Florida boundary data from ArcGIS API")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            logger.error(f"Error displaying Mapbox map with stats: {e}")
            st.error("❌ Error displaying map. Please try refreshing the page.")
    
    def _display_map_statistics(self, cities: CityCollection) -> None:
        """Display map statistics header"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏙️ Cities Mapped", len(cities))
        with col2:
            total_pop = cities.get_total_population()
            st.metric("👥 Total Population", f"{total_pop:,}")
        with col3:
            avg_pop = cities.get_average_population()
            st.metric("📊 Average Population", f"{avg_pop:,.0f}")
        with col4:
            total_area = cities.get_total_land_area()
            st.metric("🏞️ Total Land Area", f"{total_area/1000000:.1f} km²")
    
    def _display_selected_city_details(self, selected_city: City) -> None:
        """Display details for selected city"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"🎯 **Selected City:** {selected_city.name}")
            st.metric("👥 Population", f"{selected_city.population:,}")
        with col2:
            st.metric("🏞️ Land Area", f"{selected_city.land_area/1000000:.2f} km²")
            st.metric("📍 Coordinates", f"{selected_city.latitude:.4f}, {selected_city.longitude:.4f}")
        with col3:
            st.metric("🆔 GEOID", selected_city.geoid)
            st.metric("🌊 Water Area", f"{selected_city.water_area/1000000:.2f} km²")
    
    def _get_or_fetch_traffic_data(self, 
                                  county_filter: Optional[str] = None,
                                  roadway_filter: Optional[str] = None,
                                  max_records: int = 1000,
                                  force_refresh: bool = False) -> Optional[TrafficCollection]:
        """
        Get traffic data from session or fetch from API
        
        Args:
            county_filter: Optional county name to filter results
            roadway_filter: Optional roadway name to filter results
            max_records: Maximum number of records to fetch
            force_refresh: Force refresh of cached data
            
        Returns:
            TrafficCollection with traffic data or None if error
        """
        try:
            with st.spinner("🚦 Loading FDOT AADT data..."):
                # Fetch traffic data
                traffic_data = self.traffic_controller.fetch_and_cache_traffic_data(
                    county_filter=county_filter,
                    roadway_filter=roadway_filter,
                    max_records=max_records,
                    force_refresh=force_refresh
                )
                
                if traffic_data and len(traffic_data) > 0:
                    # Display success message with statistics
                    stats = self.traffic_controller.get_traffic_statistics(traffic_data)
                    st.success(f"✅ Loaded {stats['total_segments']} AADT segments "
                             f"(Avg AADT: {stats['avg_volume']:,.0f} vehicles/day)")
                    
                    # Display traffic level breakdown
                    level_counts = stats['traffic_levels']
                    if any(level_counts.values()):
                        cols = st.columns(4)
                        level_colors = {
                            'Low': '🟢', 'Moderate': '🟡', 'High': '🟠', 'Heavy': '🔴'
                        }
                        for idx, (level, count) in enumerate(level_counts.items()):
                            if count > 0:
                                with cols[idx % 4]:
                                    st.metric(f"{level_colors.get(level, '⚪')} {level}", count)
                    
                    return traffic_data
                else:
                    st.warning("⚠️ No traffic data found with current filters")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching traffic data: {e}")
            st.error("❌ Failed to load traffic data. Please try again.")
            return None
    
    def display_traffic_data_tab(self) -> None:
        """
        Display traffic data analysis tab
        """
        try:
            st.markdown("### 🚦 FDOT AADT Traffic Analysis")
            
            # Get traffic data from session
            traffic_data = self.traffic_controller.get_session_traffic_data()
            
            if not traffic_data:
                st.info("👆 Enable traffic data in the map view above to see AADT analysis")
                
                # Option to fetch traffic data directly
                if st.button("🚦 Load AADT Data Now"):
                    traffic_data = self._get_or_fetch_traffic_data()
                
                if not traffic_data:
                    return
            
            # Traffic data analysis interface
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Traffic statistics
                stats = self.traffic_controller.get_traffic_statistics(traffic_data)
                self._display_traffic_statistics(stats)
                
                # AADT data table
                st.markdown("#### 📊 AADT Data Table")
                self._display_traffic_data_table(traffic_data)
            
            with col2:
                # Traffic controls and filters
                st.markdown("#### 🎛️ Analysis Controls")
                filters = self._create_traffic_filters(traffic_data)
                
                # Export options
                st.markdown("#### 💾 Export Options")
                self._create_traffic_export_options(traffic_data)
                
                # Data quality information
                st.markdown("#### ℹ️ Data Info")
                self._display_traffic_data_info(traffic_data)
            
        except Exception as e:
            logger.error(f"Error displaying traffic data tab: {e}")
            st.error("❌ Error displaying traffic analysis")
    
    def _display_traffic_statistics(self, stats: Dict) -> None:
        """Display AADT statistics overview"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🛣️ Total Segments", stats.get('total_segments', 0))
            st.metric("🚗 Total AADT", f"{stats.get('total_volume', 0):,}")
        
        with col2:
            st.metric("📈 Avg AADT", f"{stats.get('avg_volume', 0):,.0f}")
            traffic_levels = stats.get('traffic_levels', {})
            st.metric("🔴 Heavy Traffic", traffic_levels.get('Heavy', 0))
        
        with col3:
            st.metric("🟠 High Traffic", traffic_levels.get('High', 0))
            st.metric("🟡 Moderate Traffic", traffic_levels.get('Moderate', 0))
        
        with col4:
            st.metric("🟢 Low Traffic", traffic_levels.get('Low', 0))
            if stats.get('last_updated'):
                from datetime import datetime
                try:
                    updated_time = datetime.fromisoformat(stats['last_updated'])
                    st.metric("🕒 Updated", updated_time.strftime('%H:%M'))
                except:
                    st.metric("🕒 Updated", "Recent")
    
    def _display_traffic_data_table(self, traffic_data: TrafficCollection) -> None:
        """Display AADT data in tabular format"""
        import pandas as pd
        
        # Convert traffic data to DataFrame
        data_for_table = []
        for traffic in traffic_data.traffic_data[:100]:  # Limit to 100 rows for performance
            data_for_table.append({
                'Roadway': traffic.roadway_name,
                'From': traffic.desc_from,
                'To': traffic.desc_to,
                'County': traffic.county,
                'District': traffic.district,
                'AADT': traffic.aadt,
                'AADT Flag': traffic.aadt_flag,
                'Traffic Level': traffic.get_traffic_level(),
                'Year': traffic.year,
                'Data Quality': traffic.data_quality
            })
        
        if data_for_table:
            df = pd.DataFrame(data_for_table)
            st.dataframe(df, use_container_width=True, height=400)
            
            if len(traffic_data) > 100:
                st.info(f"📊 Showing first 100 of {len(traffic_data)} AADT segments")
        else:
            st.warning("No traffic data to display")
    
    def _create_traffic_filters(self, traffic_data: TrafficCollection) -> Dict:
        """Create traffic data filter controls"""
        filters = {}
        
        # County filter
        counties = traffic_data.get_unique_counties()
        if counties:
            filters['county'] = st.selectbox(
                "🏢 Filter by County",
                ['All'] + counties,
                key="traffic_county_filter"
            )
        
        # Roadway filter
        roadways = traffic_data.get_unique_roadways()[:20]  # Limit for performance
        if roadways:
            filters['roadway'] = st.selectbox(
                "🛣️ Filter by Roadway",
                ['All'] + roadways,
                key="traffic_roadway_filter"
            )
        
        # Traffic level filter
        filters['traffic_level'] = st.selectbox(
            "📊 Filter by Traffic Level",
            ['All', 'Low', 'Moderate', 'High', 'Heavy'],
            key="traffic_level_filter"
        )
        
        return filters
    
    def _create_traffic_export_options(self, traffic_data: TrafficCollection) -> None:
        """Create traffic data export options"""
        export_format = st.selectbox(
            "📁 Export Format",
            ['GeoJSON', 'JSON', 'CSV'],
            key="traffic_export_format"
        )
        
        if st.button("💾 Export Traffic Data"):
            try:
                exported_data = self.traffic_controller.export_traffic_data(
                    traffic_data, export_format.lower()
                )
                
                # Create download
                filename = f"traffic_data.{export_format.lower()}"
                st.download_button(
                    label=f"⬇️ Download {export_format}",
                    data=exported_data,
                    file_name=filename,
                    mime="application/json" if export_format != "CSV" else "text/csv"
                )
                
            except Exception as e:
                st.error(f"Export failed: {e}")
    
    def _display_traffic_data_info(self, traffic_data: TrafficCollection) -> None:
        """Display traffic data information and metadata"""
        st.info(f"📊 **Data Source:** FDOT Annual Average Daily Traffic (AADT)")
        st.info(f"🔢 **Total Segments:** {len(traffic_data)}")
        
        if traffic_data.last_updated:
            st.info(f"🕒 **Last Updated:** {traffic_data.last_updated}")
        
        # Data quality overview
        quality_counts = {}
        for traffic in traffic_data.traffic_data:
            quality = traffic.data_quality
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        if quality_counts:
            st.markdown("**Data Quality:**")
            for quality, count in quality_counts.items():
                if quality != 'Unknown':
                    st.write(f"• {quality}: {count} segments")