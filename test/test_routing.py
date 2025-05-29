#!/usr/bin/env python3
"""
Unit tests for the Accessible Route Optimizer
"""

import unittest
import sys
import networkx as nx
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from routing_engine import AccessibleRouter
from accessibility import AccessibilityFilter
from data_loader import DataLoader


class TestDataLoader(unittest.TestCase):
    """Test cases for the DataLoader class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.data_loader = DataLoader()
        self.test_data_path = Path(__file__).parent.parent / 'data'
    
    def test_load_transit_csv(self):
        """Test loading transit network from CSV"""
        try:
            graph = self.data_loader.load_transit_csv(self.test_data_path / 'sample_transit.csv')
            
            # Check that graph was created
            self.assertIsInstance(graph, nx.Graph)
            self.assertGreater(graph.number_of_nodes(), 0)
            self.assertGreater(graph.number_of_edges(), 0)
            
            # Check specific nodes exist
            self.assertIn('Union Station', graph.nodes())
            self.assertIn('Bloor-Yonge', graph.nodes())
            
            # Check edge attributes
            edge_data = graph.get_edge_data('Union Station', 'King')
            self.assertIsNotNone(edge_data)
            self.assertIn('travel_time', edge_data)
            self.assertIn('wheelchair_accessible', edge_data)
            
        except FileNotFoundError:
            self.skipTest("Sample transit data file not found")
    
    def test_load_accessibility_json(self):
        """Test loading accessibility metadata from JSON"""
        try:
            accessibility_data = self.data_loader.load_accessibility_json(
                self.test_data_path / 'accessibility.json'
            )
            
            # Check that data was loaded
            self.assertIsInstance(accessibility_data, dict)
            self.assertGreater(len(accessibility_data), 0)
            
            # Check specific stop data
            if 'Union Station' in accessibility_data:
                union_data = accessibility_data['Union Station']
                self.assertIn('wheelchair_accessible', union_data)
                self.assertIn('has_elevator', union_data)
                self.assertIsInstance(union_data['wheelchair_accessible'], bool)
                
        except FileNotFoundError:
            self.skipTest("Accessibility data file not found")
    
    def test_parse_boolean(self):
        """Test boolean parsing functionality"""
        # Test various boolean representations
        self.assertTrue(self.data_loader._parse_boolean(True))
        self.assertTrue(self.data_loader._parse_boolean('true'))
        self
