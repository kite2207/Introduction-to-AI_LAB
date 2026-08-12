"""
Pydantic schemas cho FastAPI request/response validation
"""
from pydantic import BaseModel
from typing import List, Optional, Literal


# ─── Request Schemas ────────────────────────────────────────

class SearchRequest(BaseModel):
    start: str
    end: str
    algorithm: str  # Frontend gửi display name: "A*", "Depth-first Search", ...
    optimization: Literal["distance", "time", "mixed"] = "mixed"


# ─── Response Schemas ───────────────────────────────────────

class NodeResponse(BaseModel):
    node_id: str
    name: str
    lat: float
    lng: float
    node_type: str


class EdgeResponse(BaseModel):
    source_id: str
    target_id: str
    distance: float
    estimated_time: float
    congestion_level: int
    road_type: str
    direction: str
    risk_factors: List[str] = []


class Coordinate(BaseModel):
    lat: float
    lng: float

class SearchResponse(BaseModel):
    algorithm_name: str
    path: List[str]                # node IDs theo thứ tự start → end
    explored_nodes: List[str]      # thứ tự node được khám phá
    total_cost: float
    total_distance: float          # meters
    total_time: float              # seconds
    explored_count: int
    execution_time_ms: float
    # Thông tin bổ sung cho UI
    path_node_names: List[str] = []
    path_coordinates: List[Coordinate] = []
    start_name: str = ""
    end_name: str = ""


class GraphInfoResponse(BaseModel):
    node_count: int
    edge_count: int
