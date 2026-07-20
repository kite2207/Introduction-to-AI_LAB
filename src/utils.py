from typing import List, Dict, Any
from src.models import TrafficGraph, CostEvaluator, Edge
from src.algorithms.base import SearchResult

class RouteExplainer:
    @staticmethod
    def explain_route(
        graph: TrafficGraph,
        result: SearchResult,
        cost_evaluator: CostEvaluator,
        alternative_results: List[SearchResult] = None
    ) -> str:
        """
        Generates a human-readable explanation of why the selected route was chosen.
        Written in Vietnamese as requested by the Lab requirements.
        """
        if not result.path:
            return "Không tìm thấy tuyến đường khả thi."

        # 1. Gather stats of the selected route
        nodes = graph.nodes
        path_names = [nodes[node_id].name for node_id in result.path]
        path_str = " → ".join(path_names)

        # Inspect edges along the path
        congested_segments = []
        flooded_segments = []
        construction_segments = []
        narrow_segments = []
        
        for i in range(len(result.path) - 1):
            u, v = result.path[i], result.path[i+1]
            # Find the active edge
            active_edge = None
            for edge in graph.get_neighbors(u):
                if edge.target_id == v:
                    active_edge = edge
                    break
            
            if active_edge:
                road_name = f"đoạn từ [{nodes[u].name}] đến [{nodes[v].name}]"
                if active_edge.congestion_level >= 4:
                    congested_segments.append(f"{road_name} (mức kẹt xe: {active_edge.congestion_level}/5)")
                if "flooding" in active_edge.risk_factors:
                    flooded_segments.append(road_name)
                if "construction" in active_edge.risk_factors:
                    construction_segments.append(road_name)
                if "narrow_road" in active_edge.risk_factors:
                    narrow_segments.append(road_name)

        # 2. Determine optimality guarantee
        optimal_guaranteed = result.algorithm_name in ["UCS", "Dijkstra", "A* (distance)", "A* (time)"]
        opt_text = (
            "Thuật toán này đảm bảo tìm ra đường đi tối ưu tuyệt đối theo hàm chi phí đã thiết lập."
            if optimal_guaranteed else
            "Thuật toán này sử dụng cơ chế tìm kiếm gần đúng (heuristic hoặc duyệt nhanh), không đảm bảo tối ưu tuyệt đối nhưng thời gian chạy rất nhanh."
        )

        # 3. Base explanation structure
        explanation = []
        explanation.append(f"### Giải thích Tuyến đường ({result.algorithm_name})")
        explanation.append(f"**Lộ trình đề xuất**: {path_str}")
        explanation.append(f"- **Tổng khoảng cách**: {result.total_distance:.1f} mét.")
        explanation.append(f"- **Tổng thời gian dự kiến**: {result.total_time / 60.0:.2f} phút.")
        explanation.append(f"- **Tổng chi phí tối ưu**: {result.total_cost:.2f} điểm chi phí.")
        explanation.append(f"- *{opt_text}*")

        # 4. Scenario analysis (congestion / risks)
        if congested_segments or flooded_segments or construction_segments:
            explanation.append("\n**Các lưu ý đặc biệt trên tuyến đường này**:")
            for item in congested_segments:
                explanation.append(f"- ⚠️ Kẹt xe nặng: {item}.")
            for item in flooded_segments:
                explanation.append(f"- 🌧️ Điểm ngập nước: {item}.")
            for item in construction_segments:
                explanation.append(f"- 🚧 Đang thi công: {item}.")
            for item in narrow_segments:
                explanation.append(f"- 🛣️ Đường hẹp: {item}.")
        else:
            explanation.append("\n- Tuyến đường thông thoáng, không gặp các trở ngại ngập nước hay công trình thi công.")

        # 5. Comparative explanation
        if alternative_results:
            explanation.append("\n**So sánh với các phương án khác**:")
            for alt in alternative_results:
                if alt.algorithm_name == result.algorithm_name or not alt.path:
                    continue
                
                # Check how they differ
                dist_diff = alt.total_distance - result.total_distance
                time_diff = (alt.total_time - result.total_time) / 60.0
                cost_diff = alt.total_cost - result.total_cost
                
                # Formulate comparison text
                if cost_diff > 0:
                    # Selected route is cheaper
                    explanation.append(
                        f"- So với tuyến đường của **{alt.algorithm_name}** (chi phí cao hơn {cost_diff:.1f}đ): "
                        f"Tuyến đường đề xuất giúp bạn tối ưu hơn."
                    )
                    if dist_diff < 0:
                        explanation.append(
                            f"  * Lưu ý: Mặc dù **{alt.algorithm_name}** có quãng đường ngắn hơn {-dist_diff:.1f} mét, "
                            f"nhưng do đi qua khu vực kẹt xe hoặc có rủi ro ngập úng cao hơn, "
                            f"nên tổng thời gian di chuyển và chi phí của nó lại cao hơn."
                        )
                elif cost_diff < 0:
                    explanation.append(
                        f"- Tuyến đường của **{alt.algorithm_name}** có chi phí tốt hơn tuyến hiện tại {-cost_diff:.1f} điểm chi phí. "
                        f"Đây là lựa chọn lý tưởng nếu bạn muốn tối ưu tối đa theo tiêu chí của thuật toán đó."
                    )
        
        return "\n".join(explanation)


def print_comparison_table(results: List[SearchResult]):
    """
    Prints a formatted markdown table comparing search algorithms.
    """
    header = "| Thuật toán | Đường đi khả thi | Chi phí tổng hợp | Khoảng cách (m) | Thời gian (phút) | Số nút đã khám phá | Thời gian chạy (ms) |"
    divider = "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    lines = [header, divider]
    
    for r in results:
        path_status = f"Có ({len(r.path)} nút)" if r.path else "Không"
        time_mins = r.total_time / 60.0 if r.path else 0.0
        line = f"| {r.algorithm_name} | {path_status} | {r.total_cost:.2f} | {r.total_distance:.1f} | {time_mins:.2f} | {r.explored_count} | {r.execution_time_ms:.3f} |"
        lines.append(line)
        
    print("\n".join(lines))
