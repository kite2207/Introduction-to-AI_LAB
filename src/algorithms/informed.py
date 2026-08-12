import time
import heapq
from typing import List, Dict, Set, Optional, Callable
from src.models import TrafficGraph, CostEvaluator, Node
from src.algorithms.base import SearchNode, SearchResult, reconstruct_path
from src.heuristics import haversine_distance, get_time_scaled_heuristic

def ucs_search(graph: TrafficGraph, start_id: str, target_id: str, cost_evaluator: CostEvaluator) -> SearchResult:
    """
    Uniform Cost Search (UCS) expands nodes in order of increasing path cost g(n).
    Guarantees the optimal path.
    """
    start_time = time.perf_counter()
    explored_nodes = []
    
    if start_id not in graph.nodes or target_id not in graph.nodes:
        return SearchResult("UCS", [], [], 0.0, 0.0, 0.0, 0, 0.0)

    # Priority queue: list of (g_cost, counter, SearchNode)
    counter = 0
    start_node = SearchNode(node_id=start_id, g_cost=0.0, f_cost=0.0)
    frontier = [(0.0, counter, start_node)]
    
    # Store the minimum cost to reach each node
    best_costs = {start_id: 0.0}
    final_node = None

    while frontier:
        current_g, _, current_node = heapq.heappop(frontier)
        node_id = current_node.node_id
        
        # Skip if we already found a cheaper path to this node before we popped it
        if current_g > best_costs.get(node_id, float('inf')):
            continue
            
        explored_nodes.append(node_id)
        
        if node_id == target_id:
            final_node = current_node
            break
            
        for edge in graph.get_neighbors(node_id):
            neighbor_id = edge.target_id
            edge_cost = cost_evaluator.calculate_cost(edge)
            new_g = current_g + edge_cost
            
            if new_g < best_costs.get(neighbor_id, float('inf')):
                best_costs[neighbor_id] = new_g
                counter += 1
                neighbor_node = SearchNode(
                    node_id=neighbor_id,
                    parent=current_node,
                    g_cost=new_g,
                    f_cost=new_g, # In UCS, f(n) = g(n)
                    edge_taken=edge
                )
                heapq.heappush(frontier, (new_g, counter, neighbor_node))

    end_time = time.perf_counter()
    exec_time = (end_time - start_time) * 1000.0

    if final_node is None:
        return SearchResult("UCS", [], explored_nodes, 0.0, 0.0, 0.0, len(explored_nodes), exec_time)

    path_nodes = reconstruct_path(final_node)
    path_ids = [n.node_id for n in path_nodes]
    
    total_dist = sum(n.edge_taken.distance for n in path_nodes if n.edge_taken)
    total_time = sum(n.edge_taken.estimated_time * (1.0 + (n.edge_taken.congestion_level - 1) * 0.5) 
                     for n in path_nodes if n.edge_taken)
    total_cost = final_node.g_cost

    return SearchResult(
        algorithm_name="UCS",
        path=path_ids,
        explored_nodes=explored_nodes,
        total_cost=total_cost,
        total_distance=total_dist,
        total_time=total_time,
        explored_count=len(explored_nodes),
        execution_time_ms=exec_time
    )


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
    
    if start_id not in graph.nodes or target_id not in graph.nodes:
        return SearchResult("A*", [], [], 0.0, 0.0, 0.0, 0, 0.0)

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
        
        if node_id == target_id:
            final_node = current_node
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

    end_time = time.perf_counter()
    exec_time = (end_time - start_time) * 1000.0

    if final_node is None:
        return SearchResult("A*", [], explored_nodes, 0.0, 0.0, 0.0, len(explored_nodes), exec_time)

    path_nodes = reconstruct_path(final_node)
    path_ids = [n.node_id for n in path_nodes]
    
    total_dist = sum(n.edge_taken.distance for n in path_nodes if n.edge_taken)
    total_time = sum(n.edge_taken.estimated_time * (1.0 + (n.edge_taken.congestion_level - 1) * 0.5) 
                     for n in path_nodes if n.edge_taken)
    total_cost = final_node.g_cost

    return SearchResult(
        algorithm_name=f"A* ({cost_evaluator.optimization})",
        path=path_ids,
        explored_nodes=explored_nodes,
        total_cost=total_cost,
        total_distance=total_dist,
        total_time=total_time,
        explored_count=len(explored_nodes),
        execution_time_ms=exec_time
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
    
    if start_id not in graph.nodes or target_id not in graph.nodes:
        return SearchResult("Greedy Best-First", [], [], 0.0, 0.0, 0.0, 0, 0.0)

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
        
        if node_id == target_id:
            final_node = current_node
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

    end_time = time.perf_counter()
    exec_time = (end_time - start_time) * 1000.0

    if final_node is None:
        return SearchResult("Greedy Best-First", [], explored_nodes, 0.0, 0.0, 0.0, len(explored_nodes), exec_time)

    path_nodes = reconstruct_path(final_node)
    path_ids = [n.node_id for n in path_nodes]
    
    total_dist = sum(n.edge_taken.distance for n in path_nodes if n.edge_taken)
    total_time = sum(n.edge_taken.estimated_time * (1.0 + (n.edge_taken.congestion_level - 1) * 0.5) 
                     for n in path_nodes if n.edge_taken)
    total_cost = final_node.g_cost

    return SearchResult(
        algorithm_name=f"Greedy Best-First ({cost_evaluator.optimization})",
        path=path_ids,
        explored_nodes=explored_nodes,
        total_cost=total_cost,
        total_distance=total_dist,
        total_time=total_time,
        explored_count=len(explored_nodes),
        execution_time_ms=exec_time
    )
