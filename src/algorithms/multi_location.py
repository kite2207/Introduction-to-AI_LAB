import time
from typing import List, Dict, Tuple, Set, Optional
from src.models import TrafficGraph, CostEvaluator
from src.algorithms.informed import astar_search

def compute_distance_matrix(
    graph: TrafficGraph,
    locations: List[str],
    cost_evaluator: CostEvaluator
) -> Tuple[Dict[Tuple[str, str], float], Dict[Tuple[str, str], List[str]]]:
    """
    Computes pairwise shortest path costs and paths between all locations in the list.
    Returns:
      - cost_matrix: Dictionary mapping (loc_a, loc_b) -> optimal cost.
      - path_matrix: Dictionary mapping (loc_a, loc_b) -> list of node IDs.
    """
    cost_matrix = {}
    path_matrix = {}
    
    n = len(locations)
    for i in range(n):
        for j in range(n):
            if i == j:
                cost_matrix[(locations[i], locations[j])] = 0.0
                path_matrix[(locations[i], locations[j])] = [locations[i]]
                continue
                
            loc_a = locations[i]
            loc_b = locations[j]
            
            # Use A* to find the optimal path under the current cost evaluator
            res = astar_search(graph, loc_a, loc_b, cost_evaluator, heuristic_type="time")
            
            if res.path:
                cost_matrix[(loc_a, loc_b)] = res.total_cost
                path_matrix[(loc_a, loc_b)] = res.path
            else:
                cost_matrix[(loc_a, loc_b)] = float('inf')
                path_matrix[(loc_a, loc_b)] = []
                
    return cost_matrix, path_matrix


def solve_tsp_nearest_neighbor(
    graph: TrafficGraph,
    start_id: str,
    visit_ids: List[str],
    cost_evaluator: CostEvaluator
) -> Tuple[List[str], List[str], float]:
    """
    Solves the TSP using the Nearest Neighbor heuristic.
    Visits all target locations starting and returning to start_id.
    Returns:
      - visiting_order: Order of the target locations visited (including start and end).
      - full_path: Concat of all road segment node IDs.
      - total_cost: Combined path cost.
    """
    start_time = time.perf_counter()
    all_locations = [start_id] + list(visit_ids)
    
    # Compute the pairwise distance (cost) matrix
    cost_matrix, path_matrix = compute_distance_matrix(graph, all_locations, cost_evaluator)
    
    visiting_order = [start_id]
    unvisited = set(visit_ids)
    current = start_id
    
    while unvisited:
        # Find nearest unvisited neighbor
        next_node = None
        min_cost = float('inf')
        
        for neighbor in unvisited:
            cost = cost_matrix.get((current, neighbor), float('inf'))
            if cost < min_cost:
                min_cost = cost
                next_node = neighbor
                
        if next_node is None:
            # Graph is disconnected, cannot visit all nodes
            break
            
        unvisited.remove(next_node)
        visiting_order.append(next_node)
        current = next_node
        
    # Return to start node to complete the loop
    visiting_order.append(start_id)
    
    # Reconstruct the full path
    full_path = []
    total_cost = 0.0
    
    for i in range(len(visiting_order) - 1):
        segment_path = path_matrix.get((visiting_order[i], visiting_order[i+1]), [])
        if not segment_path:
            return [], [], float('inf')
        
        total_cost += cost_matrix[(visiting_order[i], visiting_order[i+1])]
        # To avoid duplicating intermediate nodes (end of one segment is start of next)
        if i == 0:
            full_path.extend(segment_path)
        else:
            full_path.extend(segment_path[1:])
            
    return visiting_order, full_path, total_cost


def solve_tsp_dynamic_programming(
    graph: TrafficGraph,
    start_id: str,
    visit_ids: List[str],
    cost_evaluator: CostEvaluator
) -> Tuple[List[str], List[str], float]:
    """
    Solves the TSP optimally using Dynamic Programming (Held-Karp algorithm).
    Time complexity: O(N^2 * 2^N) where N is the number of locations.
    Suitable for N <= 15.
    Returns:
      - visiting_order: Optimal order of the target locations visited (including start/end).
      - full_path: Concat of all road segment node IDs.
      - total_cost: Optimal combined path cost.
    """
    all_locations = [start_id] + list(visit_ids)
    n = len(all_locations)
    
    # Map node ID to index
    id_to_idx = {loc: i for i, loc in enumerate(all_locations)}
    idx_to_id = {i: loc for i, loc in enumerate(all_locations)}
    
    cost_matrix, path_matrix = compute_distance_matrix(graph, all_locations, cost_evaluator)
    
    # Convert cost matrix to index-based 2D array
    dist = [[float('inf')] * n for _ in range(n)]
    for (loc_a, loc_b), cost in cost_matrix.items():
        dist[id_to_idx[loc_a]][id_to_idx[loc_b]] = cost
        
    # DP table: memo[(mask, current_node_idx)] -> (min_cost, parent_node_idx)
    # mask: bitmask representing the set of visited nodes (from index 1 to n-1)
    # Start node is index 0
    memo = {}

    def tsp(mask: int, u: int) -> Tuple[float, int]:
        # If all nodes are visited (mask has all 1s except position 0)
        # We need to return to start node (index 0)
        if mask == (1 << n) - 1:
            return dist[u][0], 0
            
        state = (mask, u)
        if state in memo:
            return memo[state]
            
        min_val = float('inf')
        best_next = -1
        
        for v in range(1, n):
            # If node v is not yet visited
            if not (mask & (1 << v)):
                cost_to_v = dist[u][v]
                if cost_to_v < float('inf'):
                    cost, _ = tsp(mask | (1 << v), v)
                    total = cost_to_v + cost
                    if total < min_val:
                        min_val = total
                        best_next = v
                        
        memo[state] = (min_val, best_next)
        return min_val, best_next

    # Solve starting from start node (index 0), mask has only node 0 visited (bit 0 set)
    opt_cost, next_node = tsp(1, 0)
    
    if opt_cost == float('inf'):
        # No TSP tour possible
        return [], [], float('inf')
        
    # Reconstruct the visiting order
    visiting_order = [start_id]
    mask = 1
    current = 0
    
    while True:
        if mask == (1 << n) - 1:
            visiting_order.append(start_id)
            break
        cost, parent = memo[(mask, current)]
        visiting_order.append(idx_to_id[parent])
        mask |= (1 << parent)
        current = parent
        
    # Reconstruct the full path
    full_path = []
    total_cost = 0.0
    
    for i in range(len(visiting_order) - 1):
        segment_path = path_matrix.get((visiting_order[i], visiting_order[i+1]), [])
        total_cost += cost_matrix[(visiting_order[i], visiting_order[i+1])]
        
        if i == 0:
            full_path.extend(segment_path)
        else:
            full_path.extend(segment_path[1:])
            
    return visiting_order, full_path, total_cost
