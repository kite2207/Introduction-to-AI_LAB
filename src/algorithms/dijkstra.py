from src.models import TrafficGraph, CostEvaluator
from src.algorithms.base import SearchResult
from src.algorithms.ucs import ucs_search

def dijkstra_search(
    graph: TrafficGraph,
    start_id: str,
    target_id: str,
    cost_evaluator: CostEvaluator,
) -> SearchResult:
    """
    Dijkstra's Algorithm. Visually and logically similar to UCS.
    Here we implement it explicitly as Dijkstra. It behaves identically to UCS on single target.
    """
    result = ucs_search(graph, start_id, target_id, cost_evaluator)
    result.algorithm_name = "Dijkstra"
    return result
