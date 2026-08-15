import time
from collections import deque
from src.models import TrafficGraph, CostEvaluator
from src.algorithms.base import SearchNode, SearchResult, reconstruct_path


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
        "current": (
            current_node.node_id
            if current_node else None
        ),
        "exploredNodes": list(explored_nodes),
        "frontierNodes": [
            node.node_id for node in frontier
        ],
        "exploredEdges": [
            dict(edge) for edge in explored_edges
        ],
        "pathSoFar": (
            [
                node.node_id
                for node in reconstruct_path(current_node)
            ]
            if current_node else []
        ),
        "metrics": {},
        "candidates": list(candidates),
        "nextSelected": next_selected,
        "selectionMetric": selection_metric,
    })


def bfs_search(
    graph: TrafficGraph,
    start_id: str,
    target_id: str,
    cost_evaluator: CostEvaluator,
) -> SearchResult:
    """
    Breadth-First Search.
    Next node is determined by FIFO queue order, not by g/h/f.
    """

    start_time = time.perf_counter()
    explored_nodes = []
    explored_edges = []
    steps = []

    if (
        start_id not in graph.nodes
        or target_id not in graph.nodes
    ):
        result = SearchResult(
            "BFS", [], [], 0.0, 0.0, 0.0, 0, 0.0
        )
        result.steps = steps
        return result

    frontier = deque([
        SearchNode(node_id=start_id)
    ])

    discovered = {start_id}
    final_node = None

    while frontier:
        current_node = frontier.popleft()
        node_id = current_node.node_id
        explored_nodes.append(node_id)

        if node_id == target_id:
            final_node = current_node

            candidates = _candidate_data(
                list(frontier),
                discovered,
            )

            _record_uninformed_step(
                steps,
                current_node,
                explored_nodes,
                list(frontier),
                explored_edges,
                candidates,
                frontier[0].node_id
                if frontier else None,
                "fifo",
            )
            break

        for edge in graph.get_neighbors(node_id):
            neighbor_id = edge.target_id

            # Directed graph: only the actual edge direction is allowed.
            if neighbor_id in discovered:
                continue

            discovered.add(neighbor_id)

            child = SearchNode(
                node_id=neighbor_id,
                parent=current_node,
                g_cost=(
                    current_node.g_cost
                    + cost_evaluator.calculate_cost(edge)
                ),
                edge_taken=edge,
            )

            frontier.append(child)

            explored_edges.append({
                "source": node_id,
                "target": neighbor_id,
            })

        candidates = _candidate_data(
            list(frontier),
            discovered,
        )

        _record_uninformed_step(
            steps,
            current_node,
            explored_nodes,
            list(frontier),
            explored_edges,
            candidates,
            frontier[0].node_id
            if frontier else None,
            "fifo",
        )

    exec_time = (
        time.perf_counter() - start_time
    ) * 1000.0

    if final_node is None:
        result = SearchResult(
            "BFS",
            [],
            explored_nodes,
            0.0,
            0.0,
            0.0,
            len(explored_nodes),
            exec_time,
        )
        result.steps = steps
        return result

    path_nodes = reconstruct_path(final_node)
    path_ids = [
        node.node_id for node in path_nodes
    ]

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
        algorithm_name="BFS",
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

    if (
        start_id not in graph.nodes
        or target_id not in graph.nodes
    ):
        result = SearchResult(
            "DFS", [], [], 0.0, 0.0, 0.0, 0, 0.0
        )
        result.steps = steps
        return result

    frontier = [
        SearchNode(node_id=start_id)
    ]
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

            candidates = _candidate_data(
                list(reversed(frontier)),
                visited,
            )

            _record_uninformed_step(
                steps,
                current_node,
                explored_nodes,
                list(frontier),
                explored_edges,
                candidates,
                frontier[-1].node_id
                if frontier else None,
                "lifo",
            )
            break

        for edge in reversed(
            graph.get_neighbors(node_id)
        ):
            neighbor_id = edge.target_id

            if neighbor_id in visited:
                continue

            child = SearchNode(
                node_id=neighbor_id,
                parent=current_node,
                g_cost=(
                    current_node.g_cost
                    + cost_evaluator.calculate_cost(edge)
                ),
                edge_taken=edge,
            )

            frontier.append(child)

            explored_edges.append({
                "source": node_id,
                "target": neighbor_id,
            })

        candidates = _candidate_data(
            list(reversed(frontier)),
            visited,
        )

        _record_uninformed_step(
            steps,
            current_node,
            explored_nodes,
            list(frontier),
            explored_edges,
            candidates,
            frontier[-1].node_id
            if frontier else None,
            "lifo",
        )

    exec_time = (
        time.perf_counter() - start_time
    ) * 1000.0

    if final_node is None:
        result = SearchResult(
            "DFS",
            [],
            explored_nodes,
            0.0,
            0.0,
            0.0,
            len(explored_nodes),
            exec_time,
        )
        result.steps = steps
        return result

    path_nodes = reconstruct_path(final_node)
    path_ids = [
        node.node_id for node in path_nodes
    ]

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
