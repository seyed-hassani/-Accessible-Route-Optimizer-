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
            
            # Group by trip to create sequential connections
            for trip_id, trip_stops in merged_df.groupby('trip_id'):
                trip_stops = trip_stops.sort_values('stop_sequence')
                stops_list = trip_stops.to_dict('records')
                
                # Create edges between consecutive stops
                for i in range(len(stops_list) - 1):
                    from_stop = stops_list[i]['stop_name']
                    to_stop = stops_list[i + 1]['stop_name']
                    
                    # Calculate travel time (simplified)
                    from_time = self._parse_gtfs_time(stops_list[i]['departure_time'])
                    to_time = self._parse_gtfs_time(stops_list[i + 1]['arrival_time'])
                    travel_time = max(1, (to_time - from_time) / 60)  # Convert to minutes
                    
                    # Add edge with route information
                    graph.add_edge(from_stop, to_stop,
                                 travel_time=travel_time,
                                 route_id=stops_list[i]['route_short_name'],
                                 route_type=stops_list[i]['route_type'],
                                 wheelchair_accessible=stops_list[i].get('wheelchair_accessible', 0) == 1)
            
            print(f"Loaded GTFS transit network: {graph.number_of_nodes()} stops, {graph.number_of_edges()} connections")
            return graph
            
        except Exception as e:
            raise ValueError(f"Error loading GTFS data from {gtfs_folder}: {str(e)}")
    
    def _parse_gtfs_time(self, time_str: str) -> int:
        """
        Parse GTFS time format (HH:MM:SS) to seconds since midnight
        
        Args:
            time_str: Time string in HH:MM:SS format
            
        Returns:
            Seconds since midnight
        """
        try:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except:
            return 0
    
    def _parse_boolean(self, value: Union[str, bool, int]) -> bool:
        """
        Parse various boolean representations
        
        Args:
            value: Value to parse as boolean
            
        Returns:
            Boolean value
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'y', 't']
        return False
    
    def _normalize_accessibility_data(self, stop_data: Dict) -> Dict:
        """
        Normalize accessibility data for a stop
        
        Args:
            stop_data: Raw accessibility data
            
        Returns:
            Normalized accessibility data
        """
        normalized = {}
        
        # Boolean fields
        boolean_fields = [
            'wheelchair_accessible', 'has_elevator', 'has_stairs', 'has_ramp',
            'elevator_working', 'audio_announcements', 'visual_displays',
            'tactile_guidance', 'wide_doors', 'level_boarding', 'low_floor_service'
        ]
        
        for field in boolean_fields:
            if field in stop_data:
                normalized[field] = self._parse_boolean(stop_data[field])
        
        # String fields
        string_fields = ['platform_gap', 'surface_type', 'lighting_quality']
        for field in string_fields:
            if field in stop_data:
                normalized[field] = str(stop_data[field]).lower()
        
        # Numeric fields
        numeric_fields = ['platform_width', 'door_width', 'ramp_grade']
        for field in numeric_fields:
            if field in stop_data:
                try:
                    normalized[field] = float(stop_data[field])
                except ValueError:
                    pass
        
        return normalized
    
    def export_transit_csv(self, graph: nx.Graph, file_path: str):
        """
        Export transit network graph to CSV format
        
        Args:
            graph: NetworkX graph to export
            file_path: Output CSV file path
        """
        try:
            edges_data = []
            
            for u, v, data in graph.edges(data=True):
                edge_data = {
                    'from_stop': u,
                    'to_stop': v,
                    **data
                }
                edges_data.append(edge_data)
            
            df = pd.DataFrame(edges_data)
            df.to_csv(file_path, index=False)
            print(f"Exported transit network to {file_path}")
            
        except Exception as e:
            raise ValueError(f"Error exporting to CSV {file_path}: {str(e)}")
    
    def export_accessibility_json(self, accessibility_data: Dict, file_path: str):
        """
        Export accessibility data to JSON format
        
        Args:
            accessibility_data: Accessibility data dictionary
            file_path: Output JSON file path
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(accessibility_data, file, indent=2, ensure_ascii=False)
            print(f"Exported accessibility data to {file_path}")
            
        except Exception as e:
            raise ValueError(f"Error exporting to JSON {file_path}: {str(e)}")
    
    def validate_data_consistency(self, graph: nx.Graph, accessibility_data: Dict) -> Dict:
        """
        Validate consistency between transit network and accessibility data
        
        Args:
            graph: Transit network graph
            accessibility_data: Accessibility data dictionary
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check for stops in graph but not in accessibility data
        graph_stops = set(graph.nodes())
        accessibility_stops = set(accessibility_data.keys())
        
        missing_accessibility = graph_stops - accessibility_stops
        if missing_accessibility:
            results['warnings'].append(
                f"Stops without accessibility data: {list(missing_accessibility)[:10]}..."
                if len(missing_accessibility) > 10 else 
                f"Stops without accessibility data: {list(missing_accessibility)}"
            )
        
        # Check for accessibility data without corresponding stops
        extra_accessibility = accessibility_stops - graph_stops
        if extra_accessibility:
            results['warnings'].append(
                f"Accessibility data for non-existent stops: {list(extra_accessibility)[:10]}..."
                if len(extra_accessibility) > 10 else
                f"Accessibility data for non-existent stops: {list(extra_accessibility)}"
            )
        
        # Check for disconnected components
        if not nx.is_connected(graph):
            components = list(nx.connected_components(graph))
            results['warnings'].append(
                f"Network has {len(components)} disconnected components"
            )
        
        # Check for negative travel times
        negative_times = []
        for u, v, data in graph.edges(data=True):
            if data.get('travel_time', 0) <= 0:
                negative_times.append((u, v))
        
        if negative_times:
            results['errors'].append(
                f"Edges with non-positive travel times: {negative_times[:5]}..."
                if len(negative_times) > 5 else
                f"Edges with non-positive travel times: {negative_times}"
            )
            results['valid'] = False
        
        return results
    
    def get_data_summary(self, graph: nx.Graph, accessibility_data: Dict) -> Dict:
        """
        Generate summary statistics for loaded data
        
        Args:
            graph: Transit network graph
            accessibility_data: Accessibility data dictionary
            
        Returns:
            Dictionary with summary statistics
        """
        # Graph statistics
        graph_stats = {
            'total_stops': graph.number_of_nodes(),
            'total_connections': graph.number_of_edges(),
            'average_degree': sum(dict(graph.degree()).values()) / graph.number_of_nodes() if graph.number_of_nodes() > 0 else 0,
            'is_connected': nx.is_connected(graph),
            'number_of_components': nx.number_connected_components(graph)
        }
        
        # Route statistics
        routes = set()
        travel_times = []
        for u, v, data in graph.edges(data=True):
            routes.add(data.get('route_id', 'unknown'))
            travel_times.append(data.get('travel_time', 0))
        
        graph_stats.update({
            'unique_routes': len(routes),
            'avg_travel_time': sum(travel_times) / len(travel_times) if travel_times else 0,
            'min_travel_time': min(travel_times) if travel_times else 0,
            'max_travel_time': max(travel_times) if travel_times else 0
        })
        
        # Accessibility statistics
        accessibility_stats = {
            'stops_with_accessibility_data': len(accessibility_data),
            'wheelchair_accessible_stops': 0,
            'stops_with_elevators': 0,
            'stops_with_ramps': 0,
            'stops_with_audio': 0,
            'stops_with_visual': 0
        }
        
        for stop_data in accessibility_data.values():
            if stop_data.get('wheelchair_accessible', False):
                accessibility_stats['wheelchair_accessible_stops'] += 1
            if stop_data.get('has_elevator', False):
                accessibility_stats['stops_with_elevators'] += 1
            if stop_data.get('has_ramp', False):
                accessibility_stats['stops_with_ramps'] += 1
            if stop_data.get('audio_announcements', False):
                accessibility_stats['stops_with_audio'] += 1
            if stop_data.get('visual_displays', False):
                accessibility_stats['stops_with_visual'] += 1
        
        return {
            'graph_statistics': graph_stats,
            'accessibility_statistics': accessibility_stats,
            'data_coverage': {
                'accessibility_coverage': len(accessibility_data) / graph.number_of_nodes() * 100 if graph.number_of_nodes() > 0 else 0
            }
        }
            
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
