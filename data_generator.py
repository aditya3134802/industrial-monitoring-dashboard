import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

class DataGenerator:
    """
    Generates simulated industrial infrastructure metrics for the dashboard
    """
    def __init__(self):
        # Initialize with some "history" data
        self.data_history = self._generate_historical_data()
        self.last_timestamp = self.data_history['timestamp'].max()
    
    def _generate_historical_data(self, days=7):
        """Generate historical data for the past X days"""
        now = datetime.now()
        start_time = now - timedelta(days=days)
        
        # Create timestamps at 5-minute intervals
        timestamps = []
        current_time = start_time
        while current_time <= now:
            timestamps.append(current_time)
            current_time += timedelta(minutes=5)
        
        # Create dataframe with timestamps
        df = pd.DataFrame({'timestamp': timestamps})
        
        # Add metrics with realistic patterns and trends
        
        # CPU Utilization: 25-85% with daily patterns and occasional spikes
        hour_of_day = df['timestamp'].dt.hour
        day_factor = np.sin(hour_of_day * np.pi / 12) * 15 + 55  # Higher during work hours
        cpu_noise = np.random.normal(0, 5, len(df))
        df['CPU Utilization'] = day_factor + cpu_noise
        
        # Occasional CPU spikes
        spike_indices = np.random.choice(len(df), size=int(len(df) * 0.03), replace=False)
        df.loc[spike_indices, 'CPU Utilization'] += np.random.uniform(15, 30, len(spike_indices))
        
        # Memory Usage: 40-95% with gradual increases and drops
        memory_base = 60 + np.cumsum(np.random.normal(0, 0.5, len(df))) * 0.1
        # Reset memory occasionally (simulating system restarts or cleanup)
        reset_points = np.random.choice(len(df), size=int(len(df) / 250), replace=False)
        for idx in reset_points:
            if idx < len(memory_base) - 1:
                memory_base[idx+1:] = memory_base[idx+1:] - memory_base[idx+1] + 60 + np.random.normal(0, 5)
        df['Memory Usage'] = np.clip(memory_base, 40, 95)
        
        # Disk I/O: 500-5000 IOPS with occasional bursts
        disk_base = 1500 + np.cumsum(np.random.normal(0, 50, len(df))) * 0.1
        df['Disk I/O'] = np.clip(disk_base, 500, 5000)
        disk_bursts = np.random.choice(len(df), size=int(len(df) * 0.05), replace=False)
        df.loc[disk_bursts, 'Disk I/O'] = df.loc[disk_bursts, 'Disk I/O'] + np.random.uniform(1000, 3000, len(disk_bursts))
        
        # Network Traffic: 10-200 MB/s with weekly patterns
        day_of_week = df['timestamp'].dt.dayofweek
        weekday_factor = np.where(day_of_week < 5, 1.0, 0.5)  # Less traffic on weekends
        network_base = 50 + 30 * np.sin(hour_of_day * np.pi / 12) * weekday_factor
        network_noise = np.random.exponential(20, len(df))
        df['Network Traffic'] = network_base + network_noise
        
        # Temperature: 35-80°C with daily cycles and correlation to CPU
        temp_base = 45 + 5 * np.sin(hour_of_day * np.pi / 12)
        # Add correlation with CPU
        cpu_impact = (df['CPU Utilization'] - 50) * 0.2
        temp_noise = np.random.normal(0, 2, len(df))
        df['Temperature'] = temp_base + cpu_impact + temp_noise
        
        # Power Consumption: 5-15 kW with correlation to CPU and temperature
        power_base = 8 + 2 * np.sin(hour_of_day * np.pi / 12) * weekday_factor
        power_cpu_impact = (df['CPU Utilization'] - 50) * 0.05
        power_temp_impact = (df['Temperature'] - 50) * 0.03
        power_noise = np.random.normal(0, 0.5, len(df))
        df['Power Consumption'] = power_base + power_cpu_impact + power_temp_impact + power_noise
        
        # Ensure all metrics stay within reasonable bounds
        df['CPU Utilization'] = np.clip(df['CPU Utilization'], 0, 100)
        df['Memory Usage'] = np.clip(df['Memory Usage'], 0, 100)
        df['Disk I/O'] = np.clip(df['Disk I/O'], 0, 10000)
        df['Network Traffic'] = np.clip(df['Network Traffic'], 0, 500)
        df['Temperature'] = np.clip(df['Temperature'], 30, 95)
        df['Power Consumption'] = np.clip(df['Power Consumption'], 3, 20)
        
        return df
    
    def get_latest_data(self, time_range="Last hour"):
        """Get data for the selected time range and generate new data if needed"""
        # Update with new data points if needed
        self._extend_data_if_needed()
        
        # Filter data based on the selected time range
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
        
        filtered_data = self.data_history[self.data_history['timestamp'] >= start_time].copy()
        
        return filtered_data
    
    def _extend_data_if_needed(self):
        """Extend data history with new data points up to current time"""
        now = datetime.now()
        
        # If last timestamp is less than current time, add new data points
        if self.last_timestamp < now:
            current_time = self.last_timestamp + timedelta(minutes=5)
            new_timestamps = []
            
            while current_time <= now:
                new_timestamps.append(current_time)
                current_time += timedelta(minutes=5)
            
            if new_timestamps:
                # Get the last row of existing data as a starting point
                last_values = self.data_history.iloc[-1].copy()
                
                new_rows = []
                for ts in new_timestamps:
                    # Generate new values with some continuity from the last values
                    new_row = {
                        'timestamp': ts,
                        'CPU Utilization': self._next_value(last_values['CPU Utilization'], 0, 100, 
                                                          mean_reversion=True, mean=60, volatility=5),
                        'Memory Usage': self._next_value(last_values['Memory Usage'], 0, 100, 
                                                       mean_reversion=False, drift=0.1, volatility=1),
                        'Disk I/O': self._next_value(last_values['Disk I/O'], 0, 10000, 
                                                   mean_reversion=True, mean=2000, volatility=200),
                        'Network Traffic': self._next_value(last_values['Network Traffic'], 0, 500, 
                                                         mean_reversion=True, mean=100, volatility=20),
                        'Temperature': self._next_value(last_values['Temperature'], 30, 95, 
                                                     mean_reversion=True, mean=55, volatility=2),
                        'Power Consumption': self._next_value(last_values['Power Consumption'], 3, 20, 
                                                           mean_reversion=True, mean=10, volatility=0.5)
                    }
                    
                    # Occasionally create "events" with correlated changes
                    if random.random() < 0.05:  # 5% chance of an "event"
                        event_type = random.choice(['cpu_spike', 'memory_leak', 'thermal_issue', 'network_burst'])
                        
                        if event_type == 'cpu_spike':
                            new_row['CPU Utilization'] += random.uniform(10, 30)
                            new_row['Temperature'] += random.uniform(5, 15)
                            new_row['Power Consumption'] += random.uniform(1, 3)
                        elif event_type == 'memory_leak':
                            new_row['Memory Usage'] += random.uniform(5, 15)
                        elif event_type == 'thermal_issue':
                            new_row['Temperature'] += random.uniform(10, 25)
                        elif event_type == 'network_burst':
                            new_row['Network Traffic'] += random.uniform(50, 150)
                            new_row['CPU Utilization'] += random.uniform(5, 15)
                    
                    # Ensure values stay within bounds
                    new_row['CPU Utilization'] = min(100, max(0, new_row['CPU Utilization']))
                    new_row['Memory Usage'] = min(100, max(0, new_row['Memory Usage']))
                    new_row['Disk I/O'] = min(10000, max(0, new_row['Disk I/O']))
                    new_row['Network Traffic'] = min(500, max(0, new_row['Network Traffic']))
                    new_row['Temperature'] = min(95, max(30, new_row['Temperature']))
                    new_row['Power Consumption'] = min(20, max(3, new_row['Power Consumption']))
                    
                    new_rows.append(new_row)
                    last_values = new_row
                
                # Add new rows to the data history
                new_data = pd.DataFrame(new_rows)
                self.data_history = pd.concat([self.data_history, new_data], ignore_index=True)
                self.last_timestamp = self.data_history['timestamp'].max()
    
    def _next_value(self, current, min_val, max_val, mean_reversion=False, mean=None, 
                  drift=0, volatility=1):
        """Generate next value with optional mean reversion, drift and volatility"""
        if mean_reversion and mean is not None:
            # Mean reverting process
            next_val = current + (mean - current) * 0.1 + np.random.normal(0, volatility)
        else:
            # Random walk with drift
            next_val = current + drift + np.random.normal(0, volatility)
        
        # Ensure value stays within bounds
        return min(max_val, max(min_val, next_val))
