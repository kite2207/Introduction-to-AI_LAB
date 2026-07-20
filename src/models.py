from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
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

        # 2. If it's a two-way street, add the reverse edge (target_id -> source_id)
        if edge.direction == "two-way":
            reverse_edge = Edge(
                source_id=edge.target_id,
                target_id=edge.source_id,
                distance=edge.distance,
                estimated_time=edge.estimated_time,
                congestion_level=edge.congestion_level,
                road_type=edge.road_type,
                direction=edge.direction,
                risk_factors=edge.risk_factors.copy()
            )
            self.adjacency_list[edge.target_id].append(reverse_edge)

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

    def get_neighbors(self, node_id: str) -> List[Edge]:
        return self.adjacency_list.get(node_id, [])


class CostEvaluator:
    def __init__(self, alpha: float = 1.0, beta: float = 1.0, gamma: float = 1.0, delta: float = 1.0):
        """
        Weights to prioritize different route search criteria:
        - alpha: weight for distance (meters)
        - beta: weight for travel time (seconds)
        - gamma: weight for congestion level penalty
        - delta: weight for risk penalties
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta

    def calculate_cost(self, edge: Edge) -> float:
        # 1. Base distance cost
        distance_cost = edge.distance * self.alpha

        # 2. Congestion multiplier on time
        # E.g., Congestion levels 1 to 5 scale the estimated time:
        # level 1: 1.0x time
        # level 2: 1.3x time
        # level 3: 1.8x time
        # level 4: 2.4x time
        # level 5: 3.5x time (gridlock)
        congestion_multipliers = {1: 1.0, 2: 1.3, 3: 1.8, 4: 2.4, 5: 3.5}
        multiplier = congestion_multipliers.get(edge.congestion_level, 1.0)
        adjusted_time = edge.estimated_time * multiplier
        time_cost = adjusted_time * self.beta

        # 3. Congestion flat penalty (helps avoid congested nodes)
        congestion_flat_penalty = (edge.congestion_level ** 2) * 50.0 * self.gamma

        # 4. Risk penalty cost
        risk_cost = edge.get_risk_penalty() * self.delta

        # Total Cost
        return distance_cost + time_cost + congestion_flat_penalty + risk_cost
