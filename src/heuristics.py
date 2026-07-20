import math
from src.models import Node

def haversine_distance(node_a: Node, node_b: Node) -> float:
    """
    Calculate the great-circle distance between two GPS coordinates in meters.
    This is used as the heuristic function for shortest distance paths.
    It is both admissible and consistent.
    """
    R = 6371000.0  # Earth radius in meters
    lat1, lng1 = math.radians(node_a.lat), math.radians(node_a.lng)
    lat2, lng2 = math.radians(node_b.lat), math.radians(node_b.lng)

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c

def get_time_scaled_heuristic(node_a: Node, node_b: Node, max_speed_mps: float = 16.67) -> float:
    """
    Returns an admissible travel time heuristic in seconds.
    Computes straight line distance and divides by the maximum possible speed
    to guarantee the heuristic never overestimates the actual travel time.
    60 km/h = 16.67 m/s is the default max speed.
    """
    distance = haversine_distance(node_a, node_b)
    return distance / max_speed_mps
