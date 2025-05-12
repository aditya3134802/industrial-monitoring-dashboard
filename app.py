import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import time
from datetime import datetime, timedelta
import threading
import random

from data_generator import DataGenerator
from utils import apply_filters, get_alert_status, format_number

# Set page config
st.set_page_config(
    page_title="Industrial Infrastructure Monitor",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize application state
if 'data_generator' not in st.session_state:
    st.session_state.data_generator = DataGenerator()
    
if 'metrics_data' not in st.session_state:
    st.session_state.metrics_data = pd.DataFrame()
    
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
    
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
    
if 'alert_count' not in st.session_state:
    st.session_state.alert_count = 0
    
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True

# Sidebar
with st.sidebar:
    st.title("Settings")
    
    # Time Range Selector
    st.subheader("Time Range")
    time_range = st.selectbox(
        "Select Time Range",
        ["Last 15 minutes", "Last hour", "Last 6 hours", "Last 24 hours", "Last 7 days"],
        index=1
    )
    
    # Refresh Rate
    st.subheader("Data Refresh")
    refresh_rate = st.slider("Refresh Rate (seconds)", 5, 60, 10)
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto Refresh", value=st.session_state.auto_refresh)
    st.session_state.auto_refresh = auto_refresh
    
    # Metrics Selection
    st.subheader("Metrics")
    selected_metrics = st.multiselect(
        "Select Metrics to Display",
        ["CPU Utilization", "Memory Usage", "Disk I/O", "Network Traffic", "Power Consumption", "Temperature"],
        default=["CPU Utilization", "Memory Usage", "Network Traffic", "Temperature"]
    )
    
    # Alert Thresholds
    st.subheader("Alert Thresholds")
    st.caption("Set thresholds for alerting")
    
    cpu_threshold = st.slider("CPU Utilization Alert (%)", 70, 100, 85)
    memory_threshold = st.slider("Memory Usage Alert (%)", 70, 100, 90)
    temperature_threshold = st.slider("Temperature Alert (°C)", 50, 100, 75)
    
    # Manual refresh button
    if st.button("Refresh Data Now"):
        st.session_state.metrics_data = st.session_state.data_generator.get_latest_data(time_range)
        st.session_state.last_update = datetime.now()

# Main content
st.title("Industrial Infrastructure Monitoring Dashboard")

# Status and last update info
status_col1, status_col2, status_col3 = st.columns([1, 1, 1])

with status_col1:
    st.metric("Systems Monitored", "32")

with status_col2:
    alert_count = st.session_state.alert_count
    st.metric("Active Alerts", str(alert_count), delta=None, 
              delta_color="inverse" if alert_count > 0 else "normal")

with status_col3:
    st.write("Last Updated:")
    st.write(f"{st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

# Get data based on selected time range
if st.session_state.auto_refresh and (datetime.now() - st.session_state.last_update).total_seconds() > refresh_rate:
    st.session_state.metrics_data = st.session_state.data_generator.get_latest_data(time_range)
    st.session_state.last_update = datetime.now()
elif not st.session_state.metrics_data.empty:
    pass  # Keep using existing data
else:
    st.session_state.metrics_data = st.session_state.data_generator.get_latest_data(time_range)
    st.session_state.last_update = datetime.now()

# Create dashboard layout
if not st.session_state.metrics_data.empty:
    data = st.session_state.metrics_data
    
    # Create KPI metrics for current values
    st.subheader("Current System Metrics")
    
    # Get the most recent values
    latest_data = data.iloc[-1].to_dict()
    
    # KPI metrics row
    metric_cols = st.columns(len(selected_metrics))
    
    alert_count = 0
    current_alerts = []
    
    for i, metric in enumerate(selected_metrics):
        with metric_cols[i]:
            current_value = latest_data.get(metric, 0)
            
            # Format values based on metric type
            if metric == "CPU Utilization":
                display_value = f"{current_value:.1f}%"
                alert_status = get_alert_status(current_value, cpu_threshold)
                if alert_status == "alert":
                    alert_count += 1
                    current_alerts.append(f"High {metric}: {display_value}")
            elif metric == "Memory Usage":
                display_value = f"{current_value:.1f}%"
                alert_status = get_alert_status(current_value, memory_threshold)
                if alert_status == "alert":
                    alert_count += 1
                    current_alerts.append(f"High {metric}: {display_value}")
            elif metric == "Temperature":
                display_value = f"{current_value:.1f}°C"
                alert_status = get_alert_status(current_value, temperature_threshold)
                if alert_status == "alert":
                    alert_count += 1
                    current_alerts.append(f"High {metric}: {display_value}")
            elif metric == "Network Traffic":
                display_value = f"{format_number(current_value)} MB/s"
                alert_status = "normal"
            elif metric == "Disk I/O":
                display_value = f"{format_number(current_value)} IOPS"
                alert_status = "normal"
            elif metric == "Power Consumption":
                display_value = f"{format_number(current_value)} kW"
                alert_status = "normal"
            else:
                display_value = f"{current_value:.1f}"
                alert_status = "normal"
            
            # Delta is the change from previous reading
            if len(data) > 1:
                prev_value = data.iloc[-2].get(metric, 0)
                delta = current_value - prev_value
                
                # Display metric with delta indicator
                st.metric(
                    label=metric,
                    value=display_value,
                    delta=f"{delta:+.1f}" if metric not in ["Network Traffic", "Disk I/O", "Power Consumption"] else None,
                    delta_color="normal"
                )
                
                # Add visual indicator for alerts
                if alert_status == "alert":
                    st.error("⚠️ Alert Threshold Exceeded")
            else:
                st.metric(label=metric, value=display_value)
    
    # Update alert count in session state
    st.session_state.alert_count = alert_count
    st.session_state.alerts = current_alerts
    
    # Display alerts if any
    if current_alerts:
        st.subheader("🚨 Active Alerts")
        for alert in current_alerts:
            st.warning(alert)
    
    # Main charts
    st.subheader("System Metrics Over Time")
    
    # Create tabs for different visualization types
    tab1, tab2, tab3 = st.tabs(["Line Charts", "Bar Charts", "Metrics Comparison"])
    
    with tab1:
        # Line charts for selected metrics
        for metric in selected_metrics:
            fig = px.line(
                data, 
                x='timestamp', 
                y=metric,
                title=f"{metric} Over Time",
                labels={'timestamp': 'Time', metric: metric}
            )
            
            # Add threshold lines for metrics with alerts
            if metric == "CPU Utilization":
                fig.add_hline(y=cpu_threshold, line_dash="dash", line_color="red", 
                             annotation_text=f"Alert Threshold ({cpu_threshold}%)")
            elif metric == "Memory Usage":
                fig.add_hline(y=memory_threshold, line_dash="dash", line_color="red", 
                             annotation_text=f"Alert Threshold ({memory_threshold}%)")
            elif metric == "Temperature":
                fig.add_hline(y=temperature_threshold, line_dash="dash", line_color="red", 
                             annotation_text=f"Alert Threshold ({temperature_threshold}°C)")
            
            # Update layout
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Bar chart for average values over the selected time period
        avg_data = data.mean().reset_index()
        avg_data.columns = ['Metric', 'Average Value']
        avg_data = avg_data[avg_data['Metric'].isin(selected_metrics)]
        
        fig = px.bar(
            avg_data,
            x='Metric',
            y='Average Value',
            title=f"Average Metric Values ({time_range})",
            color='Average Value',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Bar chart for metric variability
        std_data = data.std().reset_index()
        std_data.columns = ['Metric', 'Standard Deviation']
        std_data = std_data[std_data['Metric'].isin(selected_metrics)]
        
        fig = px.bar(
            std_data,
            x='Metric',
            y='Standard Deviation',
            title=f"Metric Variability ({time_range})",
            color='Standard Deviation',
            color_continuous_scale=px.colors.sequential.Plasma
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Create correlation matrix for metrics
        corr_metrics = selected_metrics.copy()
        if len(corr_metrics) > 1:
            corr_data = data[corr_metrics].corr()
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_data.values,
                x=corr_data.columns,
                y=corr_data.index,
                colorscale='RdBu_r',
                zmin=-1, zmax=1,
                text=corr_data.round(2).values,
                texttemplate="%{text}",
                textfont={"size":12}
            ))
            
            fig.update_layout(
                title="Correlation Matrix Between Metrics",
                height=500,
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Scatter plot matrix for selected metrics
            if len(selected_metrics) <= 4:  # Limit to 4 metrics to keep the display readable
                fig = px.scatter_matrix(
                    data,
                    dimensions=selected_metrics,
                    title="Scatter Matrix of Selected Metrics",
                    opacity=0.7
                )
                fig.update_layout(height=700)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Select 4 or fewer metrics to view the scatter matrix")
        else:
            st.info("Select at least 2 metrics to view correlations")
    
    # System distribution section
    st.subheader("System Distribution")
    dist_col1, dist_col2 = st.columns(2)
    
    with dist_col1:
        # Pie chart for simulated system distribution
        system_types = ['Production Servers', 'Database Systems', 'Network Equipment', 'Storage Systems']
        system_counts = [12, 8, 7, 5]
        
        fig = px.pie(
            values=system_counts, 
            names=system_types,
            title="System Type Distribution",
            hole=0.3
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with dist_col2:
        # Gauge charts for overall system health
        # Calculate overall health based on current metrics and thresholds
        health_score = 100
        
        for metric in selected_metrics:
            current_value = latest_data.get(metric, 0)
            
            if metric == "CPU Utilization":
                score_reduction = max(0, (current_value - 70) / (cpu_threshold - 70) * 30)
                health_score -= score_reduction
            elif metric == "Memory Usage":
                score_reduction = max(0, (current_value - 70) / (memory_threshold - 70) * 25)
                health_score -= score_reduction
            elif metric == "Temperature":
                score_reduction = max(0, (current_value - 50) / (temperature_threshold - 50) * 35)
                health_score -= score_reduction
        
        health_score = max(0, min(100, health_score))
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = health_score,
            title = {'text': "Overall System Health"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "red"},
                    {'range': [50, 75], 'color': "orange"},
                    {'range': [75, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 75
                }
            }
        ))
        
        st.plotly_chart(fig, use_container_width=True)
    
else:
    st.info("Waiting for data to load... Please wait a moment.")

# Set up automatic refresh if enabled
if st.session_state.auto_refresh:
    time.sleep(0.1)  # Small delay to prevent excessive refreshing
    st.rerun()
