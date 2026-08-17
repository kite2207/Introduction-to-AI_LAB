"""
Explainable route generator for the HCM traffic graph.

This module is the single source of truth for the route explanation served
by the FastAPI backend. build_route_explanation() returns JSON-serializable
data that is consumed directly by the frontend (Sidebar.jsx):

    headline, why_selected, optimality, optimality_reference,
    route_comparison, congested_segments, comparison_note

It is deterministic and uses only the graph/route data; no LLM is required.
"""

from __future__ import annotations

from typing import Any

from src.models import CostEvaluator
from src.algorithms import dijkstra_search


HIGH_CONGESTION_LEVEL = 4


def _reference_route(
    graph,
    start_id: str,
    end_id: str,
    optimization: str,
):
    """Return a Dijkstra route with the same objective as an optimality reference."""
    evaluator = CostEvaluator(optimization=optimization)
    ref = dijkstra_search(graph, start_id, end_id, evaluator)

    if not ref.path:
        return None

    return {
        "algorithm": "Dijkstra",
        "optimization": optimization,
        "path": list(ref.path),
        "route_names": [graph.nodes[nid].name for nid in ref.path if nid in graph.nodes],
        "distance": ref.total_distance,
        "time": ref.total_time,
        "cost": ref.total_cost,
    }


def build_route_explanation(
    graph,
    *,
    algo: str,
    algorithm_name: str,
    optimization: str,
    start_id: str,
    end_id: str,
    path: list[str],
    path_names: list[str],
    total_cost: float | None,
    total_distance: float,
    total_time: float,
) -> dict[str, Any]:
    """Build the route-explanation JSON consumed by the frontend."""
    mode = optimization

    # Same-objective Dijkstra = optimality reference.
    optimality_ref = _reference_route(graph, start_id, end_id, mode)

    # Actual alternatives.
    shortest_ref = _reference_route(graph, start_id, end_id, "distance")
    fastest_ref = _reference_route(graph, start_id, end_id, "time")

    def compare(ref):
        if ref is None:
            return None

        return {
            **ref,
            "distance_difference": total_distance - ref["distance"],
            "time_difference": total_time - ref["time"],
            "cost_difference": (None if total_cost is None else total_cost - ref["cost"]),
        }

    criterion = {
        "ucs": "chi phí tích lũy thấp nhất g(n)",
        "dijkstra": "chi phí tích lũy thấp nhất g(n)",
        "astar": "chi phí ước tính thấp nhất f(n) = g(n) + h(n)",
        "greedy": "heuristic thấp nhất h(n)",
        "bfs": "thứ tự mở rộng FIFO",
        "dfs": "thứ tự mở rộng LIFO",
    }.get(algo, "quy tắc tìm kiếm của nó")

    objective = {
        "distance": "khoảng cách tối thiểu",
        "time": "thời gian di chuyển ước tính tối thiểu",
        "mixed": "chi phí hỗn hợp tối thiểu tính theo giao thông",
    }.get(mode, "mục tiêu chi phí đã chọn")

    if algo in {"ucs", "dijkstra"}:
        optimality = f"UCS/Dijkstra đảm bảo tối ưu khi chi phí cạnh không âm theo mục tiêu '{mode}'."
    elif algo == "astar":
        optimality = "A* đảm bảo tối ưu khi heuristic là admissible (và consistent đối với tìm kiếm trên đồ thị)."
    elif algo == "bfs":
        optimality = "BFS đảm bảo tối ưu theo số bước tối thiểu, không nhất thiết theo khoảng cách, thời gian hay chi phí giao thông."
    else:
        optimality = f"{algorithm_name} không đảm bảo tìm được đường tối ưu theo chi phí giao thông '{mode}'."

    congested = []
    for source_id, target_id in zip(path, path[1:]):
        edge = next(
            (e for e in graph.get_neighbors(source_id) if str(e.target_id) == str(target_id)),
            None,
        )

        if edge is None or edge.congestion_level < HIGH_CONGESTION_LEVEL:
            continue

        risk = getattr(edge, "risk_factors", "none")
        if isinstance(risk, list):
            risk = ", ".join(str(v) for v in risk)

        congested.append(
            {
                "from": graph.nodes[source_id].name,
                "to": graph.nodes[target_id].name,
                "congestion": edge.congestion_level,
                "risk": risk,
            }
        )

    same_reference = optimality_ref is not None and total_cost is not None and abs(total_cost - optimality_ref["cost"]) < 1e-9

    return {
        "headline": (f"Tuyến đường được chọn được tối ưu theo {objective}."),
        "why_selected": (f"{algorithm_name} chọn tuyến đường này dựa trên {criterion} theo mục tiêu '{mode}'."),
        "optimality": optimality,
        "optimality_reference": {
            "algorithm": "Dijkstra",
            "optimization": mode,
            "route_names": (optimality_ref["route_names"] if optimality_ref else []),
            "distance": optimality_ref["distance"] if optimality_ref else None,
            "time": optimality_ref["time"] if optimality_ref else None,
            "cost": optimality_ref["cost"] if optimality_ref else None,
            "same_cost_as_selected": same_reference,
        },
        "route_comparison": {
            "selected": {
                "route_names": list(path_names),
                "distance": total_distance,
                "time": total_time,
                "cost": total_cost,
            },
            "shortest_distance": compare(shortest_ref),
            "fastest_time": compare(fastest_ref),
        },
        "congested_segments": congested,
        "optimization": mode,
        "algorithm": algorithm_name,
        "comparison_note": (
            "Dijkstra với cùng mục tiêu được dùng làm tham chiếu tối ưu. Tuyến ngắn nhất và tuyến nhanh nhất là các phương án thay thế thực tế."
        ),
    }
