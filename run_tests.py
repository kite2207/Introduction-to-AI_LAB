import os
from src.models import TrafficGraph, CostEvaluator
from src.algorithms.uninformed import bfs_search, dfs_search
from src.algorithms.informed import ucs_search, dijkstra_search, astar_search, greedy_best_first_search
from src.algorithms.multi_location import solve_tsp_nearest_neighbor, solve_tsp_dynamic_programming
from src.utils import RouteExplainer, print_comparison_table

def main():
    print("=" * 80)
    print("AI LAB 1: VIETNAMESE TRAFFIC ROUTE OPTIMIZATION - TEST RUNNER")
    print("=" * 80)

    # 1. Load the Graph
    graph = TrafficGraph()
    data_dir = "data"
    nodes_path = os.path.join(data_dir, "nodes.json")
    edges_path = os.path.join(data_dir, "edges.json")

    print(f"Loading data from: {nodes_path} and {edges_path}...")
    graph.load_from_json(nodes_path, edges_path)
    print(f"Graph loaded successfully! Nodes: {len(graph.nodes)}, Edges (Forward/Two-Way): {len(graph.adjacency_list)}")

    # Define test endpoints
    start_node = "N01"  # ĐH Khoa học Tự nhiên
    goal_node = "N08"   # Bệnh viện Chợ Rẫy

    # =========================================================================
    # SCENARIO 1: SHORT-ROUTE BY PHYSICAL DISTANCE
    # =========================================================================
    print("\n" + "=" * 80)
    print("KỊCH BẢN 1: TỐI ƯU HÓA THEO KHOẢNG CÁCH VẬT LÝ (SHORTEST DISTANCE)")
    print("Hàm chi phí chỉ tính khoảng cách: Cost = 1.0 * Distance")
    print("=" * 80)
    
    # Cost weights: only distance counts
    distance_evaluator = CostEvaluator(alpha=1.0, beta=0.0, gamma=0.0, delta=0.0)

    results_sc1 = []
    
    # Run algorithms
    results_sc1.append(bfs_search(graph, start_node, goal_node, distance_evaluator))
    results_sc1.append(dfs_search(graph, start_node, goal_node, distance_evaluator))
    results_sc1.append(ucs_search(graph, start_node, goal_node, distance_evaluator))
    results_sc1.append(dijkstra_search(graph, start_node, goal_node, distance_evaluator))
    results_sc1.append(astar_search(graph, start_node, goal_node, distance_evaluator, heuristic_type="distance"))
    results_sc1.append(greedy_best_first_search(graph, start_node, goal_node, distance_evaluator, heuristic_type="distance"))

    # Print comparison table
    print_comparison_table(results_sc1)

    # Print route explanation for A* distance
    astar_dist_res = results_sc1[4]
    explanation_sc1 = RouteExplainer.explain_route(graph, astar_dist_res, distance_evaluator, results_sc1)
    print("\n" + explanation_sc1)

    # =========================================================================
    # SCENARIO 2: FASTEST ROUTE UNDER RUSH HOUR CONGESTION
    # =========================================================================
    print("\n" + "=" * 80)
    print("KỊCH BẢN 2: TỐI ƯU HÓA THEO THỜI GIAN DI CHUYỂN TRONG GIỜ CAO ĐIỂM (RUSH HOUR)")
    print("Hàm chi phí ưu tiên thời gian và kẹt xe: Cost = 0.1*Dist + 1.0*Time + 1.5*Congestion + 0.2*Risk")
    print("=" * 80)

    # Normal weights prioritizing time and congestion avoidance
    rush_hour_evaluator = CostEvaluator(alpha=0.1, beta=1.0, gamma=1.5, delta=0.2)

    results_sc2 = []
    results_sc2.append(bfs_search(graph, start_node, goal_node, rush_hour_evaluator))
    results_sc2.append(dfs_search(graph, start_node, goal_node, rush_hour_evaluator))
    results_sc2.append(ucs_search(graph, start_node, goal_node, rush_hour_evaluator))
    results_sc2.append(dijkstra_search(graph, start_node, goal_node, rush_hour_evaluator))
    results_sc2.append(astar_search(graph, start_node, goal_node, rush_hour_evaluator, heuristic_type="time"))
    results_sc2.append(greedy_best_first_search(graph, start_node, goal_node, rush_hour_evaluator, heuristic_type="time"))

    print_comparison_table(results_sc2)

    # Explaining A* time route
    astar_time_res = results_sc2[4]
    explanation_sc2 = RouteExplainer.explain_route(graph, astar_time_res, rush_hour_evaluator, results_sc2)
    print("\n" + explanation_sc2)

    # =========================================================================
    # SCENARIO 3: RAINY/FLOOD SEASON (AVOIDING FLOOD RISK)
    # =========================================================================
    print("\n" + "=" * 80)
    print("KỊCH BẢN 3: ĐƯỜNG ĐI TRÁNH ĐIỂM NGẬP LỤT (AVOIDING FLOODING RISK)")
    print("Hàm chi phí phạt rất cao cho rủi ro ngập: Cost = 0.5*Dist + 0.5*Time + 0.5*Congestion + 5.0*Risk")
    print("=" * 80)

    # High penalty for risk factors
    flood_evaluator = CostEvaluator(alpha=0.5, beta=0.5, gamma=0.5, delta=5.0)

    results_sc3 = []
    # To demonstrate routing around floods, we will search from N02 (Nguyễn Văn Cừ - ADV) to N18 (Cầu Nguyễn Văn Cừ)
    # N02 -> N16 -> N17 (flooded) -> N18  vs  N02 -> N16 -> N18
    results_sc3.append(ucs_search(graph, "N02", "N18", flood_evaluator))
    results_sc3.append(astar_search(graph, "N02", "N18", flood_evaluator, heuristic_type="distance"))

    print_comparison_table(results_sc3)

    # Explain route selection
    explanation_sc3 = RouteExplainer.explain_route(graph, results_sc3[1], flood_evaluator, results_sc3)
    print("\n" + explanation_sc3)

    # =========================================================================
    # SCENARIO 4: MULTI-LOCATION ROUTE OPTIMIZATION (TSP)
    # =========================================================================
    print("\n" + "=" * 80)
    print("KỊCH BẢN 4: TỐI ƯU HÓA LỘ TRÌNH ĐI QUA NHIỀU ĐỊA ĐIỂM (TSP)")
    print("Điểm xuất phát: N01. Cần ghé qua: N05, N14, N08, N12 rồi quay về N01.")
    print("=" * 80)

    visit_targets = ["N05", "N14", "N08", "N12"]
    
    # Use rush hour cost evaluator
    tsp_evaluator = CostEvaluator(alpha=0.2, beta=1.0, gamma=1.0, delta=1.0)
    
    # 1. Solve using Nearest Neighbor
    nn_order, nn_path, nn_cost = solve_tsp_nearest_neighbor(graph, start_node, visit_targets, tsp_evaluator)
    # Convert path list to names
    nn_order_names = [graph.nodes[nid].name for nid in nn_order]
    
    # 2. Solve using Dynamic Programming (Held-Karp)
    dp_order, dp_path, dp_cost = solve_tsp_dynamic_programming(graph, start_node, visit_targets, tsp_evaluator)
    dp_order_names = [graph.nodes[nid].name for nid in dp_order]

    print("\n--- KẾT QUẢ SO SÁNH TSP ---")
    print(f"1. Thuật toán Láng giềng gần nhất (Nearest Neighbor) [Lời giải Gần đúng]:")
    print(f"   - Thứ tự ghé thăm: {' -> '.join(nn_order_names)}")
    print(f"   - Số nút trong hành trình chi tiết: {len(nn_path)} nút")
    print(f"   - Tổng chi phí hành trình: {nn_cost:.2f} điểm chi phí")
    
    print(f"\n2. Thuật toán Quy hoạch động (Dynamic Programming TSP) [Lời giải Tối ưu]:")
    print(f"   - Thứ tự ghé thăm: {' -> '.join(dp_order_names)}")
    print(f"   - Số nút trong hành trình chi tiết: {len(dp_path)} nút")
    print(f"   - Tổng chi phí hành trình: {dp_cost:.2f} điểm chi phí")

    if dp_cost < nn_cost:
        saved = nn_cost - dp_cost
        print(f"\n=> [Nhận xét]: Quy hoạch động tìm thấy lộ trình tối ưu hơn và tiết kiệm được {saved:.2f} điểm chi phí so với thuật toán Greedy Nearest Neighbor!")
    else:
        print("\n=> [Nhận xét]: Cả hai thuật toán đều tìm thấy lộ trình có chi phí tương đương nhau ở trường hợp thử nghiệm này.")
    
    print("\n" + "=" * 80)
    print("KẾT THÚC CÁC BÀI THỬ NGHIỆM")
    print("=" * 80)

if __name__ == "__main__":
    main()
