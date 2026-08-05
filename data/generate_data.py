import osmnx as ox
import random
import json
import pandas as pd
import math

def generate_traffic_dataset():
    print("1. Đang tải dữ liệu mạng lưới đường từ OpenStreetMap...")
    center_point = (10.768123, 106.666421) # Khu vực Quận 5 / Quận 10
    dist = 800
    G = ox.graph_from_point(center_point, dist=dist, network_type='drive')
    
    # Định nghĩa các loại địa điểm muốn lấy
    tags = {
        'amenity': ['university', 'college', 'hospital', 'clinic', 'marketplace'],
        'shop': ['mall', 'supermarket']
    }
    
    print("2. Đang tải các địa điểm đặc trưng và chèn vào giữa đường...")
    try:
        pois = ox.features_from_point(center_point, tags=tags, dist=dist)
        poi_id_counter = 9000000 # Dùng ID số lớn để không trùng với ID ngã tư của OSM
        count = 0
        
        if not pois.empty:
            for idx, row in pois.iterrows():
                name = row.get('name')
                if pd.isna(name): continue
                
                # Lấy tọa độ
                if row.geometry.geom_type == 'Point':
                    lat, lng = row.geometry.y, row.geometry.x
                else:
                    lat, lng = row.geometry.centroid.y, row.geometry.centroid.x
                    
                # Phân loại
                poi_type = "landmark"
                if 'amenity' in row and pd.notna(row['amenity']):
                    if row['amenity'] in ['hospital', 'clinic']: poi_type = "hospital"
                    elif row['amenity'] in ['university', 'college']: poi_type = "university"
                elif 'shop' in row and pd.notna(row['shop']):
                    if row['shop'] in ['mall', 'supermarket']: poi_type = "mall"
                
                #Edge splitting
                try:
                    # Tìm đoạn đường (cạnh) gần địa điểm này nhất
                    u, v, key = ox.distance.nearest_edges(G, X=lng, Y=lat)
                    
                    # Thêm Node mới vào đồ thị
                    poi_id = poi_id_counter
                    poi_id_counter += 1
                    G.add_node(poi_id, y=lat, x=lng, name=str(name), type=poi_type)
                    
                    # Lấy thông tin đoạn đường gốc
                    edge_data = G.get_edge_data(u, v)[key].copy()
                    orig_length = edge_data.get('length', 100) # Chiều dài gốc
                    
                    # Tính toán tỷ lệ chia cắt khoảng cách dựa trên tọa độ
                    lat_u, lng_u = G.nodes[u]['y'], G.nodes[u]['x']
                    lat_v, lng_v = G.nodes[v]['y'], G.nodes[v]['x']
                    
                    dist_u_poi = math.hypot(lat_u - lat, lng_u - lng)
                    dist_poi_v = math.hypot(lat - lat_v, lng - lng_v)
                    total_dist = dist_u_poi + dist_poi_v
                    
                    ratio_u = dist_u_poi / total_dist if total_dist > 0 else 0.5
                    ratio_v = dist_poi_v / total_dist if total_dist > 0 else 0.5
                    
                    # Xóa cạnh gốc U -> V
                    G.remove_edge(u, v, key)
                    
                    # Tạo cạnh mới 1: U -> POI
                    edge_1 = edge_data.copy()
                    edge_1['length'] = orig_length * ratio_u
                    G.add_edge(u, poi_id, **edge_1)
                    
                    # Tạo cạnh mới 2: POI -> V
                    edge_2 = edge_data.copy()
                    edge_2['length'] = orig_length * ratio_v
                    G.add_edge(poi_id, v, **edge_2)
                    
                    # Nếu là đường 2 chiều, xử lý cắt luôn cạnh ngược V -> U
                    if G.has_edge(v, u):
                        rev_keys = list(G.get_edge_data(v, u).keys())
                        for r_key in rev_keys:
                            rev_edge_data = G.get_edge_data(v, u)[r_key].copy()
                            rev_orig_length = rev_edge_data.get('length', 100)
                            
                            G.remove_edge(v, u, r_key)
                            
                            # V -> POI
                            rev_edge_1 = rev_edge_data.copy()
                            rev_edge_1['length'] = rev_orig_length * ratio_v
                            G.add_edge(v, poi_id, **rev_edge_1)
                            
                            # POI -> U
                            rev_edge_2 = rev_edge_data.copy()
                            rev_edge_2['length'] = rev_orig_length * ratio_u
                            G.add_edge(poi_id, u, **rev_edge_2)
                            
                    count += 1
                except Exception as e:
                    pass # Bỏ qua nếu có lỗi hình học ở 1 điểm cụ thể
                
            print(f"   -> Đã chèn {count} địa điểm độc lập vào giữa các con đường!")
    except Exception as e:
        print("   -> Lỗi khi lấy POI:", e)

    # 3. CHUYỂN ĐỔI ĐỒ THỊ G ĐÃ CHỈNH SỬA THÀNH JSON
    print("3. Đang xuất đồ thị thành JSON...")
    dataset = {}
    
    for node_id, data in G.nodes(data=True):
        # Nếu là điểm POI đã có tên từ trước thì giữ nguyên
        if 'name' in data and 'type' in data:
            node_name = data['name']
            node_type = data['type']
        else:
            # Gom tên đường để tạo tên ngã tư
            street_names = set()
            for u, v, key, edge_data in G.edges(node_id, keys=True, data=True):
                if 'name' in edge_data:
                    name = edge_data['name']
                    if isinstance(name, list): street_names.add(name[0])
                    elif isinstance(name, str): street_names.add(name)
            
            street_list = list(street_names)
            if len(street_list) >= 2: node_name = f"Ngã giao {street_list[0]} - {street_list[1]}"
            elif len(street_list) == 1: node_name = f"Đường {street_list[0]}"
            else: node_name = f"Điểm nút {node_id}"
            node_type = "intersection"

        dataset[str(node_id)] = {
            "name": node_name,
            "lat": data['y'],
            "lng": data['x'],
            "type": node_type,
            "connected_to": []
        }

    # Xuất các cạnh và random rủi ro
    risk_options = ["none", "construction", "flooding", "complex_intersection", "narrow_road"]
    risk_weights = [60, 10, 10, 10, 10]
    
    for u, v, key, data in G.edges(keys=True, data=True):
        distance = round(data.get('length', 0), 2)
        direction = "one-way" if data.get('oneway', False) else "two-way"
        congestion = random.randint(1, 5)
        risk = random.choices(risk_options, weights=risk_weights, k=1)[0]
        
        base_speed = 400 
        actual_speed = base_speed / congestion 
        est_time = round((distance / actual_speed) * 60) if actual_speed > 0 else 999
        
        edge_info = {
            "target_node": str(v),
            "direction": direction,
            "risk_factors": risk,
            "congestion_level": congestion,
            "estimated_time": est_time,
            "distance": distance
        }
        dataset[str(u)]["connected_to"].append(edge_info)

    with open('hcm_traffic_data.json', 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=4)
        
    print("Hoàn tất! File dữ liệu mới là 'hcm_traffic_data.json'.")

if __name__ == "__main__":
    generate_traffic_dataset()