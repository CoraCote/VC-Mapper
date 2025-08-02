"""
FDOT City Data Explorer - Refactored with MVC Architecture
Main application entry point using the new MVC structure
"""

import streamlit as st
import logging

# Import MVC components
from models import CityCollection
from controllers import CityController
from views import MapView, CityView
from utils import load_css, create_header, create_footer
from utils.constants import UI_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FDOTCityExplorer:
    """
    Main application class using MVC architecture
    """
    
    def __init__(self):
        """Initialize the application with MVC components"""
        self.city_controller = CityController()
        self.map_view = MapView()
        self.city_view = CityView()
        
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables"""
        if 'cities_data' not in st.session_state:
            st.session_state.cities_data = None
        if 'selected_city' not in st.session_state:
            st.session_state.selected_city = None
    
    def configure_page(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title=UI_CONFIG['page_title'],
            page_icon=UI_CONFIG['page_icon'],
            layout=UI_CONFIG['layout'],
            initial_sidebar_state=UI_CONFIG['sidebar_state']
        )
    
    def render_header(self):
        """Render the simplified application header"""
        # Simple title following the wireframe design
        st.markdown(
            """
            <div style="text-align: center; padding: 1rem 0;">
                <h1 style="margin: 0; color: #1f77b4;">🗺️ FDOT City Data Explorer</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    def render_sidebar(self) -> tuple:
        """
        Render the sidebar and handle data fetching
        
        Returns:
            Tuple of (action, params)
        """
        try:
            # Create smart sidebar controls
            action, params = self.city_view.create_smart_sidebar()
            
            # Handle data fetching
            if any(params.get('button', False) for key in ['button'] if key in params):
                success = self.city_view.handle_data_fetch(action, params)
                if success:
                    logger.info(f"Successfully executed action: {action}")
            
            # Display city data in sidebar if available
            cities = self.city_controller.get_session_cities()
            if cities:
                self.city_view.display_city_data_sidebar(cities)
            
            return action, params
            
        except Exception as e:
            logger.error(f"Error rendering sidebar: {e}")
            return "🌍 Fetch All Cities", {"limit": 50, "button": False}
    
    def render_main_map(self):
        """Render the main interactive map with new simplified layout"""
        try:
            # Get cities from session
            cities = self.city_controller.get_session_cities()
            
            if cities and len(cities) > 0:
                # Display map with new simplified UI
                self.map_view.display_cities_on_map(cities)
            else:
                # Show a simplified message and Florida map when no cities are loaded
                st.info("👆 Use the sidebar to fetch city data and start exploring!")
                self.map_view.display_florida_only_map()
                
        except Exception as e:
            logger.error(f"Error rendering main map: {e}")
            st.error("❌ Error displaying map. Please try refreshing the page.")
    
    def render_data_tabs(self):
        """Render the simplified data analysis tabs"""
        try:
            cities = self.city_controller.get_session_cities()
            
            if not cities or len(cities) == 0:
                return
            
            st.markdown("---")
            
            # Create simplified tabs for core functionality
            tab1, tab2, tab3 = st.tabs([
                "📊 City Data", 
                "📈 Analytics",
                "🚦 Traffic Data"
            ])
            
            with tab1:
                self.render_city_data_tab(cities)
            
            with tab2:
                self.render_analytics_tab(cities)
            
            with tab3:
                self.render_traffic_data_tab()
                
        except Exception as e:
            logger.error(f"Error rendering data tabs: {e}")
            st.error("❌ Error displaying data tabs")
    

    
    def render_city_data_tab(self, cities: CityCollection):
        """Render the city data tab"""
        try:
            st.markdown("### 📊 City Data Table")
            
            # Create filter controls
            filters = self.city_view.create_filter_controls(cities)
            
            # Display filtered city data
            self.city_view.display_city_data_main(cities, filters)
            
        except Exception as e:
            logger.error(f"Error rendering city data tab: {e}")
            st.error("❌ Error displaying city data")
    
    def render_analytics_tab(self, cities: CityCollection):
        """Render the analytics tab"""
        try:
            st.markdown("### 📈 City Analytics")
            self.city_view.create_charts(cities)
            
        except Exception as e:
            logger.error(f"Error rendering analytics tab: {e}")
            st.error("❌ Error displaying analytics")
    
    def render_traffic_data_tab(self):
        """Render the traffic data tab"""
        try:
            # Always try to get traffic data (from session or load fresh)
            traffic_data = st.session_state.get('traffic_data')
            if not traffic_data:
                # Try to load from files or fetch fresh
                traffic_data = self.city_controller.fetch_traffic_data()
                if traffic_data:
                    self.city_controller.save_traffic_data_to_json(traffic_data)
                    st.session_state.traffic_data = traffic_data
            
            if traffic_data:
                self.city_view.display_traffic_data(traffic_data)
            else:
                st.info("🚦 Traffic data is being loaded automatically. If you don't see traffic data, please wait a moment or refresh the page.")
                
                # Provide option to fetch traffic data manually
                if st.button("🚦 Fetch Traffic Data Now", type="primary"):
                    with st.spinner("🚦 Fetching traffic data..."):
                        traffic_data = self.city_controller.fetch_traffic_data()
                        if traffic_data:
                            self.city_controller.save_traffic_data_to_json(traffic_data)
                            st.session_state.traffic_data = traffic_data
                            st.success("✅ Traffic data fetched successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to fetch traffic data")
            
        except Exception as e:
            logger.error(f"Error rendering traffic data tab: {e}")
            st.error("❌ Error displaying traffic data")
    

    
    def render_simplified_data_tabs(self, cities: CityCollection):
        """
        Render simplified data tabs when Show Data button is pressed
        
        Args:
            cities: Collection of cities to display data for
        """
        try:
            # Create simplified tabs for data analysis
            tab1, tab2, tab3 = st.tabs([
                "📊 City Data", 
                "📈 Analytics",
                "🚦 Traffic Data"
            ])
            
            with tab1:
                # Simplified city data table
                filters = self.city_view.create_filter_controls(cities)
                self.city_view.display_city_data_main(cities, filters)
            
            with tab2:
                # Analytics
                self.city_view.create_charts(cities)
            
            with tab3:
                # Traffic data
                self.render_traffic_data_tab()
                
        except Exception as e:
            logger.error(f"Error rendering simplified data tabs: {e}")
            st.error("❌ Error displaying data analysis")
    
    def render_welcome_screen(self):
        """Render welcome screen when no data is available"""
        try:
            self.city_view.display_welcome_screen()
        except Exception as e:
            logger.error(f"Error rendering welcome screen: {e}")
    
    def render_footer(self):
        """Render the application footer"""
        create_footer()
    
    def run(self):
        """Run the main application with simplified workflow"""
        try:
            # Configure page
            self.configure_page()
            
            # Load custom CSS
            load_css()
            
            # Render header
            self.render_header()
            
            # Render sidebar and handle data fetching
            action, params = self.render_sidebar()
            
            # Render main map with integrated controls
            self.render_main_map()
            
            # Optional: Show data panel if requested (triggered by Show Data button)
            if st.session_state.get('show_data_panel', False):
                cities = self.city_controller.get_session_cities()
                if cities and len(cities) > 0:
                    st.markdown("---")
                    with st.expander("📊 Detailed Data Analysis", expanded=True):
                        self.render_simplified_data_tabs(cities)
            
            # Render footer
            self.render_footer()
            
        except Exception as e:
            logger.error(f"Critical error in main application: {e}")
            st.error("❌ Critical application error. Please refresh the page.")
            
            # Display error details in expander for debugging
            with st.expander("🔧 Error Details (for debugging)"):
                st.code(str(e))
                import traceback
                st.code(traceback.format_exc())


def main():
    """
    Main entry point for the application
    """
    try:
        app = FDOTCityExplorer()
        app.run()
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        st.error("❌ Failed to start application. Please check the configuration and try again.")


if __name__ == "__main__":
    main()