"""
FastAPI Route Finding API.

Run from the project root:
    python -m uvicorn backend.api:app --reload --port 8000

The graph source is data/hcm_traffic_data.json.
The graph is loaded directly from data/hcm_traffic_data.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models import TrafficGraph, CostEvaluator
from src.algorithms import bfs_search, dfs_search, ucs_search, dijkstra_search, astar_search, greedy_best_first_search
from src.algorithms.multi_location import (
    solve_tsp_dynamic_programming,
    solve_tsp_nearest_neighbor,
)
from backend.schemas import (
    SearchRequest,
    SearchResponse,
    MultiLocationSearchRequest,
    MultiLocationSearchResponse,
    TSPCandidateResponse,
    NodeResponse,
    EdgeResponse,
    GraphInfoResponse,
)
from backend.explanation import build_route_explanation

app = FastAPI(
    title="Route Finding API",
    description="AI-powered route search trên bản đồ TP.HCM",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HCM_DATA_PATH = PROJECT_ROOT / "data" / "hcm_traffic_data.json"
if not HCM_DATA_PATH.exists():
    raise FileNotFoundError(f"Không tìm thấy: {HCM_DATA_PATH}")


def load_hcm_data() -> dict[str, Any]:
    with HCM_DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("hcm_traffic_data.json phải là JSON object")
    return data


hcm_data = load_hcm_data()
graph = TrafficGraph()
graph.load_from_hcm_data(hcm_data)

print(f"[API] HCM graph loaded: {len(graph.nodes)} nodes, {sum(len(v) for v in graph.adjacency_list.values())} edges")


def get_cost_evaluator(optimization: str) -> CostEvaluator:
    return CostEvaluator(optimization=optimization)


def normalize_algorithm(value: str) -> str:
    raw = " ".join(str(value).strip().lower().split())
    aliases = {
        "depth-first search": "dfs",
        "depth first search": "dfs",
        "dfs": "dfs",
        "breadth-first search": "bfs",
        "breadth first search": "bfs",
        "bfs": "bfs",
        "dijkstra's algorithm": "dijkstra",
        "dijkstra algorithm": "dijkstra",
        "dijkstra": "dijkstra",
        "uniform-cost search": "ucs",
        "uniform cost search": "ucs",
        "ucs": "ucs",
        "a* search": "astar",
        "a*": "astar",
        "a-star": "astar",
        "astar": "astar",
        "greedy best-first search": "greedy",
        "greedy best first search": "greedy",
        "greedy": "greedy",
    }
    return aliases.get(raw, raw)


def get_path_metrics(path: list[str]) -> tuple[float, float]:
    """Return physical distance and traffic-adjusted time for a node path."""
    total_distance = 0.0
    total_time = 0.0
    congestion_multipliers = {1: 1.0, 2: 1.3, 3: 1.8, 4: 2.4, 5: 3.5}

    for source_id, target_id in zip(path, path[1:]):
        edge = next(
            (edge for edge in graph.get_neighbors(source_id) if edge.target_id == target_id),
            None,
        )
        if edge is None:
            raise ValueError(f"Missing edge in reconstructed path: {source_id}->{target_id}")

        total_distance += edge.distance
        multiplier = congestion_multipliers.get(max(1, edge.congestion_level), 1.0)
        total_time += edge.estimated_time * multiplier + edge.get_risk_penalty()

    return total_distance, total_time


def make_tsp_candidate(
    algorithm_name: str,
    visiting_order: list[str],
    path: list[str],
    total_cost: float,
    execution_time_ms: float,
) -> TSPCandidateResponse:
    total_distance, total_time = get_path_metrics(path)
    return TSPCandidateResponse(
        algorithm_name=algorithm_name,
        visiting_order=visiting_order,
        visiting_order_names=[graph.nodes[node_id].name for node_id in visiting_order],
        path=path,
        total_cost=total_cost,
        total_distance=total_distance,
        total_time=total_time,
        execution_time_ms=execution_time_ms,
    )


@app.get("/api/nodes", response_model=list[NodeResponse], tags=["Graph"])
def get_nodes():
    return [
        NodeResponse(
            node_id=n.node_id,
            name=n.name,
            lat=n.lat,
            lng=n.lng,
            node_type=n.node_type,
        )
        for n in graph.nodes.values()
    ]


@app.get("/api/edges", response_model=list[EdgeResponse], tags=["Graph"])
def get_edges():
    seen = set()
    result = []
    for edge_list in graph.adjacency_list.values():
        for e in edge_list:
            key = tuple(sorted([e.source_id, e.target_id]))
            if key in seen:
                continue
            seen.add(key)
            result.append(
                EdgeResponse(
                    source_id=e.source_id,
                    target_id=e.target_id,
                    distance=e.distance,
                    estimated_time=e.estimated_time,
                    congestion_level=e.congestion_level,
                    road_type=e.road_type,
                    direction=e.direction,
                    risk_factors=e.risk_factors,
                )
            )
    return result


@app.get("/api/graph/info", response_model=GraphInfoResponse, tags=["Graph"])
def get_graph_info():
    return GraphInfoResponse(
        node_count=len(graph.nodes),
        edge_count=sum(len(v) for v in graph.adjacency_list.values()),
    )


@app.get("/api/graph", tags=["Graph"])
def get_graph():
    """Return the canonical graph representation used by the frontend."""
    nodes = []
    edges = []

    for node_id, node in hcm_data.items():
        nodes.append({
            "id": str(node_id),
            "name": node.get("name") or str(node_id),
            "lat": node["lat"],
            "lng": node["lng"],
            "type": node.get("type") or "intersection",
        })
        for edge in node.get("connected_to", []):
            edges.append({
                "source": str(node_id),
                "target": str(edge["target_node"]),
                "distance": edge["distance"],
                "estimatedTime": edge["estimated_time"],
                "congestion": edge.get("congestion_level", 1),
                "direction": edge.get("direction", "two-way"),
                "risk": edge.get("risk_factors", []),
                "geometry": edge.get("geometry"),
            })

    return {"nodes": nodes, "edges": edges}


@app.post(
    "/api/search/multi",
    response_model=MultiLocationSearchResponse,
    tags=["Search"],
)
def search_multi_location(req: MultiLocationSearchRequest):
    """Compare both TSP solvers and return the lower-cost open route."""
    start_id = str(req.start)
    end_id = str(req.end)
    waypoint_ids = [str(node_id) for node_id in req.waypoints]

    requested_ids = [start_id, *waypoint_ids, end_id]
    missing = [node_id for node_id in requested_ids if node_id not in graph.nodes]
    if missing:
        raise HTTPException(404, f"Node '{missing[0]}' không tồn tại")
    if start_id == end_id:
        raise HTTPException(400, "Start và End phải khác nhau")
    if len(set(requested_ids)) != len(requested_ids):
        raise HTTPException(400, "Start, End và các waypoint không được trùng nhau")

    evaluator = get_cost_evaluator(req.optimization)

    nn_started = time.perf_counter()
    nn_order, nn_path, nn_cost = solve_tsp_nearest_neighbor(
        graph, start_id, waypoint_ids, evaluator, end_id=end_id
    )
    nn_ms = (time.perf_counter() - nn_started) * 1000.0

    dp_started = time.perf_counter()
    dp_order, dp_path, dp_cost = solve_tsp_dynamic_programming(
        graph, start_id, waypoint_ids, evaluator, end_id=end_id
    )
    dp_ms = (time.perf_counter() - dp_started) * 1000.0

    raw_candidates = [
        ("TSP Nearest Neighbor", nn_order, nn_path, nn_cost, nn_ms),
        ("TSP Held-Karp", dp_order, dp_path, dp_cost, dp_ms),
    ]
    if any(not path or cost == float("inf") for _, _, path, cost, _ in raw_candidates):
        raise HTTPException(404, "Không tìm thấy hành trình đi qua tất cả địa điểm")

    candidates = [make_tsp_candidate(*candidate) for candidate in raw_candidates]
    # Held-Karp wins ties because it carries an optimality guarantee.
    selected = min(
        candidates,
        key=lambda candidate: (
            candidate.total_cost,
            0 if candidate.algorithm_name == "TSP Held-Karp" else 1,
        ),
    )

    path_names = [graph.nodes[node_id].name for node_id in selected.path]
    comparison_data = [candidate.model_dump() for candidate in candidates]
    explanation = {
        "headline": "Đã so sánh hai thuật toán TSP và chọn hành trình có tổng chi phí thấp hơn.",
        "why_selected": (
            f"{selected.algorithm_name} được chọn với tổng chi phí "
            f"{selected.total_cost:.2f} theo mục tiêu '{req.optimization}'."
        ),
        "optimality": (
            "Held–Karp xét toàn bộ thứ tự waypoint và cho lời giải tối ưu; "
            "Nearest Neighbor là heuristic chọn điểm gần nhất ở từng bước."
        ),
        "algorithm": selected.algorithm_name,
        "optimization": req.optimization,
        "comparison_note": "Start và End được giữ cố định; chỉ thứ tự waypoint ở giữa được tối ưu.",
        "tsp_comparison": comparison_data,
        "visiting_order_names": selected.visiting_order_names,
        "optimality_reference": None,
        "route_comparison": None,
        "congested_segments": [],
    }

    return MultiLocationSearchResponse(
        algorithm_name=selected.algorithm_name,
        selected_algorithm=selected.algorithm_name,
        visiting_order=selected.visiting_order,
        visiting_order_names=selected.visiting_order_names,
        path=selected.path,
        total_cost=selected.total_cost,
        total_distance=selected.total_distance,
        total_time=selected.total_time,
        execution_time_ms=nn_ms + dp_ms,
        path_node_names=path_names,
        path_coordinates=[
            {"lat": graph.nodes[node_id].lat, "lng": graph.nodes[node_id].lng}
            for node_id in selected.path
        ],
        start_name=graph.nodes[start_id].name,
        end_name=graph.nodes[end_id].name,
        explanation=explanation,
        comparison=candidates,
    )


@app.post("/api/search", response_model=SearchResponse, tags=["Search"])
def search_route(req: SearchRequest):
    start_id = str(req.start)
    end_id = str(req.end)

    if start_id not in graph.nodes:
        raise HTTPException(404, f"Node '{start_id}' không tồn tại")
    if end_id not in graph.nodes:
        raise HTTPException(404, f"Node '{end_id}' không tồn tại")
    if start_id == end_id:
        raise HTTPException(400, "Start và End phải khác nhau")

    evaluator = get_cost_evaluator(req.optimization)
    algo = normalize_algorithm(req.algorithm)

    if algo == "dfs":
        result = dfs_search(graph, start_id, end_id, evaluator)
    elif algo == "bfs":
        result = bfs_search(graph, start_id, end_id, evaluator)
    elif algo == "dijkstra":
        result = dijkstra_search(graph, start_id, end_id, evaluator)
    elif algo == "ucs":
        result = ucs_search(graph, start_id, end_id, evaluator)
    elif algo == "astar":
        result = astar_search(graph, start_id, end_id, evaluator)
    elif algo == "greedy":
        result = greedy_best_first_search(graph, start_id, end_id, evaluator)
    else:
        raise HTTPException(400, f"Thuật toán '{req.algorithm}' không hợp lệ")

    if not result.path:
        raise HTTPException(404, f"Không tìm thấy đường từ {start_id} đến {end_id}")

    path_names = [graph.nodes[nid].name for nid in result.path if nid in graph.nodes]
    path_coords = [{"lat": graph.nodes[nid].lat, "lng": graph.nodes[nid].lng} for nid in result.path if nid in graph.nodes]

    explanation = build_route_explanation(
        graph,
        algo=algo,
        algorithm_name=result.algorithm_name,
        optimization=req.optimization,
        start_id=start_id,
        end_id=end_id,
        path=result.path,
        path_names=path_names,
        total_cost=result.total_cost,
        total_distance=result.total_distance,
        total_time=result.total_time,
    )

    return SearchResponse(
        algorithm_name=result.algorithm_name,
        path=result.path,
        explored_nodes=result.explored_nodes,
        total_cost=result.total_cost,
        total_distance=result.total_distance,
        total_time=result.total_time,
        explored_count=result.explored_count,
        execution_time_ms=result.execution_time_ms,
        path_node_names=path_names,
        path_coordinates=path_coords,
        start_name=graph.nodes[start_id].name,
        end_name=graph.nodes[end_id].name,
        steps=getattr(result, "steps", []),
        explanation=explanation,
    )


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "message": "Route Finding API is running",
        "data_source": "data/hcm_traffic_data.json",
        "node_count": len(graph.nodes),
        "edge_count": sum(len(v) for v in graph.adjacency_list.values()),
    }
