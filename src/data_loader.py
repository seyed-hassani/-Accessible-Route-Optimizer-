"""
Accessible Route Optimizer - Data Loading Module
Handles loading and parsing of transit network and accessibility data
"""

import pandas as pd
import networkx as nx
import json
import geojson
from typing import Dict, List, Optional, Union
from pathlib import Path
import csv


class DataLoader:
    """
    Handles loading and parsing of various data formats for transit networks
    """
    
    def __init__(self):
        """Initialize the data loader"""
        self.supported_formats = {
            'csv': self.load_transit_csv,
            'geojson': self.load_transit_geojson,
            'json': self.load_accessibility_json,
            'gtfs': self.load_gtfs_data
        }
    
    def load_transit_csv(self, file_path: str) -> nx.Graph:
        """
        Load transit network from CSV file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            NetworkX Graph representing the transit network
        """
        try:
            df = pd.read_csv(file_path)
            
            # Validate required columns
            required_columns = ['from_stop', 'to_stop', 'travel_time']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Create graph
            graph = nx.Graph()
            
            # Add edges with attributes
            for _, row in df.iterrows():
                from_stop = str(row['from_stop']).strip()
                to_stop = str(row['to_stop']).strip()
                
                # Edge attributes
                edge_attrs = {
                    'travel_time': float(row['travel_time']),
                    'route_id': str(row.get('route_id', 'unknown')),
                    'wheelchair_accessible': self._parse_boolean(row.get('wheelchair_accessible', False)),
                    'has_elevator': self._parse_boolean(row.get('has_elevator', False)),
                    'has_stairs': self._parse_boolean(row.get('has_stairs', True)),
                    'low_floor': self._parse_boolean(row.get('low_floor', False)),
                    'wide_doors': self._parse_boolean(row.get('wide_doors', False))
                }
                
                # Add additional attributes if present
                for col in df.columns:
                    if col not in ['from_stop', 'to_stop'] and col not in edge_attrs:
                        edge_attrs[col] = row[col]
                
                graph.add_edge(from_stop, to_stop, **edge_attrs)
            
            print(f"Loaded transit network: {graph.number_of_nodes()} stops, {graph.number_of_edges()} connections")
            return graph
            
        except Exception as e:
            raise ValueError(f"Error loading CSV file {file_path}: {str(e)}")
    
    def load_accessibility_json(self, file_path: str) -> Dict:
        """
        Load accessibility metadata from JSON file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Dictionary with accessibility data for stops
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                accessibility_data = json.load(file)
            
            # Validate and normalize the data
            normalized_data = {}
            for stop_name, stop_data in accessibility_data.items():
                normalized_data[str(stop_name).strip()] = self._normalize_accessibility_data(stop_data)
            
            print(f"Loaded accessibility data for {len(normalized_data)} stops")
            return normalized_data
            
        except FileNotFoundError:
            print(f"Warning: Accessibility file {file_path} not found. Using empty accessibility data.")
            return {}
        except Exception as e:
            raise ValueError(f"Error loading accessibility JSON file {file_path}: {str(e)}")
    
    def load_transit_geojson(self, file_path: str) -> nx.Graph:
        """
        Load transit network from GeoJSON file
        
        Args:
            file_path: Path to GeoJSON file
            
        Returns:
            NetworkX Graph representing the transit network
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                geo_data = geojson.load(file)
            
            graph = nx.Graph()
            
            # Process features
            for feature in geo_data['features']:
                if feature['geometry']['type'] == 'LineString':
                    # Extract route information from properties
                    props = feature['properties']
                    route_id = props.get('route_id', 'unknown')
                    
                    # Extract coordinates (simplified - assumes stops are at endpoints)
                    coords = feature['geometry']['coordinates']
                    if len(coords) >= 2:
                        from_stop = f"Stop_{coords[0][0]:.6f}_{coords[0][1]:.6f}"
                        to_stop = f"Stop_{coords[-1][0]:.6f}_{coords[-1][1]:.6f}"
                        
                        # Calculate approximate travel time (simplified)
                        travel_time = props.get('travel_time', 5)  # Default 5 minutes
                        
                        graph.add_edge(from_stop, to_stop, 
                                     travel_time=travel_time,
                                     route_id=route_id,
                                     coordinates=coords)
            
            print(f"Loaded GeoJSON transit network: {graph.number_of_nodes()} stops, {graph.number_of_edges()} connections")
            return graph
            
        except Exception as e:
            raise ValueError(f"Error loading GeoJSON file {file_path}: {str(e)}")
    
    def load_gtfs_data(self, gtfs_folder: str) -> nx.Graph:
        """
        Load transit network from GTFS (General Transit Feed Specification) data
        
        Args:
            gtfs_folder: Path to folder containing GTFS files
            
        Returns:
            NetworkX Graph representing the transit network
        """
        try:
            gtfs_path = Path(gtfs_folder)
            
            # Load required GTFS files
            stops_df = pd.read_csv(gtfs_path / 'stops.txt')
            stop_times_df = pd.read_csv(gtfs_path / 'stop_times.txt')
            trips_df = pd.read_csv(gtfs_path / 'trips.txt')
            routes_df = pd.read_csv(gtfs_path / 'routes.txt')
            
            # Merge data to create connections
            merged_df = stop_times_df.merge(trips_df, on='trip_id')
            merged_df = merged_df.merge(routes_df, on='route_id')
            merged_df = merged_df.merge(stops_df, left_on='stop_id', right_on='stop_id')
            
            # Create graph
            graph = nx.Graph()
