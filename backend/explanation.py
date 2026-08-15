"""
Explainable route generator for hcm_traffic_data.json.

The function generate_explanation() returns JSON-serializable data that can
be returned directly by a FastAPI route. It is deterministic and uses only
the graph/route data; no LLM is required.
"""

from typing import Any, Callable, Dict, Optional, Sequence


HIGH_CONGESTION_LEVEL = 4


def node_name(graph: Dict[str, Any], node_id: str) -> str:
    node = graph.get(str(node_id), {})
    return node.get("name") or str(node_id)


def find_edge(
    graph: Dict[str, Any],
    source: str,
    target: str,
) -> Optional[Dict[str, Any]]:
    source = str(source)
    target = str(target)

    for edge in graph.get(source, {}).get("connected_to", []):
        if str(edge.get("target_node")) == target:
            return edge

    # The dataset may represent a two-way road from the opposite side.
    for edge in graph.get(target, {}).get("connected_to", []):
        if str(edge.get("target_node")) == source:
            return edge

    return None


def edge_cost(
    edge: Dict[str, Any],
    cost_function: Optional[Callable[[Dict[str, Any]], float]] = None,
) -> Optional[float]:
    if cost_function:
        return float(cost_function(edge))

    value = edge.get("cost")
    return float(value) if value is not None else None


def route_details(
    path: Sequence[str],
    graph: Dict[str, Any],
    cost_function=None,
) -> Dict[str, Any]:
    segments = []
    distance = 0.0
    time = 0.0
    cost = 0.0
    has_cost = False
    congestion = []

    for i in range(len(path) - 1):
        source = str(path[i])
        target = str(path[i + 1])
        edge = find_edge(graph, source, target)

        if edge is None:
            segments.append({
                "from": source,
                "from_name": node_name(graph, source),
                "to": target,
                "to_name": node_name(graph, target),
                "found": False,
            })
            continue

        d = edge.get("distance")
        t = edge.get("estimated_time")
        c = edge_cost(edge, cost_function)
        level = edge.get("congestion_level")

        if d is not None:
            distance += float(d)
        if t is not None:
            time += float(t)
        if c is not None:
            cost += c
            has_cost = True

        segment = {
            "from": source,
            "from_name": node_name(graph, source),
            "to": target,
            "to_name": node_name(graph, target),
            "distance": d,
            "estimated_time": t,
            "congestion_level": level,
            "risk_factors": edge.get("risk_factors"),
            "cost": c,
            "found": True,
        }
        segments.append(segment)

        if level is not None and float(level) >= HIGH_CONGESTION_LEVEL:
            congestion.append(segment)

    return {
        "path": [str(x) for x in path],
        "route": [node_name(graph, x) for x in path],
        "segments": segments,
        "metrics": {
            "distance": round(distance, 2),
            "time": round(time, 2),
            "cost": round(cost, 2) if has_cost else None,
        },
        "high_congestion_segments": congestion,
    }


def optimality_info(algorithm: str) -> Dict[str, Any]:
    a = str(algorithm).strip().lower().replace("_", "-")

    if a in {"dfs", "depth-first search", "depth first search"}:
        return {
            "guarantees_optimality": False,
            "statement": "DFS does not guarantee an optimal route.",
        }

    if a in {"bfs", "breadth-first search", "breadth first search"}:
        return {
            "guarantees_optimality": True,
            "condition": "all edges must have equal cost",
            "statement": (
                "BFS is optimal for the minimum number of edges when all "
                "edges have equal cost. It is not generally optimal for "
                "distance or travel time."
            ),
        }

    if a in {"ucs", "uniform-cost search", "uniform cost search", "dijkstra"}:
        return {
            "guarantees_optimality": True,
            "condition": "edge costs must be non-negative",
            "statement": (
                "Uniform-Cost Search guarantees a minimum-cost route when "
                "edge costs are non-negative."
            ),
        }

    if a in {"a*", "a-star", "astar", "a star"}:
        return {
            "guarantees_optimality": True,
            "condition": "the heuristic must be admissible",
            "statement": (
                "A* guarantees an optimal route when its heuristic is "
                "admissible."
            ),
        }

    if "greedy" in a:
        return {
            "guarantees_optimality": False,
            "statement": (
                "Greedy Best-First Search does not guarantee an optimal route."
            ),
        }

    return {
        "guarantees_optimality": None,
        "statement": "Optimality information is not defined for this algorithm.",
    }


def build_reason(
    optimization: str,
    metrics: Dict[str, Any],
    congestion_count: int,
) -> str:
    opt = str(optimization).lower()

    if opt == "distance":
        return (
            f"The route is evaluated by total distance "
            f"({metrics['distance']} distance units)."
        )

    if opt == "time":
        return (
            f"The route is evaluated by estimated travel time "
            f"({metrics['time']} time units)."
        )

    if opt == "cost":
        if metrics["cost"] is not None:
            return (
                f"The route is evaluated by total cost "
                f"({metrics['cost']})."
            )
        return (
            "The route is configured for total-cost optimization, but the "
            "current traffic data does not contain an explicit edge cost."
        )

    if congestion_count:
        return (
            "The route follows the backend's default weighting and contains "
            f"{congestion_count} high-congestion segment(s)."
        )

    return "The route follows the backend's default graph weighting."


def compare_routes(selected: Dict[str, Any], alternative: Dict[str, Any]) -> Dict[str, Any]:
    sm = selected["metrics"]
    am = alternative["metrics"]

    result = {
        "alternative_path": alternative["path"],
        "alternative_route": alternative["route"],
        "distance_difference": None,
        "time_difference": None,
        "cost_difference": None,
        "summary": None,
    }

    if sm["distance"] is not None and am["distance"] is not None:
        result["distance_difference"] = round(am["distance"] - sm["distance"], 2)

    if sm["time"] is not None and am["time"] is not None:
        result["time_difference"] = round(am["time"] - sm["time"], 2)

    if sm["cost"] is not None and am["cost"] is not None:
        result["cost_difference"] = round(am["cost"] - sm["cost"], 2)

    parts = []
    d = result["distance_difference"]
    t = result["time_difference"]

    if d is not None:
        parts.append(
            "the selected route is shorter"
            if d > 0 else
            "the alternative route is shorter"
            if d < 0 else
            "both routes have the same distance"
        )

    if t is not None:
        parts.append(
            "the selected route is faster"
            if t > 0 else
            "the alternative route is faster"
            if t < 0 else
            "both routes have the same estimated time"
        )

    result["summary"] = (
        "Compared with the alternative route, " + "; ".join(parts) + "."
        if parts else
        "There is not enough metric data for a detailed comparison."
    )
    return result


def generate_explanation(
    path: Sequence[str],
    graph: Dict[str, Any],
    optimization: str = "default",
    algorithm: str = "A*",
    alternative_paths: Optional[Sequence[Sequence[str]]] = None,
    cost_function=None,
) -> Dict[str, Any]:
    """
    Generate the explanation required by the project specification.

    alternative_paths is optional. If supplied, each alternative is compared
    with the selected route.
    """
    if not path:
        return {
            "reason": "No route was found.",
            "route": [],
            "metrics": {"distance": None, "time": None, "cost": None},
            "high_congestion_segments": [],
            "comparison": [],
            "optimality": optimality_info(algorithm),
        }

    selected = route_details(path, graph, cost_function)

    result = {
        "reason": build_reason(
            optimization,
            selected["metrics"],
            len(selected["high_congestion_segments"]),
        ),
        "optimization": optimization,
        "algorithm": algorithm,
        "path": selected["path"],
        "route": selected["route"],
        "metrics": selected["metrics"],
        "high_congestion_segments": selected["high_congestion_segments"],
        "segments": selected["segments"],
        "comparison": [],
        "optimality": optimality_info(algorithm),
    }

    for alternative_path in alternative_paths or []:
        if alternative_path:
            alternative = route_details(
                alternative_path,
                graph,
                cost_function,
            )
            result["comparison"].append(
                compare_routes(selected, alternative)
            )

    return result
