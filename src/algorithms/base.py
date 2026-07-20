from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from src.models import Edge

@dataclass
class SearchNode:
    node_id: str
    parent: Optional['SearchNode'] = None
    g_cost: float = 0.0          # Path cost from start to this node
    h_cost: float = 0.0          # Heuristic estimate to target
    f_cost: float = 0.0          # g_cost + h_cost
    edge_taken: Optional[Edge] = None # Edge used to reach this node

    def __lt__(self, other: 'SearchNode') -> bool:
        # Comparison used by priority queues
        return self.f_cost < other.f_cost

@dataclass
class SearchResult:
    algorithm_name: str
    path: List[str]             # List of node IDs from start to target
    explored_nodes: List[str]   # Order of node expansion
    total_cost: float           # Total calculated cost
    total_distance: float       # Total physical distance (meters)
    total_time: float           # Total travel time (seconds, adjusted for congestion)
    explored_count: int         # Number of nodes expanded
    execution_time_ms: float = 0.0

def reconstruct_path(final_node: Optional[SearchNode]) -> List[SearchNode]:
    """
    Traces back from the goal node to the start node to construct the path.
    """
    path = []
    current = final_node
    while current is not None:
        path.append(current)
        current = current.parent
    return path[::-1] # Reverse to get start -> goal
