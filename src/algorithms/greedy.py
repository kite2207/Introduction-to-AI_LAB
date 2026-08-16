import time
import heapq
from src.models import TrafficGraph, CostEvaluator
from src.algorithms.base import (
    SearchNode, SearchResult, reconstruct_path,
    _record_step, _attach_steps, _frontier_candidates,
    haversine_distance
)

def greedy_best_first_search(
    graph: TrafficGraph, 
    start_id: str, 
    target_id: str, 
    cost_evaluator: CostEvaluator
) -> SearchResult:
    """
    Greedy Best-First Search expands nodes based solely on the heuristic estimate h(n).
    Does not guarantee optimal paths but is typically very fast and explores fewer nodes.
    """
    start_time = time.perf_counter()
    explored_nodes = []
    explored_edges = []
    steps = []
    explored_set = set()

    if start_id not in graph.nodes or target_id not in graph.nodes:
        return _attach_steps(
            SearchResult("Greedy Best-First", [], [], 0.0, 0.0, 0.0, 0, 0.0),
            steps,
        )

    target_node = graph.nodes[target_id]

    def _heuristic(node_id: str) -> float:
        dist = haversine_distance(graph.nodes[node_id], target_node)
        if cost_evaluator.optimization == "distance":
            return dist
        elif cost_evaluator.optimization == "time":
            return dist / 16.67
        else:  # "mixed"
            return (dist + (dist / 16.67) * 10.0) / 2.0

    counter = 0
    start_h = _heuristic(start_id)
    start_node = SearchNode(node_id=start_id, g_cost=0.0, h_cost=start_h, f_cost=start_h)
    frontier = [(start_h, counter, start_node)]
    
    visited = {start_id}
    final_node = None

    while frontier:
        _, _, current_node = heapq.heappop(frontier)
        node_id = current_node.node_id
        
        explored_nodes.append(node_id)
        explored_set.add(node_id)
        
        if node_id == target_id:
            final_node = current_node
            _record_step(
                steps, current_node, explored_nodes, frontier, explored_edges,
                metrics={"h": current_node.h_cost},
                candidates=_frontier_candidates(frontier, explored_set, current_node, {}, "h"),
                selection_metric="h",
            )
            break
            
        for edge in graph.get_neighbors(node_id):
            neighbor_id = edge.target_id
            if neighbor_id not in visited:
                visited.add(neighbor_id)
                edge_cost = cost_evaluator.calculate_cost(edge)
                new_g = current_node.g_cost + edge_cost
                h_val = _heuristic(neighbor_id)
                
                counter += 1
                neighbor_node = SearchNode(
                    node_id=neighbor_id,
                    parent=current_node,
                    g_cost=new_g,
                    h_cost=h_val,
                    f_cost=h_val, # In Greedy, f(n) = h(n)
                    edge_taken=edge
                )
                heapq.heappush(frontier, (h_val, counter, neighbor_node))
                explored_edges.append({"source": node_id, "target": neighbor_id})

        _record_step(
            steps, current_node, explored_nodes, frontier, explored_edges,
            metrics={"h": current_node.h_cost},
            candidates=_frontier_candidates(frontier, explored_set, current_node, {}, "h"),
            selection_metric="h",
        )

    exec_time = (time.perf_counter() - start_time) * 1000.0

    if final_node is None:
        return _attach_steps(
            SearchResult("Greedy Best-First", [], explored_nodes, 0.0, 0.0, 0.0, len(explored_nodes), exec_time),
            steps,
        )

    path_nodes = reconstruct_path(final_node)
    path_ids = [n.node_id for n in path_nodes]
    
    total_dist = sum(n.edge_taken.distance for n in path_nodes if n.edge_taken)
    total_time = sum(
        n.edge_taken.estimated_time * {1:1.0,2:1.3,3:1.8,4:2.4,5:3.5}.get(max(1, n.edge_taken.congestion_level), 1.0)
        + n.edge_taken.get_risk_penalty()
        for n in path_nodes if n.edge_taken
    )
    total_cost = final_node.g_cost

    return _attach_steps(
        SearchResult(
            algorithm_name=f"Greedy Best-First ({cost_evaluator.optimization})",
            path=path_ids,
            explored_nodes=explored_nodes,
            total_cost=total_cost,
            total_distance=total_dist,
            total_time=total_time,
            explored_count=len(explored_nodes),
            execution_time_ms=exec_time,
        ),
        steps,
    )
