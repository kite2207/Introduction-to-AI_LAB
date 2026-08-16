"""
FastAPI Route Finding API.

Run from the project root:
    python -m uvicorn backend.api:app --reload --port 8000

The graph source is data/hcm_traffic_data.json.
The existing TrafficGraph/search algorithms are kept unchanged by adapting
hcm_traffic_data.json to the existing TrafficGraph.load_from_json() interface.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models import TrafficGraph, CostEvaluator
from src.algorithms import (
    bfs_search, dfs_search, ucs_search, dijkstra_search, astar_search, greedy_best_first_search
)
from backend.schemas import (
    SearchRequest,
    SearchResponse,
    NodeResponse,
    EdgeResponse,
    GraphInfoResponse,
)

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


def make_legacy_graph_files(data: dict[str, Any]) -> tuple[Path, Path]:
    """Adapt hcm_traffic_data.json to TrafficGraph.load_from_json()."""
    nodes = []
    edges = []

    for node_id, node in data.items():
        nodes.append(
            {
                "node_id": str(node_id),
                "name": node.get("name", str(node_id)),
                "lat": node.get("lat"),
                "lng": node.get("lng"),
                "node_type": node.get("type", "intersection"),
            }
        )

        for c in node.get("connected_to", []):
            target = c.get("target_node")
            if target is None:
                continue
            edges.append(
                {
                    "source_id": str(node_id),
                    "target_id": str(target),
                    "distance": c.get("distance", 0),
                    "estimated_time": c.get("estimated_time", 0),
                    "congestion_level": c.get("congestion_level", 1),
                    "road_type": c.get("road_type"),
                    "direction": c.get("direction", "two-way"),
                    "risk_factors": c.get("risk_factors", []),
                }
            )

    temp_dir = Path(tempfile.mkdtemp(prefix="route_hcm_"))
    nodes_path = temp_dir / "nodes.json"
    edges_path = temp_dir / "edges.json"
    nodes_path.write_text(json.dumps(nodes, ensure_ascii=False), encoding="utf-8")
    edges_path.write_text(json.dumps(edges, ensure_ascii=False), encoding="utf-8")
    return nodes_path, edges_path


hcm_data = load_hcm_data()
GENERATED_NODES_PATH, GENERATED_EDGES_PATH = make_legacy_graph_files(hcm_data)

graph = TrafficGraph()
graph.load_from_json(str(GENERATED_NODES_PATH), str(GENERATED_EDGES_PATH))

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



def _reference_route(start_id: str, end_id: str, optimization: str):
    evaluator = get_cost_evaluator(optimization)
    ref = dijkstra_search(
        graph,
        start_id,
        end_id,
        evaluator,
    )

    if not ref.path:
        return None

    return {
        "algorithm": "Dijkstra",
        "optimization": optimization,
        "path": list(ref.path),
        "route_names": [
            graph.nodes[nid].name
            for nid in ref.path
            if nid in graph.nodes
        ],
        "distance": ref.total_distance,
        "time": ref.total_time,
        "cost": ref.total_cost,
    }


def build_route_explanation(
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
):
    mode = optimization

    # Same-objective Dijkstra = optimality reference.
    optimality_ref = _reference_route(
        start_id,
        end_id,
        mode,
    )

    # Actual alternatives.
    shortest_ref = _reference_route(
        start_id,
        end_id,
        "distance",
    )
    fastest_ref = _reference_route(
        start_id,
        end_id,
        "time",
    )

    def compare(ref):
        if ref is None:
            return None

        return {
            **ref,
            "distance_difference": (
                total_distance - ref["distance"]
            ),
            "time_difference": (
                total_time - ref["time"]
            ),
            "cost_difference": (
                None
                if total_cost is None
                else total_cost - ref["cost"]
            ),
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
        optimality = (
            "UCS/Dijkstra đảm bảo tối ưu khi chi phí cạnh không âm "
            f"theo mục tiêu '{mode}'."
        )
    elif algo == "astar":
        optimality = (
            "A* đảm bảo tối ưu khi heuristic là admissible "
            "(và consistent đối với tìm kiếm trên đồ thị)."
        )
    elif algo == "bfs":
        optimality = (
            "BFS đảm bảo tối ưu theo số bước tối thiểu, không nhất thiết "
            "theo khoảng cách, thời gian hay chi phí giao thông."
        )
    else:
        optimality = (
            f"{algorithm_name} không đảm bảo tìm được đường tối ưu "
            f"theo chi phí giao thông '{mode}'."
        )

    congested = []
    for source_id, target_id in zip(path, path[1:]):
        edge = next(
            (
                e
                for e in graph.get_neighbors(source_id)
                if str(e.target_id) == str(target_id)
            ),
            None,
        )

        if edge is None or edge.congestion_level < 4:
            continue

        risk = getattr(edge, "risk_factors", "none")
        if isinstance(risk, list):
            risk = ", ".join(str(v) for v in risk)

        congested.append({
            "from": graph.nodes[source_id].name,
            "to": graph.nodes[target_id].name,
            "congestion": edge.congestion_level,
            "risk": risk,
        })

    same_reference = (
        optimality_ref is not None
        and total_cost is not None
        and abs(total_cost - optimality_ref["cost"]) < 1e-9
    )

    return {
        "headline": (
            f"Tuyến đường được chọn được tối ưu theo {objective}."
        ),
        "why_selected": (
            f"{algorithm_name} chọn tuyến đường này dựa trên {criterion} "
            f"theo mục tiêu '{mode}'."
        ),
        "optimality": optimality,
        "optimality_reference": {
            "algorithm": "Dijkstra",
            "optimization": mode,
            "route_names": (
                optimality_ref["route_names"]
                if optimality_ref else []
            ),
            "distance": (
                optimality_ref["distance"]
                if optimality_ref else None
            ),
            "time": (
                optimality_ref["time"]
                if optimality_ref else None
            ),
            "cost": (
                optimality_ref["cost"]
                if optimality_ref else None
            ),
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
            "Dijkstra với cùng mục tiêu được dùng làm tham chiếu tối ưu. "
            "Tuyến ngắn nhất và tuyến nhanh nhất là các phương án "
            "thay thế thực tế."
        ),
    }


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
