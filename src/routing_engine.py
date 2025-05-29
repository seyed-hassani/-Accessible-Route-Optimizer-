"""
Accessible Route Optimizer - Core Routing Engine
Implements Dijkstra's algorithm with accessibility constraints
"""

import networkx as nx
from typing import List, Dict, Optional, Set, Tuple
import heapq
from accessibility import AccessibilityFilter


class AccessibleRouter:
    """
    Main routing engine that finds optimal paths considering accessibility needs
    """
    
    def __init__(self, transit_graph: nx.Graph, accessibility_data: Dict):
        """
        Initialize the router with transit network and accessibility data
        
        Args:
            transit_graph: NetworkX graph representing transit network
            accessibility_data: Dictionary with accessibility metadata for stops
        """
        self.graph = transit_graph
        self.accessibility_data = accessibility_data
        self.accessibility_filter = AccessibilityFilter(accessibility_data)
        
    def find_path(self, start: str, end: str) -> Dict:
        """
        Find the shortest path between two stops (basic routing)
        
        Args:
            start: Starting stop name
            end: Destination stop name
            
        Returns:
            Dictionary with path details, time, and transfers
        """
        try:
            path = nx.shortest_path(self.graph, start, end, weight='travel_time')
            total_time = nx.shortest_path_length(self.graph, start, end, weight='travel_time')
            
            # Calculate transfers and route details
            details = self._build_route_details(path)
            transfers = self._count_transfers(details)
            
            return {
                'path': path,
                'total_time': total_time,
                'transfers': transfers,
                'details': details,
                'accessible': False  # Basic routing doesn't guarantee accessibility
            }
            
        except nx.NetworkXNoPath:
            return {
                'path': None,
                'message': f"No route found between {start} and {end}"
            }
        except nx.NodeNotFound as e:
            return {
                'path': None,
                'message': f"Stop not found: {str(e)}"
            }
    
    def find_accessible_path(self, start: str, end: str, requirements: List[str]) -> Dict:
        """
        Find the shortest accessible path between two stops
        
        Args:
            start: Starting stop name
            end: Destination stop name
            requirements: List of accessibility requirements
            
        Returns:
            Dictionary with path details, time, transfers, and accessibility info
        """
        try:
            # Create filtered graph based on accessibility requirements
            accessible_graph = self._create_accessible_graph(requirements)
            
            if start not in accessible_graph.nodes or end not in accessible_graph.nodes:
                return {
                    'path': None,
                    'message': f"Start or end stop not accessible with requirements: {requirements}"
                }
            
            # Find path in filtered graph
            path = nx.shortest_path(accessible_graph, start, end, weight='travel_time')
            total_time = nx.shortest_path_length(accessible_graph, start, end, weight='travel_time')
            
            # Build detailed route information
            details = self._build_route_details(path, include_accessibility=True)
            transfers = self._count_transfers(details)
            
            return {
                'path': path,
                'total_time': total_time,
                'transfers': transfers,
                'details': details,
                'accessible': True,
                'requirements_met': requirements
            }
            
        except nx.NetworkXNoPath:
            return {
                'path': None,
                'message': f"No accessible route found between {start} and {end} with requirements: {requirements}"
            }
        except nx.NodeNotFound as e:
            return {
                'path': None,
                'message': f"Stop not found: {str(e)}"
            }
    
    def _create_accessible_graph(self, requirements: List[str]) -> nx.Graph:
        """
        Create a filtered graph containing only accessible routes
        
        Args:
            requirements: List of accessibility requirements
            
        Returns:
            Filtered NetworkX graph
        """
        accessible_graph = self.graph.copy()
        
        # Remove inaccessible nodes
        nodes_to_remove = []
        for node in accessible_graph.nodes():
            if not self.accessibility_filter.meets_requirements(node, requirements):
                nodes_to_remove.append(node)
        
        accessible_graph.remove_nodes_from(nodes_to_remove)
        
        # Remove inaccessible edges
        edges_to_remove = []
        for u, v, data in accessible_graph.edges(data=True):
            if not self.accessibility_filter.edge_meets_requirements(u, v, data, requirements):
                edges_to_remove.append((u, v))
        
        accessible_graph.remove_edges_from(edges_to_remove)
        
        return accessible_graph
    
    def _build_route_details(self, path: List[str], include_accessibility: bool = False) -> List[Dict]:
        """
        Build detailed information for each segment of the route
        
        Args:
            path: List of stops in the route
            include_accessibility: Whether to include accessibility information
            
        Returns:
            List of route segment details
        """
        details = []
        
        for i in range(len(path) - 1):
            from_stop = path[i]
            to_stop = path[i + 1]
            
            # Get edge data
            edge_data = self.graph.get_edge_data(from_stop, to_stop, {})
            
            segment = {
                'from': from_stop,
                'to': to_stop,
                'route': edge_data.get('route_id', 'Unknown'),
                'time': edge_data.get('travel_time', 0)
            }
            
            if include_accessibility:
                # Add accessibility information
                accessibility_notes = []
                
                if edge_data.get('wheelchair_accessible'):
                    accessibility_notes.append("Wheelchair accessible")
                if edge_data.get('has_elevator') and self.accessibility_data.get(from_stop, {}).get('elevator_working', True):
                    accessibility_notes.append("Elevator available")
                if not edge_data.get('has_stairs', True):
                    accessibility_notes.append("No stairs")
                
                if accessibility_notes:
                    segment['accessibility_notes'] = "; ".join(accessibility_notes)
            
            details.append(segment)
        
        return details
    
    def _count_transfers(self, details: List[Dict]) -> int:
        """
        Count the number of transfers required for a route
        
        Args:
            details: List of route segment details
            
        Returns:
            Number of transfers
        """
        if len(details) <= 1:
            return 0
        
        transfers = 0
        current_route = None
        
        for segment in details:
            route = segment['route']
            if current_route is not None and route != current_route:
                transfers += 1
            current_route = route
        
        return transfers
    
    def update_accessibility(self, stop: str, **accessibility_updates):
        """
        Update accessibility information for a stop (e.g., elevator outage)
        
        Args:
            stop: Stop name to update
            **accessibility_updates: Accessibility attributes to update
        """
        if stop not in self.accessibility_data:
            self.accessibility_data[stop] = {}
        
        self.accessibility_data[stop].update(accessibility_updates)
        
        # Update the accessibility filter
        self.accessibility_filter = AccessibilityFilter(self.accessibility_data)
    
    def get_accessibility_info(self, stop: str) -> Dict:
        """
        Get accessibility information for a specific stop
        
        Args:
            stop: Stop name
            
        Returns:
            Dictionary with accessibility information
        """
        return self.accessibility_data.get(stop, {})
    
    def get_accessible_stops(self, requirements: List[str]) -> List[str]:
        """
        Get list of stops that meet specific accessibility requirements
        
        Args:
            requirements: List of accessibility requirements
            
        Returns:
            List of accessible stop names
        """
        accessible_stops = []
        
        for stop in self.graph.nodes():
            if self.accessibility_filter.meets_requirements(stop, requirements):
                accessible_stops.append(stop)
        
        return accessible_stops
