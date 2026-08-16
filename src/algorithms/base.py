import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from src.models import Edge, Node

def haversine_distance(node_a: Node, node_b: Node) -> float:
    """Calculate the great-circle distance between two GPS coordinates in meters."""
    R = 6371000.0
    lat1, lng1 = math.radians(node_a.lat), math.radians(node_a.lng)
    lat2, lng2 = math.radians(node_b.lat), math.radians(node_b.lng)
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2)**2
    return R * 2 * math.asin(math.sqrt(a))


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
    # Optional step-by-step trace for frontend simulation.
    steps: List[Dict[str, Any]] = field(default_factory=list)

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

# =========================================================
# Step-tracking helper functions for all search algorithms
# =========================================================

def _frontier_snapshot(frontier):
    """Return node IDs currently waiting in the priority queue."""
    return list(dict.fromkeys(
        item[2].node_id
        for item in frontier
        if len(item) >= 3
    ))

def _path_ids(search_node):
    """Return the current parent-chain as node IDs."""
    if search_node is None:
        return []
    return [node.node_id for node in reconstruct_path(search_node)]

def _frontier_candidates(
    frontier,
    explored_set,
    current_node,
    best_costs,
    selection_metric=None,
):
    """
    Return only unexpanded nodes currently in the frontier.

    Candidates are sorted by the same criterion that the algorithm will use
    for its next selection:
      - g: UCS / Dijkstra
      - f: A*
      - h: Greedy
    """
    candidates = {}
    for item in frontier:
        if len(item) < 3:
            continue
        node = item[2]
        node_id = node.node_id
        if node_id in explored_set:
            continue
        candidate = {
            "node_id": node_id,
            "g": node.g_cost,
            "h": node.h_cost,
            "f": node.f_cost,
            "edge_cost": (
                node.g_cost -
                (current_node.g_cost if current_node else 0.0)
            ),
        }
        previous = candidates.get(node_id)
        if previous is None or candidate["g"] < previous["g"]:
            candidates[node_id] = candidate

    result = list(candidates.values())
    if selection_metric == "g":
        result.sort(key=lambda x: (x["g"], str(x["node_id"])))
    elif selection_metric == "f":
        result.sort(key=lambda x: (x["f"], str(x["node_id"])))
    elif selection_metric == "h":
        result.sort(key=lambda x: (x["h"], str(x["node_id"])))

    return result

def _next_frontier_candidate(candidates):
    """Return the candidate that the current algorithm will select next."""
    if not candidates:
        return None
    return candidates[0].get("node_id")

def _record_step(
    steps,
    current_node,
    explored_nodes,
    frontier,
    explored_edges,
    *,
    metrics=None,
    candidates=None,
    selection_metric=None,
):
    candidates = list(candidates or [])
    if selection_metric in {"g", "f", "h"}:
        key = {"g": "g", "f": "f", "h": "h"}[selection_metric]
        candidates.sort(
            key=lambda x: (x.get(key, float("inf")), str(x.get("node_id")))
        )

    steps.append({
        "step": len(steps),
        "current": current_node.node_id if current_node else None,
        "exploredNodes": list(explored_nodes),
        "frontierNodes": _frontier_snapshot(frontier),
        "exploredEdges": [dict(edge) for edge in explored_edges],
        "pathSoFar": _path_ids(current_node),
        "metrics": dict(metrics or {}),
        "candidates": candidates,
        "nextSelected": _next_frontier_candidate(candidates),
        "selectionMetric": selection_metric,
    })

def _attach_steps(result, steps):
    """
    Keep backward compatibility with the existing SearchResult dataclass.
    """
    result.steps = steps
    return result

def _candidate_data(nodes, visited):
    """Return unexpanded nodes in the exact queue/stack order."""
    candidates = []
    seen = set()
    for node in nodes:
        if node.node_id in visited or node.node_id in seen:
            continue
        seen.add(node.node_id)
        candidates.append({
            "node_id": node.node_id,
            "g": node.g_cost,
            "h": node.h_cost,
            "f": node.f_cost,
        })
    return candidates

def _record_uninformed_step(
    steps,
    current_node,
    explored_nodes,
    frontier,
    explored_edges,
    candidates,
    next_selected,
    selection_metric,
):
    steps.append({
        "step": len(steps),
        "current": current_node.node_id if current_node else None,
        "exploredNodes": list(explored_nodes),
        "frontierNodes": [node.node_id for node in frontier],
        "exploredEdges": [dict(edge) for edge in explored_edges],
        "pathSoFar": [node.node_id for node in reconstruct_path(current_node)] if current_node else [],
        "metrics": {},
        "candidates": list(candidates),
        "nextSelected": next_selected,
        "selectionMetric": selection_metric,
    })
