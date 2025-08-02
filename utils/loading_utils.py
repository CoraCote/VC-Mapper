"""
Loading Utilities - Progress indicators and loading bars for data operations
"""

import streamlit as st
import time
import logging
from typing import Optional, Callable, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class LoadingManager:
    """
    Manages loading states and progress indicators for data operations
    """
    
    def __init__(self):
        """Initialize the loading manager"""
        self.progress_bar = None
        self.status_text = None
    
    @contextmanager
    def loading_spinner(self, message: str, icon: str = "🔄"):
        """
        Context manager for loading spinner
        
        Args:
            message: Loading message to display
            icon: Icon to show with the message
        """
        try:
            with st.spinner(f"{icon} {message}"):
                yield
        except Exception as e:
            logger.error(f"Error in loading spinner: {e}")
            st.error(f"❌ Error during {message.lower()}")
            raise
    
    def create_progress_bar(self, total_steps: int, message: str = "Processing..."):
        """
        Create a progress bar for multi-step operations
        
        Args:
            total_steps: Total number of steps
            message: Progress message
        """
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        self.status_text.text(f"🔄 {message} (0/{total_steps})")
        return self.progress_bar
    
    def update_progress(self, current_step: int, total_steps: int, message: str = "Processing..."):
        """
        Update progress bar and status text
        
        Args:
            current_step: Current step number
            total_steps: Total number of steps
            message: Progress message
        """
        if self.progress_bar and self.status_text:
            progress = current_step / total_steps
            self.progress_bar.progress(progress)
            self.status_text.text(f"🔄 {message} ({current_step}/{total_steps})")
    
    def complete_progress(self, message: str = "✅ Completed!"):
        """
        Complete the progress bar
        
        Args:
            message: Completion message
        """
        if self.progress_bar and self.status_text:
            self.progress_bar.progress(1.0)
            self.status_text.text(f"✅ {message}")
            time.sleep(1)  # Show completion briefly
            self.progress_bar.empty()
            self.status_text.empty()
    
    def error_progress(self, message: str = "❌ Error occurred"):
        """
        Show error in progress bar
        
        Args:
            message: Error message
        """
        if self.progress_bar and self.status_text:
            self.status_text.text(f"❌ {message}")
            time.sleep(2)  # Show error briefly
            self.progress_bar.empty()
            self.status_text.empty()


class DataLoadingIndicators:
    """
    Specific loading indicators for data operations
    """
    
    @staticmethod
    def fetch_cities_loading():
        """Loading indicator for city data fetching"""
        return st.spinner("🏙️ Fetching city data from FDOT API...")
    
    @staticmethod
    def fetch_traffic_loading():
        """Loading indicator for traffic data fetching"""
        return st.spinner("🚦 Fetching traffic data from FDOT API...")
    
    @staticmethod
    def search_cities_loading():
        """Loading indicator for city search"""
        return st.spinner("🔍 Searching cities in database...")
    
    @staticmethod
    def process_data_loading():
        """Loading indicator for data processing"""
        return st.spinner("⚙️ Processing and formatting data...")
    
    @staticmethod
    def render_map_loading():
        """Loading indicator for map rendering"""
        return st.spinner("🗺️ Rendering interactive map...")
    
    @staticmethod
    def export_data_loading():
        """Loading indicator for data export"""
        return st.spinner("📊 Preparing data for export...")
    
    @staticmethod
    def save_data_loading():
        """Loading indicator for data saving"""
        return st.spinner("💾 Saving data to local storage...")
    
    @staticmethod
    def load_data_loading():
        """Loading indicator for data loading"""
        return st.spinner("📂 Loading data from local storage...")


class ProgressTracker:
    """
    Track progress for multi-step operations
    """
    
    def __init__(self, total_steps: int, operation_name: str):
        """
        Initialize progress tracker
        
        Args:
            total_steps: Total number of steps
            operation_name: Name of the operation
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.operation_name = operation_name
        self.loading_manager = LoadingManager()
        self.progress_bar = self.loading_manager.create_progress_bar(total_steps, operation_name)
    
    def step(self, step_name: str):
        """
        Move to next step
        
        Args:
            step_name: Name of the current step
        """
        self.current_step += 1
        self.loading_manager.update_progress(
            self.current_step, 
            self.total_steps, 
            f"{self.operation_name}: {step_name}"
        )
    
    def complete(self, message: str = None):
        """
        Complete the operation
        
        Args:
            message: Completion message
        """
        final_message = message or f"✅ {self.operation_name} completed successfully!"
        self.loading_manager.complete_progress(final_message)
    
    def error(self, message: str = None):
        """
        Show error in progress
        
        Args:
            message: Error message
        """
        error_message = message or f"❌ {self.operation_name} failed"
        self.loading_manager.error_progress(error_message)


def with_loading_indicator(operation_name: str, icon: str = "🔄"):
    """
    Decorator to add loading indicator to functions
    
    Args:
        operation_name: Name of the operation
        icon: Icon to display
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            with st.spinner(f"{icon} {operation_name}..."):
                try:
                    result = func(*args, **kwargs)
                    st.success(f"✅ {operation_name} completed successfully!")
                    return result
                except Exception as e:
                    logger.error(f"Error in {operation_name}: {e}")
                    st.error(f"❌ {operation_name} failed: {str(e)}")
                    raise
        return wrapper
    return decorator


def create_multi_step_progress(operation_name: str, steps: list) -> ProgressTracker:
    """
    Create a multi-step progress tracker
    
    Args:
        operation_name: Name of the operation
        steps: List of step names
        
    Returns:
        ProgressTracker instance
    """
    return ProgressTracker(len(steps), operation_name)


# Global loading manager instance
loading_manager = LoadingManager() 