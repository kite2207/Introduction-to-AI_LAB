from dataclasses import dataclass, field
from typing import Any, List, Dict
import json

@dataclass
class Node:
    node_id: str
    name: str
    lat: float
    lng: float
    node_type: str = "intersection"

@dataclass
class Edge:
    source_id: str
    target_id: str
    distance: float            # in meters
    estimated_time: float      # in seconds (normal conditions)
    congestion_level: int      # 1 (smooth) to 5 (gridlock)
    road_type: str             # e.g., "alley", "local_road", "avenue"
    direction: str             # "one-way" or "two-way"
    risk_factors: List[str] = field(default_factory=list)

    def get_risk_penalty(self) -> float:
        """
        Maps risk factors to numerical penalty values (in equivalent seconds/meters).
        """
        risk_costs = {
            "flooding": 300.0,      # High penalty (adds 5 mins delay)
            "construction": 120.0,  # Moderate penalty (adds 2 mins delay)
            "narrow_road": 60.0,    # Slow down penalty (adds 1 min delay)
            "complex_intersection": 45.0 # (adds 45s delay)
        }
        return sum(risk_costs.get(factor, 0.0) for factor in self.risk_factors)

class TrafficGraph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.adjacency_list: Dict[str, List[Edge]] = {}

    def add_node(self, node: Node):
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency_list:
            self.adjacency_list[node.node_id] = []

    def add_edge_data(self, edge: Edge):
        # 1. Add edge in the forward direction (source_id -> target_id)
        self.adjacency_list[edge.source_id].append(edge)

    def load_from_json(self, nodes_path: str, edges_path: str):
        self.nodes.clear()
        self.adjacency_list.clear()

        # Load nodes
        with open(nodes_path, 'r', encoding='utf-8') as f:
            nodes_data = json.load(f)
            for nd in nodes_data:
                self.add_node(Node(**nd))
                
        # Load edges
        with open(edges_path, 'r', encoding='utf-8') as f:
            edges_data = json.load(f)
            for ed in edges_data:
                self.add_edge_data(Edge(**ed))

    def load_from_hcm_data(self, data: Dict[str, Any]):
        """Load and validate the canonical HCM traffic-data structure."""
        if not isinstance(data, dict):
            raise ValueError("HCM traffic data must be a JSON object")

        self.nodes.clear()
        self.adjacency_list.clear()

        for raw_node_id, raw_node in data.items():
            node_id = str(raw_node_id)
            if not isinstance(raw_node, dict):
                raise ValueError(f"Node '{node_id}' must be a JSON object")

            lat = raw_node.get("lat")
            lng = raw_node.get("lng")
            if not isinstance(lat, (int, float)) or not -90 <= lat <= 90:
                raise ValueError(f"Node '{node_id}' has invalid latitude: {lat!r}")
            if not isinstance(lng, (int, float)) or not -180 <= lng <= 180:
                raise ValueError(f"Node '{node_id}' has invalid longitude: {lng!r}")

            self.add_node(Node(
                node_id=node_id,
                name=raw_node.get("name") or node_id,
                lat=float(lat),
                lng=float(lng),
                node_type=raw_node.get("type") or "intersection",
            ))

        for raw_source_id, raw_node in data.items():
            source_id = str(raw_source_id)
            connections = raw_node.get("connected_to", [])
            if not isinstance(connections, list):
                raise ValueError(f"Node '{source_id}' has invalid connected_to")

            for index, connection in enumerate(connections):
                if not isinstance(connection, dict):
                    raise ValueError(
                        f"Edge {source_id}[{index}] must be a JSON object"
                    )

                target = connection.get("target_node")
                target_id = str(target) if target is not None else ""
                if target_id not in self.nodes:
                    raise ValueError(
                        f"Edge {source_id}[{index}] targets unknown node '{target_id}'"
                    )

                distance = connection.get("distance")
                estimated_time = connection.get("estimated_time")
                congestion = connection.get("congestion_level", 1)
                if not isinstance(distance, (int, float)) or distance < 0:
                    raise ValueError(f"Edge {source_id}->{target_id} has invalid distance")
                if not isinstance(estimated_time, (int, float)) or estimated_time < 0:
                    raise ValueError(f"Edge {source_id}->{target_id} has invalid estimated_time")
                if not isinstance(congestion, int) or not 1 <= congestion <= 5:
                    raise ValueError(f"Edge {source_id}->{target_id} has invalid congestion_level")

                risk_factors = connection.get("risk_factors", [])
                if not isinstance(risk_factors, list):
                    raise ValueError(f"Edge {source_id}->{target_id} has invalid risk_factors")

                self.add_edge_data(Edge(
                    source_id=source_id,
                    target_id=target_id,
                    distance=float(distance),
                    estimated_time=float(estimated_time),
                    congestion_level=congestion,
                    road_type=connection.get("road_type") or "unknown",
                    direction=connection.get("direction") or "two-way",
                    risk_factors=risk_factors,
                ))

    def get_neighbors(self, node_id: str) -> List[Edge]:
        return self.adjacency_list.get(node_id, [])


class CostEvaluator:
    def __init__(self, optimization: str = "mixed"):
        self.optimization = optimization

    def calculate_cost(self, edge: Edge) -> float:
        # Hệ số nhân thời gian dựa trên mức độ kẹt xe (clamp về 1 nếu level = 0 hoặc ngoài bảng)
        congestion_multipliers = {1: 1.0, 2: 1.3, 3: 1.8, 4: 2.4, 5: 3.5}
        safe_level = max(1, edge.congestion_level)  # guard against level 0
        time_multiplier = congestion_multipliers.get(safe_level, 1.0)
        
        # Hệ số phạt khoảng cách dựa trên kẹt xe
        distance_multiplier = 1.0 + 0.1 * (safe_level - 1)
        
        effective_distance = edge.distance * distance_multiplier
        effective_time = edge.estimated_time * time_multiplier + edge.get_risk_penalty()

        if self.optimization == "distance":
            return effective_distance
            
        elif self.optimization == "time":
            return effective_time
            
        else: # "mixed"
            # Quy đổi thời gian ra khoảng cách tương đương để cộng dồn
            # Vận tốc trung bình ~10 m/s -> 1 giây tương đương 10 mét chi phí, chia trung bình.
            return (effective_distance + (effective_time * 10.0)) / 2.0
