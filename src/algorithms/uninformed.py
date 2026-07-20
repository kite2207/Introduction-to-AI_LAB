import time
from collections import deque
from typing import List, Set, Dict, Optional
from src.models import TrafficGraph, CostEvaluator
from src.algorithms.base import SearchNode, SearchResult, reconstruct_path

def bfs_search(graph: TrafficGraph, start_id: str, target_id: str, cost_evaluator: CostEvaluator) -> SearchResult:
    """
    Breadth-First Search (BFS) finds the path with the fewest road segments (shortest in terms of hop count).
    """
    start_time = time.perf_counter()
    explored_nodes = []
    
    if start_id not in graph.nodes or target_id not in graph.nodes:
        return SearchResult("BFS", [], [], 0.0, 0.0, 0.0, 0, 0.0)

    # Frontier holds search nodes
    frontier = deque([SearchNode(node_id=start_id)])
    # Visited tracks which node IDs have been added to the frontier
    visited = {start_id}
    
    final_node = None
    
    while frontier:
        current_node = frontier.popleft()
        node_id = current_node.node_id
        explored_nodes.append(node_id)
        
        # Check goal test
        if node_id == target_id:
            final_node = current_node
            break
            
        for edge in graph.get_neighbors(node_id):
            neighbor_id = edge.target_id
            if neighbor_id not in visited:
                visited.add(neighbor_id)
                g_cost = current_node.g_cost + cost_evaluator.calculate_cost(edge)
                frontier.append(SearchNode(
                    node_id=neighbor_id,
                    parent=current_node,
                    g_cost=g_cost,
                    edge_taken=edge
                ))

    end_time = time.perf_counter()
    exec_time = (end_time - start_time) * 1000.0
    
    if final_node is None:
        return SearchResult("BFS", [], explored_nodes, 0.0, 0.0, 0.0, len(explored_nodes), exec_time)
        
    path_nodes = reconstruct_path(final_node)
    path_ids = [n.node_id for n in path_nodes]
    
    # Calculate exact path properties
    total_dist = sum(n.edge_taken.distance for n in path_nodes if n.edge_taken)
    total_time = sum(n.edge_taken.estimated_time * (1.0 + (n.edge_taken.congestion_level - 1) * 0.5) 
                     for n in path_nodes if n.edge_taken)
    total_cost = final_node.g_cost
    
    return SearchResult(
        algorithm_name="BFS",
        path=path_ids,
        explored_nodes=explored_nodes,
        total_cost=total_cost,
        total_distance=total_dist,
        total_time=total_time,
        explored_count=len(explored_nodes),
        execution_time_ms=exec_time
    )

def dfs_search(graph: TrafficGraph, start_id: str, target_id: str, cost_evaluator: CostEvaluator) -> SearchResult:
    """
    Depth-First Search (DFS) explores as deep as possible before backtracking.
    Does not guarantee optimal paths.
    """
    start_time = time.perf_counter()
    explored_nodes = []
    
    if start_id not in graph.nodes or target_id not in graph.nodes:
        return SearchResult("DFS", [], [], 0.0, 0.0, 0.0, 0, 0.0)

    # Frontier acts as a LIFO stack
    frontier = [SearchNode(node_id=start_id)]
    # Visited tracks expanded nodes (DFS marks visited on pop, not on push, to allow finding other paths, 
    # but to prevent infinite loops in cyclic graphs we track visited)
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
            break
            
        # Reverse neighbor expansion order to match standard left-to-right DFS traversal when pushing to stack
        for edge in reversed(graph.get_neighbors(node_id)):
            neighbor_id = edge.target_id
            if neighbor_id not in visited:
                g_cost = current_node.g_cost + cost_evaluator.calculate_cost(edge)
                frontier.append(SearchNode(
                    node_id=neighbor_id,
                    parent=current_node,
                    g_cost=g_cost,
                    edge_taken=edge
                ))

    end_time = time.perf_counter()
    exec_time = (end_time - start_time) * 1000.0
    
    if final_node is None:
        return SearchResult("DFS", [], explored_nodes, 0.0, 0.0, 0.0, len(explored_nodes), exec_time)
        
    path_nodes = reconstruct_path(final_node)
    path_ids = [n.node_id for n in path_nodes]
    
    total_dist = sum(n.edge_taken.distance for n in path_nodes if n.edge_taken)
    total_time = sum(n.edge_taken.estimated_time * (1.0 + (n.edge_taken.congestion_level - 1) * 0.5) 
                     for n in path_nodes if n.edge_taken)
    total_cost = final_node.g_cost
    
    return SearchResult(
        algorithm_name="DFS",
        path=path_ids,
        explored_nodes=explored_nodes,
        total_cost=total_cost,
        total_distance=total_dist,
        total_time=total_time,
        explored_count=len(explored_nodes),
        execution_time_ms=exec_time
    )
