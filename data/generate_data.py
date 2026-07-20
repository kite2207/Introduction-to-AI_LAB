import osmnx as ox
import random
import json

def generate_traffic_dataset():
    print("Đang tải dữ liệu bản đồ từ OpenStreetMap...")
    center_point = (10.768123, 106.666421) # Khu vực Quận 5 / Quận 10
    G = ox.graph_from_point(center_point, dist=800, network_type='drive')
    
    dataset = {}
    
    # Cấu hình random risk factors
    # Khai báo các loại rủi ro và tỷ lệ xuất hiện (tổng weights = 100%)
    risk_options = ["none", "construction", "flooding", "complex_intersection", "narrow_road"]
    risk_weights = [60, 10, 10, 10, 10] # 60% đường bình thường, 40% chia đều cho các rủi ro khác
    
    print("Đang xử lý tên đường và gắn trọng số kẹt xe/rủi ro...")

    # Khởi tạo Nodes và tự động tạo tên dựa trên đường giao nhau
    for node_id, data in G.nodes(data=True):
        street_names = set()
        
        # Duyệt qua các cạnh (đoạn đường) nối với đỉnh này để lấy tên đường
        for u, v, key, edge_data in G.edges(node_id, keys=True, data=True):
            if 'name' in edge_data:
                name = edge_data['name']
                # OSM đôi khi trả về mảng nếu đường có nhiều tên, ta lấy tên đầu tiên
                if isinstance(name, list):
                    street_names.add(name[0])
                elif isinstance(name, str):
                    street_names.add(name)
        
        # Đặt tên Node dựa trên số lượng đường cắt nhau
        street_list = list(street_names)
        if len(street_list) >= 2:
            node_name = f"Ngã giao {street_list[0]} - {street_list[1]}"
        elif len(street_list) == 1:
            node_name = f"Đường {street_list[0]}"
        else:
            node_name = f"Điểm nút {node_id}" # Backup cho các hẻm nhỏ không có tên trong OSM

        dataset[str(node_id)] = {
            "name": node_name,
            "lat": data['y'],
            "lng": data['x'],
            "type": "intersection",
            "connected_to": []
        }

    # Xử lý Edges và Random thông số
    for u, v, key, data in G.edges(keys=True, data=True):
        u_str = str(u)
        v_str = str(v)
        
        distance = round(data.get('length', 0), 2)
        is_oneway = data.get('oneway', False)
        direction = "one-way" if is_oneway else "two-way"
        
        # Random mức độ kẹt xe từ 1 đến 5
        congestion = random.randint(1, 5)
        
        # Random mức độ rủi ro
        risk = random.choices(risk_options, weights=risk_weights, k=1)[0]
        
        # Tính toán thời gian dựa trên tốc độ và mức độ kẹt xe
        base_speed = 400 
        actual_speed = base_speed / congestion 
        est_time = round((distance / actual_speed) * 60) if actual_speed > 0 else 999
        
        edge_info = {
            "target_node": v_str,
            "direction": direction,
            "risk_factors": risk,
            "congestion_level": congestion,
            "estimated_time": est_time,
            "distance": distance
        }
        
        dataset[u_str]["connected_to"].append(edge_info)
        
        # Xử lý đường 2 chiều
        if direction == "two-way":
            existing_targets = [edge['target_node'] for edge in dataset[v_str]["connected_to"]]
            if u_str not in existing_targets:
                reverse_edge = edge_info.copy()
                reverse_edge["target_node"] = u_str
                dataset[v_str]["connected_to"].append(reverse_edge)

    # Xuất file
    with open('hcm_traffic_data.json', 'w', encoding = 'utf-8') as f:
        json.dump(dataset, f, ensure_ascii = False, indent = 4)
        
    print("Hoàn tất! Dữ liệu đã được lưu vào file 'hcm_traffic_data.json'.")

if __name__ == "__main__":
    generate_traffic_dataset()