import time
import heapq
from typing import List, Dict, Set, Optional, Callable
from src.models import TrafficGraph, CostEvaluator, Node
from src.algorithms.base import SearchNode, SearchResult, reconstruct_path
from src.heuristics import haversine_distance, get_time_scaled_heuristic


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

    return [
        node.node_id
        for node in reconstruct_path(search_node)
    ]



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

        if (
            previous is None
            or candidate["g"] < previous["g"]
        ):
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
        key = {
            "g": "g",
            "f": "f",
            "h": "h",
        }[selection_metric]

        candidates.sort(
            key=lambda x: (
                x.get(key, float("inf")),
                str(x.get("node_id")),
            )
        )

    steps.append({
        "step": len(steps),
        "current": (
            current_node.node_id
            if current_node
            else None
        ),
        "exploredNodes": list(explored_nodes),
        "frontierNodes": _frontier_snapshot(frontier),
        "exploredEdges": [
            dict(edge)
            for edge in explored_edges
        ],
        "pathSoFar": _path_ids(current_node),
        "metrics": dict(metrics or {}),
        "candidates": candidates,
        "nextSelected": _next_frontier_candidate(
            candidates
        ),
        "selectionMetric": selection_metric,
    })


def _attach_steps(result, steps):
    """
    Keep backward compatibility with the existing SearchResult dataclass.

    SearchResult currently does not declare a `steps` field, so attach it
    dynamically instead of changing the constructor used throughout the
    project. The API layer can read `result.steps`.
    """
    result.steps = steps
    return result


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
        result = SearchResult(
            "UCS", [], [], 0.0, 0.0, 0.0, 0, 0.0
        )
        return _attach_steps(result, steps)

    counter = 0
    start_node = SearchNode(
        node_id=start_id,
        g_cost=0.0,
        f_cost=0.0,
    )
    frontier = [(0.0, counter, start_node)]
    best_costs = {start_id: 0.0}
    final_node = None

    while frontier:
        current_g, _, current_node = heapq.heappop(frontier)
        node_id = current_node.node_id

        if current_g > best_costs.get(
            node_id,
            float("inf"),
        ):
            continue

        explored_nodes.append(node_id)
        explored_set.add(node_id)

        if node_id == target_id:
            final_node = current_node
            _record_step(
                steps,
                current_node,
                explored_nodes,
                frontier,
                explored_edges,
                metrics={"g": current_node.g_cost},
                candidates=_frontier_candidates(
                    frontier,
                    explored_set,
                    current_node,
                    best_costs,
                    selection_metric="g",
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

            if new_g < best_costs.get(
                neighbor_id,
                float("inf"),
            ):
                best_costs[neighbor_id] = new_g
                counter += 1

                neighbor_node = SearchNode(
                    node_id=neighbor_id,
                    parent=current_node,
                    g_cost=new_g,
                    f_cost=new_g,
                    edge_taken=edge,
                )

                heapq.heappush(
                    frontier,
                    (new_g, counter, neighbor_node),
                )

                explored_edges.append({
                    "source": node_id,
                    "target": neighbor_id,
                })

        _record_step(
            steps,
            current_node,
            explored_nodes,
            frontier,
            explored_edges,
            metrics={"g": current_node.g_cost},
            candidates=_frontier_candidates(
                frontier,
                explored_set,
                current_node,
                best_costs,
                selection_metric="g",
            ),
            selection_metric="g",
        )

    exec_time = (
        time.perf_counter() - start_time
    ) * 1000.0

    if final_node is None:
        result = SearchResult(
            "UCS",
            [],
            explored_nodes,
            0.0,
            0.0,
            0.0,
            len(explored_nodes),
            exec_time,
        )
        return _attach_steps(result, steps)

    path_nodes = reconstruct_path(final_node)
    path_ids = [node.node_id for node in path_nodes]

    total_dist = sum(
        node.edge_taken.distance
        for node in path_nodes
        if node.edge_taken
    )

    total_time = sum(
        node.edge_taken.estimated_time
        * (
            1.0
            + (node.edge_taken.congestion_level - 1)
            * 0.5
        )
        for node in path_nodes
        if node.edge_taken
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



def dijkstra_search(graph: TrafficGraph, start_id: str, target_id: str, cost_evaluator: CostEvaluator) -> SearchResult:
    """
    Dijkstra's Algorithm. Visually and logically similar to UCS.
    Here we implement it explicitly as Dijkstra. It behaves identically to UCS on single target 
    but we keep it separate to satisfy the requirement of "implementing at least two more algorithms".
    """
    result = ucs_search(graph, start_id, target_id, cost_evaluator)
    result.algorithm_name = "Dijkstra"
    return result


def astar_search(
    graph: TrafficGraph, 
    start_id: str, 
    target_id: str, 
    cost_evaluator: CostEvaluator
) -> SearchResult:
    """
    A* Search uses f(n) = g(n) + h(n) to find the optimal path.
    """
    start_time = time.perf_counter()
    explored_nodes = []
    explored_edges = []
    steps = []
    explored_set = set()

    if start_id not in graph.nodes or target_id not in graph.nodes:
        return _attach_steps(
            SearchResult("A*", [], [], 0.0, 0.0, 0.0, 0, 0.0),
            steps,
        )

    target_node = graph.nodes[target_id]

    def get_heuristic(node_id: str) -> float:
        node = graph.nodes[node_id]
        dist = haversine_distance(node, target_node)
        
        # Để đảm bảo heuristic là admissible (h(n) <= true_cost(n)),
        # ta ước lượng chi phí tối thiểu để đi đến đích.
        if cost_evaluator.optimization == "distance":
            # distance_multiplier tối thiểu là 1.0 (khi congestion = 1)
            # do đó true_distance_cost >= dist
            return dist
            
        elif cost_evaluator.optimization == "time":
            # Thời gian nhỏ nhất là đi bằng đường chim bay với vận tốc tối đa (16.67 m/s)
            min_time = dist / 16.67
            return min_time
            
        else: # "mixed"
            # Kết hợp cả hai với trọng số tương đương trong calculate_cost
            min_time = dist / 16.67
            return dist + (min_time * 10.0)

    # Initialize priority queue
    counter = 0
    start_h = get_heuristic(start_id)
    start_node = SearchNode(node_id=start_id, g_cost=0.0, h_cost=start_h, f_cost=start_h)
    frontier = [(start_node.f_cost, counter, start_node)]
    
    best_costs = {start_id: 0.0}
    final_node = None

    while frontier:
        current_f, _, current_node = heapq.heappop(frontier)
        node_id = current_node.node_id
        
        # If this is not the best cost path to node, skip
        if current_node.g_cost > best_costs.get(node_id, float('inf')):
            continue
            
        explored_nodes.append(node_id)
        explored_set.add(node_id)
        
        if node_id == target_id:
            final_node = current_node
            _record_step(
                steps,
                current_node,
                explored_nodes,
                frontier,
                explored_edges,
                metrics={
                    "g": current_node.g_cost,
                    "h": current_node.h_cost,
                    "f": current_node.f_cost,
                },
                candidates=_frontier_candidates(
                    frontier,
                    explored_set,
                    current_node,
                    best_costs,
                    selection_metric="f",
                ),
                selection_metric="f",
            )
            break
            
        for edge in graph.get_neighbors(node_id):
            neighbor_id = edge.target_id
            edge_cost = cost_evaluator.calculate_cost(edge)
            new_g = current_node.g_cost + edge_cost
            
            if new_g < best_costs.get(neighbor_id, float('inf')):
                best_costs[neighbor_id] = new_g
                h_val = get_heuristic(neighbor_id)
                new_f = new_g + h_val
                
                counter += 1
                neighbor_node = SearchNode(
                    node_id=neighbor_id,
                    parent=current_node,
                    g_cost=new_g,
                    h_cost=h_val,
                    f_cost=new_f,
                    edge_taken=edge
                )
                heapq.heappush(frontier, (new_f, counter, neighbor_node))
                explored_edges.append({
                    "source": node_id,
                    "target": neighbor_id,
                })

        _record_step(
            steps,
            current_node,
            explored_nodes,
            frontier,
            explored_edges,
            metrics={
                "g": current_node.g_cost,
                "h": current_node.h_cost,
                "f": current_node.f_cost,
            },
            candidates=_frontier_candidates(
                frontier,
                explored_set,
                current_node,
                best_costs,
                selection_metric="f",
            ),
            selection_metric="f",
        )

    end_time = time.perf_counter()
    exec_time = (end_time - start_time) * 1000.0

    if final_node is None:
        return _attach_steps(
            SearchResult(
                "A*",
                [],
                explored_nodes,
                0.0,
                0.0,
                0.0,
                len(explored_nodes),
                exec_time,
            ),
            steps,
        )

    path_nodes = reconstruct_path(final_node)
    path_ids = [n.node_id for n in path_nodes]
    
    total_dist = sum(n.edge_taken.distance for n in path_nodes if n.edge_taken)
    total_time = sum(n.edge_taken.estimated_time * (1.0 + (n.edge_taken.congestion_level - 1) * 0.5) 
                     for n in path_nodes if n.edge_taken)
    total_cost = final_node.g_cost

    return _attach_steps(
        SearchResult(
            algorithm_name=f"A* ({cost_evaluator.optimization})",
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
            SearchResult(
                "Greedy Best-First",
                [],
                [],
                0.0,
                0.0,
                0.0,
                0,
                0.0,
            ),
            steps,
        )

    target_node = graph.nodes[target_id]

    def get_heuristic(node_id: str) -> float:
        node = graph.nodes[node_id]
        dist = haversine_distance(node, target_node)
        if cost_evaluator.optimization == "distance":
            return dist
        elif cost_evaluator.optimization == "time":
            return dist / 16.67
        else:
            return dist + (dist / 16.67) * 10.0

    counter = 0
    start_h = get_heuristic(start_id)
    start_node = SearchNode(node_id=start_id, g_cost=0.0, h_cost=start_h, f_cost=start_h)
    frontier = [(start_h, counter, start_node)]
    
    # Store visited to prevent repeating nodes
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
                steps,
                current_node,
                explored_nodes,
                frontier,
                explored_edges,
                metrics={
                    "h": current_node.h_cost,
                },
                candidates=_frontier_candidates(
                    frontier,
                    explored_set,
                    current_node,
                    {},
                    selection_metric="h",
                ),
                selection_metric="h",
            )
            break
            
        for edge in graph.get_neighbors(node_id):
            neighbor_id = edge.target_id
            if neighbor_id not in visited:
                visited.add(neighbor_id)
                edge_cost = cost_evaluator.calculate_cost(edge)
                new_g = current_node.g_cost + edge_cost
                h_val = get_heuristic(neighbor_id)
                
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
                explored_edges.append({
                    "source": node_id,
                    "target": neighbor_id,
                })

        _record_step(
            steps,
            current_node,
            explored_nodes,
            frontier,
            explored_edges,
            metrics={
                "h": current_node.h_cost,
            },
            candidates=_frontier_candidates(
                frontier,
                explored_set,
                current_node,
                {},
                selection_metric="h",
            ),
            selection_metric="h",
        )

    end_time = time.perf_counter()
    exec_time = (end_time - start_time) * 1000.0

    if final_node is None:
        return _attach_steps(
            SearchResult(
                "Greedy Best-First",
                [],
                explored_nodes,
                0.0,
                0.0,
                0.0,
                len(explored_nodes),
                exec_time,
            ),
            steps,
        )

    path_nodes = reconstruct_path(final_node)
    path_ids = [n.node_id for n in path_nodes]
    
    total_dist = sum(n.edge_taken.distance for n in path_nodes if n.edge_taken)
    total_time = sum(n.edge_taken.estimated_time * (1.0 + (n.edge_taken.congestion_level - 1) * 0.5) 
                     for n in path_nodes if n.edge_taken)
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
