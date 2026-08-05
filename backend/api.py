"""
FastAPI Backend — Route Finding API
Run: uvicorn backend.api:app --reload --port 8000
"""
import os
import sys

# Thêm thư mục gốc vào path để import src.*
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.models import TrafficGraph, CostEvaluator
from src.algorithms.uninformed import bfs_search, dfs_search
from src.algorithms.informed import (
    ucs_search, dijkstra_search, astar_search, greedy_best_first_search
)
from backend.schemas import (
    SearchRequest, SearchResponse,
    NodeResponse, EdgeResponse, GraphInfoResponse
)

# ─────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# Load graph một lần khi khởi động
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
NODES_PATH = os.path.join(BASE_DIR, "data", "nodes.json")
EDGES_PATH = os.path.join(BASE_DIR, "data", "edges.json")

graph = TrafficGraph()
graph.load_from_json(NODES_PATH, EDGES_PATH)
print(f"[API] Graph loaded: {len(graph.nodes)} nodes, "
      f"{sum(len(v) for v in graph.adjacency_list.values())} edges")


# ─────────────────────────────────────────────
# Helper: build CostEvaluator từ optimization mode
# ─────────────────────────────────────────────
def get_cost_evaluator(optimization: str) -> CostEvaluator:
    configs = {
        "default":  CostEvaluator(alpha=1.0, beta=1.0, gamma=1.0, delta=1.0),
        "time":     CostEvaluator(alpha=0.1, beta=5.0, gamma=2.0, delta=1.0),
        "distance": CostEvaluator(alpha=5.0, beta=0.1, gamma=0.5, delta=0.5),
        "cost":     CostEvaluator(alpha=1.0, beta=2.0, gamma=3.0, delta=2.0),
    }
    return configs.get(optimization, configs["default"])


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/api/nodes", response_model=list[NodeResponse], tags=["Graph"])
def get_nodes():
    """Trả về danh sách tất cả nodes (giao lộ/địa điểm)."""
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
    """Trả về danh sách các cạnh (đường đi), không trùng lặp chiều."""
    seen = set()
    result = []
    for edges in graph.adjacency_list.values():
        for e in edges:
            key = tuple(sorted([e.source_id, e.target_id]))
            if key not in seen:
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
    """Thông tin tổng quan về graph."""
    return GraphInfoResponse(
        node_count=len(graph.nodes),
        edge_count=sum(len(v) for v in graph.adjacency_list.values()),
    )


@app.post("/api/search", response_model=SearchResponse, tags=["Search"])
def search_route(req: SearchRequest):
    """
    Tìm đường từ start → end với thuật toán và optimization được chọn.
    """
    # Validate nodes tồn tại
    if req.start not in graph.nodes:
        raise HTTPException(status_code=404, detail=f"Node '{req.start}' không tồn tại")
    if req.end not in graph.nodes:
        raise HTTPException(status_code=404, detail=f"Node '{req.end}' không tồn tại")
    if req.start == req.end:
        raise HTTPException(status_code=400, detail="Start và End phải khác nhau")

    evaluator = get_cost_evaluator(req.optimization)

    # Map algorithm names from frontend
    algo_map = {
        "depth-first search": "dfs",
        "breadth-first search": "bfs",
        "dijkstra's algorithm": "dijkstra",
        "a* search": "astar"
    }
    raw_algo = req.algorithm.lower()
    algo = algo_map.get(raw_algo, raw_algo)

    # Dispatch thuật toán
    if algo == "dfs":
        result = dfs_search(graph, req.start, req.end, evaluator)
    elif algo == "bfs":
        result = bfs_search(graph, req.start, req.end, evaluator)
    elif algo == "dijkstra":
        result = dijkstra_search(graph, req.start, req.end, evaluator)
    elif algo == "ucs":
        result = ucs_search(graph, req.start, req.end, evaluator)
    elif algo == "astar":
        result = astar_search(graph, req.start, req.end, evaluator)
    elif algo == "greedy":
        result = greedy_best_first_search(graph, req.start, req.end, evaluator)
    else:
        raise HTTPException(status_code=400, detail=f"Thuật toán '{req.algorithm}' không hợp lệ")

    if not result.path:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy đường từ {req.start} đến {req.end}"
        )

    # Thêm tên node vào response để hiển thị trên UI
    path_names = [graph.nodes[nid].name for nid in result.path if nid in graph.nodes]

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
        start_name=graph.nodes[req.start].name,
        end_name=graph.nodes[req.end].name,
    )


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Route Finding API is running"}
