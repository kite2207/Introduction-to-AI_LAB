"""
Pydantic schemas for FastAPI request/response validation.
"""

from typing import List, Optional, Union

from pydantic import BaseModel


class SearchRequest(BaseModel):
    start: str
    end: str
    algorithm: str = "A*"
    # Frontend starts with "default"; api.py maps it to "mixed".
    optimization: str = "default"


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
    road_type: Optional[str] = None
    direction: str
    # hcm_traffic_data stores risk_factors as strings such as "none".
    risk_factors: Union[str, List[str]] = "none"


class Coordinate(BaseModel):
    lat: float
    lng: float


class SearchResponse(BaseModel):
    algorithm_name: str
    path: List[str]
    explored_nodes: List[str]
    total_cost: Optional[float] = None
    total_distance: float
    total_time: float
    explored_count: int
    execution_time_ms: float
    path_node_names: List[str] = []
    path_coordinates: List[Coordinate] = []
    start_name: str = ""
    end_name: str = ""


class GraphInfoResponse(BaseModel):
    node_count: int
    edge_count: int
