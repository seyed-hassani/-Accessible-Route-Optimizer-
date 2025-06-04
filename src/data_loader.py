"""
Accessible Route Optimizer - Data Loading Module
Handles loading and parsing of transit network and accessibility data
"""

import json
from pathlib import Path
from typing import Dict, List, Union

import geojson
import networkx as nx
import pandas as pd


class DataLoader:
    """Handles loading and parsing of various data formats for transit networks."""

    def __init__(self):
        self.supported_formats = {
            "csv": self.load_transit_csv,
            "geojson": self.load_transit_geojson,
            "json": self.load_accessibility_json,
            "gtfs": self.load_gtfs_data,
        }

    def load_transit_csv(self, file_path: str) -> nx.Graph:
        """Load transit network from CSV file."""
        try:
            df = pd.read_csv(file_path)

            required_columns = ["from_stop", "to_stop", "travel_time"]
            missing = [c for c in required_columns if c not in df.columns]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

            graph = nx.Graph()
            for _, row in df.iterrows():
                from_stop = str(row["from_stop"]).strip()
                to_stop = str(row["to_stop"]).strip()

                edge_attrs = {
                    "travel_time": float(row["travel_time"]),
                    "route_id": str(row.get("route_id", "unknown")),
                    "wheelchair_accessible": self._parse_boolean(row.get("wheelchair_accessible", False)),
                    "has_elevator": self._parse_boolean(row.get("has_elevator", False)),
                    "has_stairs": self._parse_boolean(row.get("has_stairs", True)),
                    "low_floor": self._parse_boolean(row.get("low_floor", False)),
                    "wide_doors": self._parse_boolean(row.get("wide_doors", False)),
                }

                for col in df.columns:
                    if col not in ["from_stop", "to_stop"] and col not in edge_attrs:
                        edge_attrs[col] = row[col]

                graph.add_edge(from_stop, to_stop, **edge_attrs)

            print(
                f"Loaded transit network: {graph.number_of_nodes()} stops, {graph.number_of_edges()} connections"
            )
            return graph
        except Exception as e:
            raise ValueError(f"Error loading CSV file {file_path}: {e}")

    def load_accessibility_json(self, file_path: str) -> Dict:
        """Load accessibility metadata from JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                accessibility_data = json.load(f)

            normalized_data = {
                str(stop).strip(): self._normalize_accessibility_data(data)
                for stop, data in accessibility_data.items()
            }
            print(f"Loaded accessibility data for {len(normalized_data)} stops")
            return normalized_data
        except FileNotFoundError:
            print(
                f"Warning: Accessibility file {file_path} not found. Using empty accessibility data."
            )
            return {}
        except Exception as e:
            raise ValueError(f"Error loading accessibility JSON file {file_path}: {e}")

    def load_transit_geojson(self, file_path: str) -> nx.Graph:
        """Load transit network from GeoJSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                geo_data = geojson.load(f)

            graph = nx.Graph()
            for feature in geo_data["features"]:
                if feature["geometry"]["type"] == "LineString":
                    props = feature["properties"]
                    route_id = props.get("route_id", "unknown")
                    coords = feature["geometry"]["coordinates"]
                    if len(coords) >= 2:
                        from_stop = f"Stop_{coords[0][0]:.6f}_{coords[0][1]:.6f}"
                        to_stop = f"Stop_{coords[-1][0]:.6f}_{coords[-1][1]:.6f}"
                        travel_time = props.get("travel_time", 5)
                        graph.add_edge(
                            from_stop,
                            to_stop,
                            travel_time=travel_time,
                            route_id=route_id,
                            coordinates=coords,
                        )
            print(
                f"Loaded GeoJSON transit network: {graph.number_of_nodes()} stops, {graph.number_of_edges()} connections"
            )
            return graph
        except Exception as e:
            raise ValueError(f"Error loading GeoJSON file {file_path}: {e}")

    def load_gtfs_data(self, gtfs_folder: str) -> nx.Graph:
        """Load transit network from a folder containing GTFS files."""
        try:
            gtfs_path = Path(gtfs_folder)
            stops_df = pd.read_csv(gtfs_path / "stops.txt")
            stop_times_df = pd.read_csv(gtfs_path / "stop_times.txt")
            trips_df = pd.read_csv(gtfs_path / "trips.txt")
            routes_df = pd.read_csv(gtfs_path / "routes.txt")

            merged = (
                stop_times_df.merge(trips_df, on="trip_id")
                .merge(routes_df, on="route_id")
                .merge(stops_df, left_on="stop_id", right_on="stop_id")
            )

            graph = nx.Graph()
            for trip_id, trip_stops in merged.groupby("trip_id"):
                trip_stops = trip_stops.sort_values("stop_sequence")
                records = trip_stops.to_dict("records")
                for i in range(len(records) - 1):
                    from_stop = records[i]["stop_name"]
                    to_stop = records[i + 1]["stop_name"]
                    from_time = self._parse_gtfs_time(records[i]["departure_time"])
                    to_time = self._parse_gtfs_time(records[i + 1]["arrival_time"])
                    travel_time = max(1, (to_time - from_time) / 60)
                    graph.add_edge(
                        from_stop,
                        to_stop,
                        travel_time=travel_time,
                        route_id=records[i]["route_short_name"],
                        route_type=records[i]["route_type"],
                        wheelchair_accessible=records[i].get("wheelchair_accessible", 0) == 1,
                    )
            print(
                f"Loaded GTFS transit network: {graph.number_of_nodes()} stops, {graph.number_of_edges()} connections"
            )
            return graph
        except Exception as e:
            raise ValueError(f"Error loading GTFS data from {gtfs_folder}: {e}")

    def _parse_gtfs_time(self, time_str: str) -> int:
        try:
            parts = time_str.split(":")
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except Exception:
            return 0

    def _parse_boolean(self, value: Union[str, bool, int]) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            return value.lower() in ["true", "1", "yes", "y", "t"]
        return False

    def _normalize_accessibility_data(self, stop_data: Dict) -> Dict:
        normalized: Dict[str, Union[bool, float, str]] = {}
        boolean_fields = [
            "wheelchair_accessible",
            "has_elevator",
            "has_stairs",
            "has_ramp",
            "elevator_working",
            "audio_announcements",
            "visual_displays",
            "tactile_guidance",
            "wide_doors",
            "level_boarding",
            "low_floor_service",
        ]
        for field in boolean_fields:
            if field in stop_data:
                normalized[field] = self._parse_boolean(stop_data[field])

        string_fields = ["platform_gap", "surface_type", "lighting_quality"]
        for field in string_fields:
            if field in stop_data:
                normalized[field] = str(stop_data[field]).lower()

        numeric_fields = ["platform_width", "door_width", "ramp_grade"]
        for field in numeric_fields:
            if field in stop_data:
                try:
                    normalized[field] = float(stop_data[field])
                except ValueError:
                    pass
        return normalized

    def export_transit_csv(self, graph: nx.Graph, file_path: str) -> None:
        try:
            edges_data: List[Dict[str, Union[str, float, bool]]] = []
            for u, v, data in graph.edges(data=True):
                edges_data.append({"from_stop": u, "to_stop": v, **data})
            pd.DataFrame(edges_data).to_csv(file_path, index=False)
            print(f"Exported transit network to {file_path}")
        except Exception as e:
            raise ValueError(f"Error exporting to CSV {file_path}: {e}")

    def export_accessibility_json(self, accessibility_data: Dict, file_path: str) -> None:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(accessibility_data, f, indent=2, ensure_ascii=False)
            print(f"Exported accessibility data to {file_path}")
        except Exception as e:
            raise ValueError(f"Error exporting to JSON {file_path}: {e}")

    def validate_data_consistency(self, graph: nx.Graph, accessibility_data: Dict) -> Dict:
        results = {"valid": True, "warnings": [], "errors": []}
        graph_stops = set(graph.nodes())
        accessibility_stops = set(accessibility_data.keys())
        missing_accessibility = graph_stops - accessibility_stops
        if missing_accessibility:
            results["warnings"].append(
                f"Stops without accessibility data: {list(missing_accessibility)[:10]}..."
                if len(missing_accessibility) > 10
                else f"Stops without accessibility data: {list(missing_accessibility)}"
            )
        extra_accessibility = accessibility_stops - graph_stops
        if extra_accessibility:
            results["warnings"].append(
                f"Accessibility data for non-existent stops: {list(extra_accessibility)[:10]}..."
                if len(extra_accessibility) > 10
                else f"Accessibility data for non-existent stops: {list(extra_accessibility)}"
            )
        if not nx.is_connected(graph):
            components = list(nx.connected_components(graph))
            results["warnings"].append(
                f"Network has {len(components)} disconnected components"
            )
        negative_times = []
        for u, v, data in graph.edges(data=True):
            if data.get("travel_time", 0) <= 0:
                negative_times.append((u, v))
        if negative_times:
            results["errors"].append(
                f"Edges with non-positive travel times: {negative_times[:5]}..."
                if len(negative_times) > 5
                else f"Edges with non-positive travel times: {negative_times}"
            )
            results["valid"] = False
        return results

    def get_data_summary(self, graph: nx.Graph, accessibility_data: Dict) -> Dict:
        graph_stats = {
            "total_stops": graph.number_of_nodes(),
            "total_connections": graph.number_of_edges(),
            "average_degree": sum(dict(graph.degree()).values()) / graph.number_of_nodes()
            if graph.number_of_nodes() > 0
            else 0,
            "is_connected": nx.is_connected(graph),
            "number_of_components": nx.number_connected_components(graph),
        }
        routes = set()
        travel_times = []
        for u, v, data in graph.edges(data=True):
            routes.add(data.get("route_id", "unknown"))
            travel_times.append(data.get("travel_time", 0))
        graph_stats.update(
            {
                "unique_routes": len(routes),
                "avg_travel_time": sum(travel_times) / len(travel_times) if travel_times else 0,
                "min_travel_time": min(travel_times) if travel_times else 0,
                "max_travel_time": max(travel_times) if travel_times else 0,
            }
        )
        accessibility_stats = {
            "stops_with_accessibility_data": len(accessibility_data),
            "wheelchair_accessible_stops": 0,
            "stops_with_elevators": 0,
            "stops_with_ramps": 0,
            "stops_with_audio": 0,
            "stops_with_visual": 0,
        }
        for stop_data in accessibility_data.values():
            if stop_data.get("wheelchair_accessible", False):
                accessibility_stats["wheelchair_accessible_stops"] += 1
            if stop_data.get("has_elevator", False):
                accessibility_stats["stops_with_elevators"] += 1
            if stop_data.get("has_ramp", False):
                accessibility_stats["stops_with_ramps"] += 1
            if stop_data.get("audio_announcements", False):
                accessibility_stats["stops_with_audio"] += 1
            if stop_data.get("visual_displays", False):
                accessibility_stats["stops_with_visual"] += 1
        return {
            "graph_statistics": graph_stats,
            "accessibility_statistics": accessibility_stats,
            "data_coverage": {
                "accessibility_coverage": len(accessibility_data) / graph.number_of_nodes() * 100
                if graph.number_of_nodes() > 0
                else 0
            },
        }
