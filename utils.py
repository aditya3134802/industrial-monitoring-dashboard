import pandas as pd
from datetime import datetime, timedelta

def apply_filters(data, time_range=None, selected_metrics=None):
    """
    Apply filters to the dataset based on time range and selected metrics
    
    Args:
        data (pd.DataFrame): The input dataframe
        time_range (str): Time range filter
        selected_metrics (list): List of metrics to include
        
    Returns:
        pd.DataFrame: Filtered dataframe
    """
    if data.empty:
        return data
    
    filtered_data = data.copy()
    
    # Apply time range filter if specified
    if time_range:
        now = datetime.now()
        
        if time_range == "Last 15 minutes":
            start_time = now - timedelta(minutes=15)
        elif time_range == "Last hour":
            start_time = now - timedelta(hours=1)
        elif time_range == "Last 6 hours":
            start_time = now - timedelta(hours=6)
        elif time_range == "Last 24 hours":
            start_time = now - timedelta(hours=24)
        else:  # "Last 7 days"
            start_time = now - timedelta(days=7)
        
        filtered_data = filtered_data[filtered_data['timestamp'] >= start_time]
    
    # Apply metric selection if specified
    if selected_metrics:
        # Always keep timestamp column
        columns_to_keep = ['timestamp'] + selected_metrics
        filtered_data = filtered_data[columns_to_keep]
    
    return filtered_data

def get_alert_status(value, threshold):
    """
    Determine alert status based on value and threshold
    
    Args:
        value (float): The current metric value
        threshold (float): The alert threshold
        
    Returns:
        str: 'alert' if value exceeds threshold, 'normal' otherwise
    """
    if value >= threshold:
        return "alert"
    return "normal"

def format_number(num):
    """
    Format numbers for display
    
    Args:
        num (float): Number to format
        
    Returns:
        str: Formatted number
    """
    if num >= 1000:
        return f"{num/1000:.1f}k"
    return f"{num:.1f}"
