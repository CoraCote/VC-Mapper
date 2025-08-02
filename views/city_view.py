"""
City View - UI components for city data display and interaction
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import logging
from typing import Dict, Optional
from models.city_model import City, CityCollection, TrafficDataCollection
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
                    st.info("⚠️ Will fetch ALL cities from the database (no limit). This may take some time...")
                    
                    save_to_file = st.checkbox(
                        "Save to JSON file",
                        value=True,  # Auto-checked by default
                        help="Save the fetched cities data to a local JSON file"
                    )
                    
                    fetch_button = st.button("🚀 FETCH ALL CITIES", type="primary", use_container_width=True)
                    params = {
                        "limit": None,  # Always no limit
                        "button": fetch_button, 
                        "fetch_all": True,  # Always fetch all
                        "save_to_file": save_to_file,
                        "fetch_traffic": True
                    }

                elif action == "🔍 Search Cities":
                    search_query = st.text_input(
                        "City name",
                        placeholder="e.g., Miami, Orlando, Tampa",
                        help="Enter the name of the city to search for"
                    )
                    search_button = st.button("🔍 SEARCH", type="primary", use_container_width=True)
                    params = {"query": search_query, "button": search_button}
                    

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
            
            # Removed "📋 City Data and Statistics" section as requested
            # This method is kept for compatibility but no longer displays sidebar data
            
        except Exception as e:
            logger.error(f"Error displaying city data in sidebar: {e}")
            st.sidebar.error("Error displaying city data")
    
    def _display_sidebar_statistics(self, cities: CityCollection) -> None:
        """Display summary statistics in sidebar - REMOVED as requested"""
        # This method is kept for compatibility but no longer displays statistics
        pass
    
    def display_city_data_main(self, cities: CityCollection, filters: Optional[Dict] = None) -> None:
        """
        Display city data in the main content area with filters and pagination
        
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
            
            # Add export functionality
            self._add_export_buttons(df, "City Data", "cities")
            
            # Implement pagination for city data table
            self._display_paginated_data_table(df, "city_data")
            
            # Summary Statistics section removed as requested
            
        except Exception as e:
            logger.error(f"Error displaying city data in main area: {e}")
            st.error("Error displaying city data")
    
    def _display_main_statistics(self, cities: CityCollection) -> None:
        """Display summary statistics in main area - REMOVED as requested"""
        # This method is kept for compatibility but no longer displays statistics
        pass
    
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
        Display comprehensive summary statistics - REMOVED as requested
        
        Args:
            cities: Collection of cities to analyze
        """
        # This method is kept for compatibility but no longer displays summary statistics
        # as requested by the user to remove "Summary Statistics" sections
        pass
    
    def _display_paginated_data_table(self, df, table_key: str, 
                                     items_per_page: int = 20) -> None:
        """
        Display paginated data table with navigation controls
        
        Args:
            df: DataFrame to display
            table_key: Unique key for the table session state
            items_per_page: Number of items to display per page
        """
        try:
            if df.empty:
                st.info("No data to display")
                return
            
            # Initialize session state for pagination
            page_key = f"{table_key}_page"
            if page_key not in st.session_state:
                st.session_state[page_key] = 0
            
            total_rows = len(df)
            total_pages = (total_rows - 1) // items_per_page + 1
            
            # Pagination controls
            if total_pages > 1:
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                
                with col1:
                    if st.button("⏪ First", key=f"{table_key}_first", 
                               disabled=st.session_state[page_key] == 0):
                        st.session_state[page_key] = 0
                        st.rerun()
                
                with col2:
                    if st.button("◀ Previous", key=f"{table_key}_prev", 
                               disabled=st.session_state[page_key] == 0):
                        st.session_state[page_key] -= 1
                        st.rerun()
                
                with col3:
                    st.write(f"Page {st.session_state[page_key] + 1} of {total_pages} "
                            f"({total_rows:,} total records)")
                
                with col4:
                    if st.button("Next ▶", key=f"{table_key}_next", 
                               disabled=st.session_state[page_key] >= total_pages - 1):
                        st.session_state[page_key] += 1
                        st.rerun()
                
                with col5:
                    if st.button("Last ⏩", key=f"{table_key}_last", 
                               disabled=st.session_state[page_key] >= total_pages - 1):
                        st.session_state[page_key] = total_pages - 1
                        st.rerun()
            
            # Calculate start and end indices for current page
            start_idx = st.session_state[page_key] * items_per_page
            end_idx = min(start_idx + items_per_page, total_rows)
            
            # Display current page data
            page_df = df.iloc[start_idx:end_idx]
            st.dataframe(page_df, use_container_width=True, height=400)
            
            # Show items count for current page
            if total_pages > 1:
                st.caption(f"Showing items {start_idx + 1}-{end_idx} of {total_rows}")
            
        except Exception as e:
            logger.error(f"Error displaying paginated table: {e}")
            st.error("Error displaying table data")
    
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
                        <li>🚦 <strong>Traffic Data</strong> - Fetch and analyze traffic information</li>
                        <li>💾 <strong>Data Export</strong> - Save data as JSON files locally</li>
                    </ul>
                    <h5>✨ New Features:</h5>
                    <ul>
                        <li>🌍 <strong>Fetch ALL Cities</strong> - No more limits when fetching city data</li>
                        <li>🔍 <strong>Search Cities</strong> - Search for specific cities by name</li>
                        <li>🚦 <strong>Traffic Data Integration</strong> - Fetch Annual Average Daily Traffic data</li>
                        <li>💾 <strong>JSON Export</strong> - Automatically save data to local files</li>
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
    
    def display_traffic_data(self, traffic_data: Dict) -> None:
        """
        Display traffic data in a dedicated section
        
        Args:
            traffic_data: GeoJSON traffic data from the API
        """
        try:
            if not traffic_data or 'features' not in traffic_data:
                st.info("🚦 No traffic data available")
                return
            
            # Create traffic data collection
            traffic_collection = TrafficDataCollection(traffic_data)
            
            st.markdown("### 🚦 Traffic Data Analysis")
            
            # Display summary statistics
            stats = traffic_collection.get_traffic_summary_stats()
            if stats:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Records", f"{stats.get('total_records', 0):,}")
                with col2:
                    st.metric("Avg AADT", f"{stats.get('avg_aadt', 0):,.0f}")
                with col3:
                    st.metric("Max AADT", f"{stats.get('max_aadt', 0):,}")
                with col4:
                    st.metric("Counties", stats.get('unique_counties', 0))
            
            # Convert to DataFrame and display
            traffic_df = traffic_collection.to_dataframe()
            
            if not traffic_df.empty:
                # Traffic data filters
                st.markdown("#### 🔍 Filter Traffic Data")
                
                min_aadt = st.number_input(
                    "Minimum AADT",
                    min_value=0,
                    max_value=int(traffic_df['AADT'].max()) if not traffic_df['AADT'].empty else 100000,
                    value=0,
                    step=1000,
                    help="Filter roads with minimum Annual Average Daily Traffic"
                )
                
                # Apply filters
                filtered_df = traffic_df.copy()
                if min_aadt > 0:
                    filtered_df = filtered_df[filtered_df['AADT'] >= min_aadt]
                
                # Display filtered data with correct columns
                st.markdown(f"#### 📊 Traffic Data Table ({len(filtered_df)} records)")
                
                # Add export functionality for traffic data
                self._add_export_buttons(filtered_df, "Traffic Data", "traffic")
                
                # Select relevant columns for display
                display_columns = ['Object ID', 'Roadway', 'County', 'Year', 'AADT', 'Peak Hour', 'District', 'Route', 'Description To']
                available_columns = [col for col in display_columns if col in filtered_df.columns]
                
                if available_columns:
                    display_df = filtered_df[available_columns]
                    self._display_paginated_data_table(display_df, "traffic_data")
                else:
                    self._display_paginated_data_table(filtered_df, "traffic_data")
                
                # Traffic charts
                if len(filtered_df) > 0:
                    self._create_traffic_charts(filtered_df)
            
        except Exception as e:
            logger.error(f"Error displaying traffic data: {e}")
            st.error("❌ Error displaying traffic data")
    
    def _add_export_buttons(self, df: pd.DataFrame, data_type: str, data_key: str) -> None:
        """
        Add export buttons for CSV and Excel download
        
        Args:
            df: DataFrame to export
            data_type: Type of data (e.g., "City Data", "Traffic Data")
            data_key: Key for unique file naming
        """
        try:
            if df.empty:
                return
            
            st.markdown("#### 💾 Export Data")
            
            # Create export buttons in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # CSV Export
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📄 Download CSV",
                    data=csv_data,
                    file_name=f"{data_key}_data_{len(df)}_records.csv",
                    mime="text/csv",
                    help=f"Download {data_type} as CSV file",
                    use_container_width=True
                )
            
            with col2:
                # Excel Export
                try:
                    import io
                    from openpyxl import Workbook
                    from openpyxl.utils.dataframe import dataframe_to_rows
                    
                    # Create Excel workbook
                    wb = Workbook()
                    ws = wb.active
                    ws.title = f"{data_type}"
                    
                    # Add data to worksheet
                    for r in dataframe_to_rows(df, index=False, header=True):
                        ws.append(r)
                    
                    # Auto-adjust column widths
                    for column in ws.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        ws.column_dimensions[column_letter].width = adjusted_width
                    
                    # Save to bytes
                    excel_buffer = io.BytesIO()
                    wb.save(excel_buffer)
                    excel_data = excel_buffer.getvalue()
                    
                    st.download_button(
                        label="📊 Download Excel",
                        data=excel_data,
                        file_name=f"{data_key}_data_{len(df)}_records.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help=f"Download {data_type} as Excel file",
                        use_container_width=True
                    )
                    
                except ImportError:
                    st.warning("⚠️ Excel export requires openpyxl. Install with: pip install openpyxl")
                except Exception as e:
                    logger.error(f"Error creating Excel export: {e}")
                    st.error("❌ Excel export failed")
            
            with col3:
                # JSON Export
                json_data = df.to_json(orient='records', indent=2)
                st.download_button(
                    label="📋 Download JSON",
                    data=json_data,
                    file_name=f"{data_key}_data_{len(df)}_records.json",
                    mime="application/json",
                    help=f"Download {data_type} as JSON file",
                    use_container_width=True
                )
            
            st.success(f"✅ {data_type} export options available for {len(df)} records!")
            
        except Exception as e:
            logger.error(f"Error adding export buttons: {e}")
            st.error("❌ Export functionality failed")
    
    def _create_traffic_charts(self, traffic_df: pd.DataFrame) -> None:
        """
        Create charts for traffic data analysis
        
        Args:
            traffic_df: DataFrame containing traffic data
        """
        try:
            st.markdown("#### 📈 Traffic Analytics")
            
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                # AADT distribution histogram
                if 'AADT' in traffic_df.columns and not traffic_df['AADT'].empty:
                    fig_aadt = px.histogram(
                        traffic_df[traffic_df['AADT'] > 0], 
                        x='AADT',
                        nbins=min(30, len(traffic_df)),
                        title="AADT Distribution",
                        labels={'AADT': 'Annual Average Daily Traffic', 'count': 'Number of Roads'},
                        color_discrete_sequence=['#FF6B6B']
                    )
                    fig_aadt.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#2a5298'
                    )
                    st.plotly_chart(fig_aadt, use_container_width=True)
            
            with chart_col2:
                # Traffic by county
                if 'County' in traffic_df.columns and not traffic_df['County'].empty:
                    county_traffic = traffic_df.groupby('County')['AADT'].mean().sort_values(ascending=False).head(10)
                    if len(county_traffic) > 0:
                        fig_county = px.bar(
                            x=county_traffic.values,
                            y=county_traffic.index,
                            orientation='h',
                            title="Average AADT by County (Top 10)",
                            labels={'x': 'Average AADT', 'y': 'County'},
                            color=county_traffic.values,
                            color_continuous_scale='Viridis'
                        )
                        fig_county.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font_color='#2a5298',
                            yaxis={'categoryorder': 'total ascending'}
                        )
                        st.plotly_chart(fig_county, use_container_width=True)
            
            # High traffic roads table
            high_traffic = traffic_df[traffic_df['AADT'] >= 20000].nlargest(10, 'AADT') if 'AADT' in traffic_df.columns else pd.DataFrame()
            if not high_traffic.empty:
                st.markdown("#### 🔥 Highest Traffic Roads")
                st.dataframe(
                    high_traffic[['Roadway', 'County', 'AADT', 'Route', 'Description To']],
                    use_container_width=True,
                    height=300
                )
            
        except Exception as e:
            logger.error(f"Error creating traffic charts: {e}")
            st.error("❌ Error creating traffic charts")