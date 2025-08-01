"""
Street View - UI components for street data display and interaction
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import logging
from typing import Dict, Optional
from models.street_model import StreetCollection
from models.city_model import City
from controllers.street_controller import StreetController

logger = logging.getLogger(__name__)


class StreetView:
    """
    View component for street data display and interaction
    """
    
    def __init__(self):
        """Initialize the street view"""
        self.street_controller = StreetController()
    
    def display_street_data_table(self, streets: StreetCollection, city_name: str) -> None:
        """
        Display street data in a formatted table with filters and charts
        
        Args:
            streets: Collection of streets to display
            city_name: Name of the city for the table title
        """
        try:
            if not streets or len(streets) == 0:
                st.info("📍 No street data available for the selected city")
                return
            
            st.subheader(f"🛣️ Street Data for {city_name}")
            
            # Create filter controls
            filters = self._create_filter_controls(streets)
            
            # Apply filters and sorting
            filtered_streets = self.street_controller.filter_streets(streets, filters)
            sorted_streets = self.street_controller.sort_streets(filtered_streets, filters.get('sort_by', 'Street Name'))
            
            # Display summary metrics
            self._display_street_metrics(sorted_streets)
            
            # Display the table
            self._display_street_table(sorted_streets)
            
            # Display traffic distribution charts
            if len(sorted_streets) > 0:
                self._display_traffic_charts(sorted_streets)
                
        except Exception as e:
            logger.error(f"Error displaying street data table: {e}")
            st.error("❌ Error displaying street data")
    
    def _create_filter_controls(self, streets: StreetCollection) -> Dict:
        """
        Create filter and sort controls for street data
        
        Args:
            streets: Collection of streets to create filters for
            
        Returns:
            Dictionary of filter values
        """
        try:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                search_term = st.text_input("🔍 Search streets", placeholder="Enter street name...")
            
            with col2:
                unique_levels = streets.get_unique_traffic_levels()
                traffic_filter = st.selectbox(
                    "🚦 Filter by traffic level",
                    ["All"] + unique_levels
                )
            
            with col3:
                sort_by = st.selectbox(
                    "📊 Sort by",
                    ["Street Name", "Traffic Volume", "Length", "Speed Limit"]
                )
            
            return {
                'search_term': search_term,
                'traffic_level': traffic_filter,
                'sort_by': sort_by
            }
            
        except Exception as e:
            logger.error(f"Error creating filter controls: {e}")
            return {}
    
    def _display_street_metrics(self, streets: StreetCollection) -> None:
        """Display summary metrics for streets"""
        try:
            stats = self.street_controller.get_street_statistics(streets)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🛣️ Total Streets", stats.get('total_streets', 0))
            
            with col2:
                total_traffic = stats.get('total_traffic_volume', 0)
                st.metric("🚗 Total Daily Traffic", f"{total_traffic:,}")
            
            with col3:
                avg_traffic = stats.get('average_traffic_volume', 0)
                st.metric("📊 Avg Traffic/Street", f"{avg_traffic:,.0f}")
            
            with col4:
                total_length = stats.get('total_length', 0)
                st.metric("📏 Total Length", f"{total_length:.1f} units")
                
        except Exception as e:
            logger.error(f"Error displaying street metrics: {e}")
    
    def _display_street_table(self, streets: StreetCollection) -> None:
        """Display the street data table"""
        try:
            # Convert to DataFrame for display
            df = streets.to_dataframe()
            
            # Display the table with custom column configuration
            st.dataframe(
                df, 
                use_container_width=True,
                height=400,
                column_config={
                    "Traffic Volume": st.column_config.TextColumn(
                        "Traffic Volume (daily)",
                        help="Daily traffic volume"
                    ),
                    "Traffic Level": st.column_config.TextColumn(
                        "Traffic Level",
                        help="Classification based on daily traffic volume"
                    )
                }
            )
            
        except Exception as e:
            logger.error(f"Error displaying street table: {e}")
    
    def _display_traffic_charts(self, streets: StreetCollection) -> None:
        """Display traffic distribution charts"""
        try:
            st.subheader("📈 Traffic Level Distribution")
            
            traffic_distribution = streets.get_traffic_distribution()
            
            if not traffic_distribution:
                st.info("No traffic data available for charts")
                return
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Pie chart
                fig_pie = px.pie(
                    values=list(traffic_distribution.values()),
                    names=list(traffic_distribution.keys()),
                    title="Streets by Traffic Level",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Bar chart
                fig_bar = px.bar(
                    x=list(traffic_distribution.keys()),
                    y=list(traffic_distribution.values()),
                    title="Street Count by Traffic Level",
                    labels={'x': 'Traffic Level', 'y': 'Number of Streets'},
                    color=list(traffic_distribution.values()),
                    color_continuous_scale='Viridis'
                )
                fig_bar.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    showlegend=False
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                
        except Exception as e:
            logger.error(f"Error displaying traffic charts: {e}")
    
    def display_street_tab_content(self) -> None:
        """
        Display content for the street data tab
        """
        try:
            st.markdown("### 🛣️ Street Data Analysis")
            
            # Check if there's a selected city
            if 'selected_city' in st.session_state and st.session_state.selected_city:
                selected_city_data = st.session_state.selected_city
                selected_city = City(selected_city_data)
                
                # Load street data for the selected city
                with st.spinner(f"Loading street data for {selected_city.name}..."):
                    try:
                        streets = self.street_controller.get_streets_for_city(selected_city)
                        
                        if streets and len(streets) > 0:
                            # Store in session state for reuse
                            self.street_controller.save_to_session(streets)
                            self.display_street_data_table(streets, selected_city.name)
                        else:
                            self._display_no_street_data_message()
                            
                    except Exception as e:
                        st.error(f"❌ Error loading street data: {str(e)}")
                        logger.error(f"Street data error: {e}")
            else:
                self._display_street_instructions()
                
        except Exception as e:
            logger.error(f"Error displaying street tab content: {e}")
            st.error("❌ Error loading street data interface")
    
    def _display_no_street_data_message(self) -> None:
        """Display message when no street data is available"""
        st.warning("⚠️ No street data available for this city")
        st.info("This might be due to:")
        st.markdown("- Limited street data in OpenStreetMap database")
        st.markdown("- City location might be outside mapped areas")
        st.markdown("- API connectivity issues")
    
    def _display_street_instructions(self) -> None:
        """Display instructions for getting street data"""
        st.info("🎯 Please select a city from the map above to view street data")
        st.markdown("**How to get started:**")
        st.markdown("1. Press 'FETCH CITY' button from the sidebar")
        st.markdown("2. Select a specific city from the dropdown on the map")
        st.markdown("3. Street data will be displayed here")
    
    def create_street_summary_card(self, streets: StreetCollection, city_name: str) -> None:
        """
        Create a summary card for street data
        
        Args:
            streets: Collection of streets
            city_name: Name of the city
        """
        try:
            if not streets or len(streets) == 0:
                return
            
            stats = self.street_controller.get_street_statistics(streets)
            
            st.markdown(f"""
            <div class="metric-container">
                <h4>🛣️ Street Summary for {city_name}</h4>
                <p><strong>Total Streets:</strong> {stats.get('total_streets', 0)}</p>
                <p><strong>Total Daily Traffic:</strong> {stats.get('total_traffic_volume', 0):,} vehicles</p>
                <p><strong>Average Traffic per Street:</strong> {stats.get('average_traffic_volume', 0):,.0f} vehicles</p>
                <p><strong>Total Road Length:</strong> {stats.get('total_length', 0):.1f} units</p>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            logger.error(f"Error creating street summary card: {e}")
    
    def display_street_loading_state(self, city_name: str) -> None:
        """
        Display loading state for street data
        
        Args:
            city_name: Name of the city being loaded
        """
        try:
            with st.spinner(f"🔄 Loading street data for {city_name}..."):
                # Create placeholder content
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🛣️ Streets", "Loading...")
                with col2:
                    st.metric("🚗 Traffic", "Loading...")
                with col3:
                    st.metric("📏 Length", "Loading...")
                
                st.info("⏳ Fetching street data from OpenStreetMap API...")
                
        except Exception as e:
            logger.error(f"Error displaying street loading state: {e}")
    
    def create_street_filter_panel(self, streets: StreetCollection) -> Dict:
        """
        Create an advanced filter panel for streets
        
        Args:
            streets: Collection of streets to filter
            
        Returns:
            Dictionary of filter criteria
        """
        try:
            st.subheader("🔧 Advanced Filters")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Name filter
                name_filter = st.text_input(
                    "Street Name Contains",
                    placeholder="Enter partial street name"
                )
                
                # Traffic level filter
                traffic_levels = streets.get_unique_traffic_levels()
                traffic_filter = st.multiselect(
                    "Traffic Levels",
                    traffic_levels,
                    default=traffic_levels
                )
            
            with col2:
                # Highway type filter if available
                highway_types = list(set(street.highway_type for street in streets.streets if street.highway_type))
                if highway_types:
                    highway_filter = st.multiselect(
                        "Highway Types",
                        highway_types,
                        default=highway_types
                    )
                else:
                    highway_filter = []
                
                # Length range filter
                if streets.streets:
                    max_length = max(street.length for street in streets.streets if street.length)
                    length_range = st.slider(
                        "Length Range",
                        0.0,
                        max_length,
                        (0.0, max_length),
                        step=0.1
                    )
                else:
                    length_range = (0.0, 0.0)
            
            return {
                'name_filter': name_filter,
                'traffic_levels': traffic_filter,
                'highway_types': highway_filter,
                'length_range': length_range
            }
            
        except Exception as e:
            logger.error(f"Error creating street filter panel: {e}")
            return {}
    
    def display_street_export_options(self, streets: StreetCollection, city_name: str) -> None:
        """
        Display export options for street data
        
        Args:
            streets: Collection of streets to export
            city_name: Name of the city
        """
        try:
            if not streets or len(streets) == 0:
                return
            
            st.subheader("📥 Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # CSV export
                df = streets.to_dataframe()
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📄 Download as CSV",
                    data=csv,
                    file_name=f"{city_name}_streets.csv",
                    mime="text/csv"
                )
            
            with col2:
                # JSON export
                import json
                streets_dict = streets.get_streets_as_dict_list()
                json_str = json.dumps(streets_dict, indent=2)
                st.download_button(
                    label="📋 Download as JSON",
                    data=json_str,
                    file_name=f"{city_name}_streets.json",
                    mime="application/json"
                )
                
        except Exception as e:
            logger.error(f"Error displaying street export options: {e}")