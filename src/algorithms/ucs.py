import time
import heapq
from src.models import TrafficGraph, CostEvaluator
from src.algorithms.base import (
    SearchNode, SearchResult, reconstruct_path,
    _record_step, _attach_steps, _frontier_candidates
)

def ucs_search(
    graph: TrafficGraph,
    start_id: str,
    target_id: str,
    cost_evaluator: CostEvaluator,
) -> SearchResult:
    """Uniform Cost Search: priority = g(n)."""
    start_time = time.perf_counter()
    explored_nodes = []
    explored_edges = []
    steps = []
    explored_set = set()

    if start_id not in graph.nodes or target_id not in graph.nodes:
        result = SearchResult("UCS", [], [], 0.0, 0.0, 0.0, 0, 0.0)
        return _attach_steps(result, steps)

    counter = 0
    start_node = SearchNode(node_id=start_id, g_cost=0.0, f_cost=0.0)
    frontier = [(0.0, counter, start_node)]
    best_costs = {start_id: 0.0}
    final_node = None

    while frontier:
        current_g, _, current_node = heapq.heappop(frontier)
        node_id = current_node.node_id

        if current_g > best_costs.get(node_id, float("inf")):
            continue

        explored_nodes.append(node_id)
        explored_set.add(node_id)

        if node_id == target_id:
            final_node = current_node
            _record_step(
                steps, current_node, explored_nodes, frontier,
                explored_edges, metrics={"g": current_node.g_cost},
                candidates=_frontier_candidates(
                    frontier, explored_set, current_node, best_costs, "g"
                ),
                selection_metric="g",
            )
            break

        for edge in graph.get_neighbors(node_id):
            neighbor_id = edge.target_id
            if neighbor_id in explored_set:
                continue

            edge_cost = cost_evaluator.calculate_cost(edge)
            new_g = current_g + edge_cost

            if new_g < best_costs.get(neighbor_id, float("inf")):
                best_costs[neighbor_id] = new_g
                counter += 1
                neighbor_node = SearchNode(
                    node_id=neighbor_id,
                    parent=current_node,
                    g_cost=new_g,
                    f_cost=new_g,
                    edge_taken=edge,
                )
                heapq.heappush(frontier, (new_g, counter, neighbor_node))
                explored_edges.append({"source": node_id, "target": neighbor_id})

        _record_step(
            steps, current_node, explored_nodes, frontier,
            explored_edges, metrics={"g": current_node.g_cost},
            candidates=_frontier_candidates(
                frontier, explored_set, current_node, best_costs, "g"
            ),
            selection_metric="g",
        )

    exec_time = (time.perf_counter() - start_time) * 1000.0

    if final_node is None:
        result = SearchResult("UCS", [], explored_nodes, 0.0, 0.0, 0.0, len(explored_nodes), exec_time)
        return _attach_steps(result, steps)

    path_nodes = reconstruct_path(final_node)
    path_ids = [node.node_id for node in path_nodes]

    total_dist = sum(node.edge_taken.distance for node in path_nodes if node.edge_taken)
    total_time = sum(
        node.edge_taken.estimated_time * {1:1.0,2:1.3,3:1.8,4:2.4,5:3.5}.get(max(1, node.edge_taken.congestion_level), 1.0)
        + node.edge_taken.get_risk_penalty()
        for node in path_nodes if node.edge_taken
    )

    result = SearchResult(
        algorithm_name="UCS",
        path=path_ids,
        explored_nodes=explored_nodes,
        total_cost=final_node.g_cost,
        total_distance=total_dist,
        total_time=total_time,
        explored_count=len(explored_nodes),
        execution_time_ms=exec_time,
    )
    return _attach_steps(result, steps)
