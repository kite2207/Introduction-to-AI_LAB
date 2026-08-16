import time
from src.models import TrafficGraph, CostEvaluator
from src.algorithms.base import (
    SearchNode, SearchResult, reconstruct_path,
    _candidate_data, _record_uninformed_step
)

def dfs_search(
    graph: TrafficGraph,
    start_id: str,
    target_id: str,
    cost_evaluator: CostEvaluator,
) -> SearchResult:
    """
    Depth-First Search.
    Next node is determined by LIFO stack order, not by g/h/f.
    """
    start_time = time.perf_counter()
    explored_nodes = []
    explored_edges = []
    steps = []

    if start_id not in graph.nodes or target_id not in graph.nodes:
        result = SearchResult("DFS", [], [], 0.0, 0.0, 0.0, 0, 0.0)
        result.steps = steps
        return result

    frontier = [SearchNode(node_id=start_id)]
    visited = set()
    final_node = None

    while frontier:
        current_node = frontier.pop()
        node_id = current_node.node_id

        if node_id in visited:
            continue

        visited.add(node_id)
        explored_nodes.append(node_id)

        if node_id == target_id:
            final_node = current_node
            candidates = _candidate_data(list(reversed(frontier)), visited)
            _record_uninformed_step(
                steps, current_node, explored_nodes, list(frontier),
                explored_edges, candidates,
                frontier[-1].node_id if frontier else None,
                "lifo",
            )
            break

        for edge in reversed(graph.get_neighbors(node_id)):
            neighbor_id = edge.target_id
            if neighbor_id in visited:
                continue

            child = SearchNode(
                node_id=neighbor_id,
                parent=current_node,
                g_cost=current_node.g_cost + cost_evaluator.calculate_cost(edge),
                edge_taken=edge,
            )
            frontier.append(child)
            explored_edges.append({"source": node_id, "target": neighbor_id})

        candidates = _candidate_data(list(reversed(frontier)), visited)
        _record_uninformed_step(
            steps, current_node, explored_nodes, list(frontier),
            explored_edges, candidates,
            frontier[-1].node_id if frontier else None,
            "lifo",
        )

    exec_time = (time.perf_counter() - start_time) * 1000.0

    if final_node is None:
        result = SearchResult("DFS", [], explored_nodes, 0.0, 0.0, 0.0, len(explored_nodes), exec_time)
        result.steps = steps
        return result

    path_nodes = reconstruct_path(final_node)
    path_ids = [node.node_id for node in path_nodes]

    total_dist = sum(node.edge_taken.distance for node in path_nodes if node.edge_taken)
    total_time = sum(
        node.edge_taken.estimated_time * {1:1.0,2:1.3,3:1.8,4:2.4,5:3.5}.get(max(1, node.edge_taken.congestion_level), 1.0)
        + node.edge_taken.get_risk_penalty()
        for node in path_nodes if node.edge_taken
    )

    result = SearchResult(
        algorithm_name="DFS",
        path=path_ids,
        explored_nodes=explored_nodes,
        total_cost=final_node.g_cost,
        total_distance=total_dist,
        total_time=total_time,
        explored_count=len(explored_nodes),
        execution_time_ms=exec_time,
    )
    result.steps = steps
    return result
