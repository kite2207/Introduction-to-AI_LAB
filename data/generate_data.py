import osmnx as ox
import random
import json
import networkx as nx
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def generate_traffic_dataset():
    random.seed(42)
    print("1. Đang tải dữ liệu mạng lưới đường từ OpenStreetMap...")
    places = ["Quận 5, Hồ Chí Minh, Việt Nam", "Quận 10, Hồ Chí Minh, Việt Nam"]
    cf = (
        '["highway"~"primary|secondary|tertiary|trunk|primary_link|'
        'secondary_link|tertiary_link|residential|unclassified"]'
    )
    
    # Tải đồ thị mặc định
    G = ox.graph_from_place(places, custom_filter=cf, simplify=True)
    
    # =====================================================================
    # THUẬT TOÁN GOM CỤM VÒNG XOAY VÀ NGÃ TƯ PHỨC TẠP THÀNH 1 NODE
    # =====================================================================
    print("   -> Đang xử lý gom cụm vòng xoay và làm sạch ngã tư...")
    # Bước 1: Chuyển đổi hệ tọa độ sang hệ mét để tính toán khoảng cách
    G_proj = ox.project_graph(G)
    
    # Bước 2: Gom các node rất gần nhau thành một node trung tâm.
    # Mức 12 m giữ được các giao lộ gần nhau trên mạng đường dân cư.
    G_cons = ox.consolidate_intersections(G_proj, rebuild_graph=True, tolerance=12, dead_ends=False)
    
    # Bước 3: Đưa hệ tọa độ về lại Kinh độ/Vĩ độ (Lat/Lng) chuẩn ban đầu
    G = ox.project_graph(G_cons, to_crs="EPSG:4326")
    # =====================================================================
    
    # Chống đứt gãy bằng liên thông yếu
    import networkx as nx
    largest_wcc = max(nx.weakly_connected_components(G), key=len)
    G = G.subgraph(largest_wcc).copy()

    print("2. Đang chuyển đổi dữ liệu và gắn rủi ro...")
    dataset = {}
    
    # Chỉ giữ các node xác định được ít nhất một tên đường.
    for node_id, data in G.nodes(data=True):
        street_names = set()
        incident_edges = list(G.in_edges(node_id, keys=True, data=True))
        incident_edges.extend(G.out_edges(node_id, keys=True, data=True))
        for u, v, key, edge_data in incident_edges:
            name = edge_data.get('name')
            if isinstance(name, list):
                street_names.update(item for item in name if isinstance(item, str) and item.strip())
            elif isinstance(name, str) and name.strip():
                street_names.add(name)
        
        street_list = sorted(street_names)
        if len(street_list) >= 2: node_name = f"{street_list[0]} - {street_list[1]}"
        elif len(street_list) == 1: node_name = street_list[0]
        else:
            continue

        dataset[str(node_id)] = {
            "name": node_name,
            "lat": data['y'],
            "lng": data['x'],
            "type": "intersection",
            "connected_to": []
        }

    # Xử lý Edges (Các đoạn đường thẳng tắp)
    for u, v, key, data in G.edges(keys=True, data=True):
        u_str = str(u)
        v_str = str(v)

        # Một cạnh không hợp lệ nếu một trong hai đầu đã bị loại vì không có tên.
        if u_str not in dataset or v_str not in dataset:
            continue
        
        distance = round(data.get('length', 0), 2)
        direction = "one-way" if data.get('oneway', False) else "two-way"
        congestion = random.randint(1, 5)
        
        # Thời gian cơ sở ở điều kiện thông thoáng (400 mét/phút).
        # Hệ số kẹt xe được áp dụng đúng một lần trong CostEvaluator.
        base_speed = 400
        est_time = round((distance / base_speed) * 60)
        
        # LOGIC ĐA RỦI RO
        risks = []
        road_type = data.get('highway', '')
        if isinstance(road_type, list): road_type = road_type[0]
        if not isinstance(road_type, str) or not road_type:
            road_type = "unknown"
            
        if road_type in ['tertiary', 'tertiary_link']:
            risks.append("narrow_road")
            
        if G.degree(u) >= 5 or G.degree(v) >= 5:
            risks.append("complex_intersection")
            
        if 'name' in data and any(street in str(data.get('name', '')) for street in ['3 Tháng 2', 'Lý Thường Kiệt']):
            risks.append("flooding")
        
        if road_type in ['primary', 'trunk'] and random.random() < 0.15:
            risks.append("construction")
        
        if len(risks) == 0:
            risks.append("none")

        # Preserve the real OSM road shape. Shapely uses (lng, lat), while
        # Leaflet expects (lat, lng).
        geometry = data.get("geometry")
        if geometry is not None:
            geometry_points = [
                [lat, lng]
                for lng, lat in geometry.coords
            ]
        else:
            geometry_points = [
                [G.nodes[u]["y"], G.nodes[u]["x"]],
                [G.nodes[v]["y"], G.nodes[v]["x"]],
            ]
            
        edge_info = {
            "target_node": v_str,
            "direction": direction,
            "risk_factors": risks,
            "congestion_level": congestion,
            "estimated_time": est_time,
            "distance": distance,
            "road_type": road_type,
            "geometry": geometry_points,
        }
        dataset[u_str]["connected_to"].append(edge_info)
        
        # Xử lý đường 2 chiều
        if direction == "two-way":
            existing_targets = [edge['target_node'] for edge in dataset[v_str]["connected_to"]]
            if u_str not in existing_targets:
                reverse_edge = {
                    **edge_info,
                    "target_node": u_str,
                    "geometry": list(reversed(geometry_points)),
                }
                dataset[v_str]["connected_to"].append(reverse_edge)

    output_path = Path(__file__).resolve().parent / 'hcm_traffic_data.json'
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=4)
        
    print(f"Hoàn tất! Dữ liệu đã được ghi vào {output_path}.")

if __name__ == "__main__":
    generate_traffic_dataset()
