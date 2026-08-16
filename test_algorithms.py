"""
Quick test script: chạy thử các thuật toán với data nodes.json + edges.json
Usage: python test_algorithms.py
"""
import sys
import os

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Đảm bảo import đúng từ thư mục gốc
sys.path.insert(0, os.path.dirname(__file__))

from src.models import TrafficGraph, CostEvaluator
from src.algorithms import bfs_search, dfs_search, dijkstra_search, astar_search, greedy_best_first_search

# ──────────────────────────────────────────────
# 1. Load graph từ file JSON
# ──────────────────────────────────────────────
NODES_PATH = "data/nodes.json"
EDGES_PATH = "data/edges.json"

print("=" * 60)
print("  Loading graph from JSON files...")
print("=" * 60)

graph = TrafficGraph()
graph.load_from_json(NODES_PATH, EDGES_PATH)

print(f"  ✅  Nodes loaded : {len(graph.nodes)}")
print(f"  ✅  Edges loaded : {sum(len(v) for v in graph.adjacency_list.values())}")
print()

# In danh sách node IDs
print("Available nodes:")
for nid, node in list(graph.nodes.items()):
    print(f"  {nid:>5}  |  {node.name}")
print()

# ──────────────────────────────────────────────
# 2. Chọn START và END để test
# ──────────────────────────────────────────────
node_ids = list(graph.nodes.keys())
START_ID = node_ids[0]   # Node đầu tiên
END_ID   = node_ids[-1]  # Node cuối cùng

print(f"🔴  Start : {START_ID} — {graph.nodes[START_ID].name}")
print(f"🟢  End   : {END_ID}  — {graph.nodes[END_ID].name}")
print()

# ──────────────────────────────────────────────
# 3. Các CostEvaluator theo optimization mode
# ──────────────────────────────────────────────
cost_modes = {
    "Default" : CostEvaluator(optimization="mixed"),
    "Time"    : CostEvaluator(optimization="time"),
    "Distance": CostEvaluator(optimization="distance"),
    "Cost"    : CostEvaluator(optimization="mixed"),
}

# ──────────────────────────────────────────────
# 4. Chạy tất cả thuật toán
# ──────────────────────────────────────────────
def fmt_time(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}m {s}s"

def print_result(result):
    if not result.path:
        print(f"  ⚠️  No path found!")
        return
    print(f"  Algorithm     : {result.algorithm_name}")
    print(f"  Path length   : {len(result.path)} nodes")
    print(f"  Path          : {' → '.join(result.path)}")
    print(f"  Distance      : {result.total_distance:.1f} m  ({result.total_distance/1000:.2f} km)")
    print(f"  Travel time   : {fmt_time(result.total_time)}  ({result.total_time:.0f}s)")
    print(f"  Total cost    : {result.total_cost:.2f}")
    print(f"  Nodes explored: {result.explored_count}")
    print(f"  Exec time     : {result.execution_time_ms:.3f} ms")

evaluator = cost_modes["Default"]

algorithms = [
    ("DFS",    lambda: dfs_search(graph, START_ID, END_ID, evaluator)),
    ("BFS",    lambda: bfs_search(graph, START_ID, END_ID, evaluator)),
    ("Dijkstra", lambda: dijkstra_search(graph, START_ID, END_ID, evaluator)),
    ("A* (distance)", lambda: astar_search(graph, START_ID, END_ID, cost_modes["Distance"])),
    ("A* (time)",     lambda: astar_search(graph, START_ID, END_ID, cost_modes["Time"])),
    ("Greedy Best-First", lambda: greedy_best_first_search(graph, START_ID, END_ID, evaluator)),
]

for name, fn in algorithms:
    print(f"{'─'*60}")
    print(f"  🔍  Running: {name}")
    result = fn()
    print_result(result)
    print()

# ──────────────────────────────────────────────
# 5. So sánh A* với các optimization mode
# ──────────────────────────────────────────────
print(f"{'='*60}")
print("  A* across optimization modes")
print(f"{'='*60}")
for mode_name, evaluator in cost_modes.items():
    result = astar_search(graph, START_ID, END_ID, evaluator)
    status = "✅" if result.path else "❌"
    if result.path:
        print(f"  {status} [{mode_name:>8}]  dist={result.total_distance/1000:.2f}km  "
              f"time={fmt_time(result.total_time)}  cost={result.total_cost:.1f}  "
              f"explored={result.explored_count}  exec={result.execution_time_ms:.2f}ms")
    else:
        print(f"  {status} [{mode_name:>8}]  No path found")

print()
print("✅  All algorithms ran successfully!")
