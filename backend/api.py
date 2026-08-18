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
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models import TrafficGraph, CostEvaluator
from src.algorithms import bfs_search, dfs_search, ucs_search, dijkstra_search, astar_search, greedy_best_first_search
from backend.schemas import (
    SearchRequest,
    SearchResponse,
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
