"""
City View - UI components for city data display and interaction
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import logging
from typing import Dict, Optional
from models.city_model import City, CityCollection
from controllers.city_controller import CityController

logger = logging.getLogger(__name__)


class CityView:
    """
    View component for city data display and interaction
    """
    
    def __init__(self):
        """Initialize the city view"""
        self.city_controller = CityController()
    
    def create_smart_sidebar(self) -> tuple:
        """
        Create an enhanced sidebar with data source options
        
        Returns:
            Tuple of (action, parameters)
        """
        try:
            with st.sidebar:
                st.markdown('<div class="search-container">', unsafe_allow_html=True)
                
                st.markdown("### 🎯 Data Source")
                action = st.selectbox(
                    "Choose data source",
                    ["🌍 Fetch All Cities", "🔍 Search Cities", "📍 Get by GEOID"],
                    help="Select how you want to retrieve city data"
                )
                
                st.markdown("### ⚙️ Settings")
                
                # Different settings based on action
                if action == "🌍 Fetch All Cities":
                    limit = st.slider(
                        "Number of cities",
                        min_value=5,
                        max_value=500,
                        value=50,
                        step=5,
                        help="Limit the number of cities to fetch"
                    )
                    fetch_button = st.button("🚀 FETCH CITY", type="primary", use_container_width=True)
                    params = {"limit": limit, "button": fetch_button}
                    
                elif action == "🔍 Search Cities":
                    search_query = st.text_input(
                        "City name",
                        placeholder="e.g., Miami, Orlando, Tampa",
                        help="Enter part of a city name to search"
                    )
                    search_limit = st.slider(
                        "Max results",
                        min_value=1,
                        max_value=50,
                        value=15,
                        help="Maximum number of search results"
                    )
                    search_button = st.button("🔍 Search", type="primary", use_container_width=True)
                    params = {"query": search_query, "limit": search_limit, "button": search_button}
                    
                elif action == "📍 Get by GEOID":
                    geoid = st.text_input(
                        "GEOID",
                        placeholder="e.g., 1264400",
                        help="Enter the Geographic Identifier"
                    )
                    geoid_button = st.button("📍 Get City", type="primary", use_container_width=True)
                    params = {"geoid": geoid, "button": geoid_button}
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                return action, params
                
        except Exception as e:
            logger.error(f"Error creating smart sidebar: {e}")
            return "🌍 Fetch All Cities", {"limit": 50, "button": False}
    
    def display_city_data_sidebar(self, cities: CityCollection) -> None:
        """
        Display city data in the sidebar under controls
        
        Args:
            cities: Collection of cities to display
        """
        try:
            if not cities or len(cities) == 0:
                st.sidebar.warning("No city data available")
                return
            
            # Display the data in sidebar
            st.sidebar.subheader("📋 City Data and Statistics")
            
            # Convert to DataFrame for display
            df = cities.to_dataframe()
            st.sidebar.dataframe(df, use_container_width=True)
            
            # Show summary statistics in sidebar
            self._display_sidebar_statistics(cities)
            
        except Exception as e:
            logger.error(f"Error displaying city data in sidebar: {e}")
            st.sidebar.error("Error displaying city data")
    
    def _display_sidebar_statistics(self, cities: CityCollection) -> None:
        """Display summary statistics in sidebar"""
        st.sidebar.subheader("Summary Statistics")
        
        total_cities = len(cities)
        total_population = cities.get_total_population()
        avg_population = cities.get_average_population()
        
        st.sidebar.metric("Total Cities", total_cities)
        st.sidebar.metric("Total Population", f"{total_population:,}")
        st.sidebar.metric("Average Population", f"{avg_population:,.0f}")
    
    def display_city_data_main(self, cities: CityCollection, filters: Optional[Dict] = None) -> None:
        """
        Display city data in the main content area with filters
        
        Args:
            cities: Collection of cities to display
            filters: Optional filter criteria
        """
        try:
            if not cities or len(cities) == 0:
                st.warning("No city data available")
                return
            
            # Apply filters if provided
            if filters:
                cities = self.city_controller.filter_cities(cities, filters)
                if filters.get('sort_by'):
                    reverse = filters['sort_by'] in ["Population", "Land Area", "Water Area"]
                    cities = self.city_controller.sort_cities(cities, filters['sort_by'], reverse)
            
            # Convert to DataFrame for display
            df = cities.to_dataframe()
            
            # Display the data
            st.dataframe(df, use_container_width=True)
            
            # Show summary statistics
            self._display_main_statistics(cities)
            
        except Exception as e:
            logger.error(f"Error displaying city data in main area: {e}")
            st.error("Error displaying city data")
    
    def _display_main_statistics(self, cities: CityCollection) -> None:
        """Display summary statistics in main area"""
        st.subheader("Summary Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Cities", len(cities))
        
        with col2:
            total_population = cities.get_total_population()
            st.metric("Total Population", f"{total_population:,}")
        
        with col3:
            avg_population = cities.get_average_population()
            st.metric("Average Population", f"{avg_population:,.0f}")
    
    def create_filter_controls(self, cities: CityCollection) -> Dict:
        """
        Create filter controls for city data
        
        Args:
            cities: Collection of cities to create filters for
            
        Returns:
            Dictionary of filter values
        """
        try:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                max_pop = max(city.population for city in cities.cities) if cities.cities else 100000
                pop_filter = st.slider(
                    "Minimum Population", 
                    0, 
                    max_pop, 
                    0
                )
            
            with col2:
                # Get unique state FIPS for filter
                state_fips = list(set(city.state_fips for city in cities.cities if city.state_fips))
                state_filter = st.selectbox("State FIPS", ["All"] + sorted(state_fips))
            
            with col3:
                sort_by = st.selectbox(
                    "Sort by", 
                    ["Name", "Population", "Land Area", "Water Area"]
                )
            
            return {
                'min_population': pop_filter,
                'state_fips': state_filter,
                'sort_by': sort_by
            }
            
        except Exception as e:
            logger.error(f"Error creating filter controls: {e}")
            return {}
    
    def create_charts(self, cities: CityCollection) -> None:
        """
        Create interactive charts for city data analysis
        
        Args:
            cities: Collection of cities to analyze
        """
        try:
            if not cities or len(cities) == 0:
                st.info("📊 No data available for charts")
                return
            
            # Prepare data for charts
            df = cities.to_dataframe()
            df['population'] = pd.to_numeric(df['Population'], errors='coerce').fillna(0)
            df['land_area_km2'] = pd.to_numeric(df['Land Area (sq m)'], errors='coerce').fillna(0) / 1000000
            
            # Filter out cities with no name for better display
            df = df[df['Name'].notna() & (df['Name'] != '')]
            
            if len(df) == 0:
                st.warning("⚠️ No valid data available for charts")
                return
            
            col1, col2 = st.columns(2)
            
            with col1:
                self._create_population_histogram(df)
            
            with col2:
                self._create_top_cities_chart(df)
                
        except Exception as e:
            logger.error(f"Error creating charts: {e}")
            st.error(f"❌ Error creating charts: {str(e)}")
    
    def _create_population_histogram(self, df: pd.DataFrame) -> None:
        """Create population distribution histogram"""
        try:
            if df['population'].sum() > 0:
                fig_pop = px.histogram(
                    df, 
                    x='population', 
                    nbins=min(20, len(df)),
                    title="Population Distribution",
                    labels={'population': 'Population', 'count': 'Number of Cities'},
                    color_discrete_sequence=['#2a5298']
                )
                fig_pop.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#2a5298'
                )
                st.plotly_chart(fig_pop, use_container_width=True)
            else:
                st.info("📊 No population data available for histogram")
        except Exception as e:
            logger.error(f"Error creating population histogram: {e}")
    
    def _create_top_cities_chart(self, df: pd.DataFrame) -> None:
        """Create top cities by population chart"""
        try:
            if len(df) > 0 and df['population'].sum() > 0:
                top_cities = df.nlargest(min(10, len(df)), 'population')
                if len(top_cities) > 0:
                    fig_top = px.bar(
                        top_cities, 
                        x='population', 
                        y='Name',
                        orientation='h',
                        title="Top Cities by Population",
                        labels={'population': 'Population', 'Name': 'City'},
                        color='population',
                        color_continuous_scale='Blues'
                    )
                    fig_top.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#2a5298',
                        yaxis={'categoryorder': 'total ascending'}
                    )
                    st.plotly_chart(fig_top, use_container_width=True)
                else:
                    st.info("📊 No cities available for ranking")
            else:
                st.info("📊 No population data available for ranking")
        except Exception as e:
            logger.error(f"Error creating top cities chart: {e}")
    
    def display_summary_statistics(self, cities: CityCollection) -> None:
        """
        Display comprehensive summary statistics
        
        Args:
            cities: Collection of cities to analyze
        """
        try:
            if not cities or len(cities) == 0:
                st.warning("No city data available for statistics")
                return
            
            st.markdown("### 📋 Summary Statistics")
            
            # Get statistics from controller
            stats = self.city_controller.get_city_statistics(cities)
            
            if not stats:
                st.error("Unable to calculate statistics")
                return
            
            # Statistics grid
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("🏙️ Total Cities", stats['total_cities'])
                st.metric("👥 Total Population", f"{stats['total_population']:,}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("📊 Average Population", f"{stats['average_population']:,.0f}")
                st.metric("📍 Median Population", f"{stats['median_population']:,}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("🏞️ Total Land Area", f"{stats['total_land_area_km2']:.1f} km²")
                st.metric("🌊 Total Water Area", f"{stats['total_water_area_km2']:.1f} km²")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                largest = stats['largest_city']
                smallest = stats['smallest_city']
                if largest:
                    st.metric("🏆 Largest City", largest.name, f"{largest.population:,}")
                if smallest:
                    st.metric("🏘️ Smallest City", smallest.name, f"{smallest.population:,}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Top cities showcase
            self._display_top_cities_showcase(cities)
            
        except Exception as e:
            logger.error(f"Error displaying summary statistics: {e}")
            st.error("Error calculating statistics")
    
    def _display_top_cities_showcase(self, cities: CityCollection) -> None:
        """Display top cities in styled cards"""
        try:
            st.markdown("---")
            st.markdown("### 🏆 Top Cities")
            
            top_5 = cities.get_top_cities(5)
            for i, city in enumerate(top_5, 1):
                st.markdown(f"""
                <div class="city-card">
                    <h4>#{i} {city.name}</h4>
                    <p><strong>Population:</strong> {city.population:,} | 
                       <strong>GEOID:</strong> {city.geoid} | 
                       <strong>Land Area:</strong> {city.land_area/1000000:.2f} km²</p>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            logger.error(f"Error displaying top cities showcase: {e}")
    
    def display_welcome_screen(self) -> None:
        """Display welcome screen when no data is loaded"""
        try:
            st.markdown("### 🌟 Welcome to FDOT City Data Explorer")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("""
                <div class="search-container">
                    <h4>🚀 Getting Started</h4>
                    <p>Explore Florida city data with our powerful tools:</p>
                    <ul>
                        <li>🗺️ <strong>Interactive Maps</strong> - Visualize cities on modern map interfaces</li>
                        <li>📊 <strong>Data Tables</strong> - Browse detailed city information</li>
                        <li>📈 <strong>Analytics</strong> - Discover insights with charts and statistics</li>
                        <li>🔍 <strong>Smart Search</strong> - Find cities by name or GEOID</li>
                    </ul>
                    <p><strong>👈 Start by selecting a data source from the sidebar!</strong></p>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            logger.error(f"Error displaying welcome screen: {e}")
    
    def handle_data_fetch(self, action: str, params: Dict) -> bool:
        """
        Handle data fetching and display appropriate messages
        
        Args:
            action: The action to perform
            params: Action parameters
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with st.spinner("🔄 Loading data..."):
                return self.city_controller.handle_data_fetch_action(action, params)
        except Exception as e:
            logger.error(f"Error handling data fetch: {e}")
            st.error(f"❌ Error: {str(e)}")
            return False