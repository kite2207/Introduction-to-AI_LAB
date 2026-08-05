import osmnx as ox
import random
import json
import networkx as nx

def generate_traffic_dataset():
    print("1. Đang tải dữ liệu mạng lưới đường từ OpenStreetMap...")
    
    places = ["Quận 5, Hồ Chí Minh, Việt Nam", "Quận 10, Hồ Chí Minh, Việt Nam"]
    cf = '["highway"~"primary|secondary|tertiary|trunk|primary_link|secondary_link|tertiary_link"]'
    
    G = ox.graph_from_place(places, custom_filter=cf, simplify=False, retain_all=False)
    
    for u, v, key, data in G.edges(keys=True, data=True):
        noisy_attributes = ['lanes', 'maxspeed', 'width', 'surface', 'name:en', 'ref']
        for attr in noisy_attributes:
            data.pop(attr, None)
                
    G = ox.simplify_graph(G)
    
    print("   -> Đang xử lý gom cụm vòng xoay và làm sạch ngã tư...")
    G_proj = ox.project_graph(G)
    G_cons = ox.consolidate_intersections(G_proj, rebuild_graph=True, tolerance=20, dead_ends=False)
    G = ox.project_graph(G_cons, to_crs="EPSG:4326")
    
    G.remove_nodes_from(list(nx.isolates(G)))
    
    largest_wcc = max(nx.weakly_connected_components(G), key=len)
    G = G.subgraph(largest_wcc).copy()

    print("2. Đang chuyển đổi dữ liệu, trích xuất hình học và gắn rủi ro...")
    dataset = {}
    
    for node_id, data in G.nodes(data=True):
        street_names = set()
        for u, v, key, edge_data in G.edges(node_id, keys=True, data=True):
            name = edge_data.get('name')
            if name:
                if isinstance(name, list): 
                    street_names.add(name[0])
                elif isinstance(name, str): 
                    street_names.add(name)
        
        street_list = list(street_names)
        if len(street_list) >= 2: 
            node_name = f"Ngã giao {street_list[0]} - {street_list[1]}"
        elif len(street_list) == 1: 
            node_name = f"Đường {street_list[0]}"
        else: 
            node_name = f"Điểm nút {node_id}"

        dataset[str(node_id)] = {
            "name": node_name,
            "lat": data['y'],
            "lng": data['x'],
            "type": "intersection",
            "connected_to": []
        }

    for u, v, key, data in G.edges(keys=True, data=True):
        u_str = str(u)
        v_str = str(v)
        
        distance = round(data.get('length', 0), 2)
        direction = "one-way" if data.get('oneway', False) else "two-way"
        congestion = random.randint(1, 5)
        
        base_speed = 400 
        actual_speed = base_speed / congestion 
        est_time = round((distance / actual_speed) * 60) if actual_speed > 0 else 999
        
        risks = []
        road_type = data.get('highway', '')
        if isinstance(road_type, list): 
            road_type = road_type[0]
            
        if road_type in ['tertiary', 'tertiary_link']:
            risks.append("narrow_road")
            
        if G.degree(u) >= 5 or G.degree(v) >= 5:
            risks.append("complex_intersection")
            
        if 'name' in data and any(street in str(data.get('name', '')) for street in ['3 Tháng 2', 'Lý Thường Kiệt']):
            risks.append("flooding")
        
        if road_type in ['primary', 'trunk'] and random.random() < 0.15:
            risks.append("construction")
        
        if not risks:
            risks.append("none")
            
        if 'geometry' in data:
            path_coords = [{"lat": y, "lng": x} for x, y in data['geometry'].coords]
        else:
            path_coords = [
                {"lat": G.nodes[u]['y'], "lng": G.nodes[u]['x']},
                {"lat": G.nodes[v]['y'], "lng": G.nodes[v]['x']}
            ]
            
        edge_info = {
            "target_node": v_str,
            "direction": direction,
            "risk_factors": risks,
            "congestion_level": congestion,
            "estimated_time": est_time,
            "distance": distance,
            "geometry": path_coords
        }
        dataset[u_str]["connected_to"].append(edge_info)
        
        if direction == "two-way":
            existing_targets = [edge['target_node'] for edge in dataset[v_str]["connected_to"]]
            if u_str not in existing_targets:
                reverse_edge = edge_info.copy()
                reverse_edge["target_node"] = u_str
                reverse_edge["geometry"] = list(reversed(path_coords))
                dataset[v_str]["connected_to"].append(reverse_edge)

    with open('hcm_traffic_data_final.json', 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=4)
        
    print("Hoàn tất! Cấu trúc dữ liệu master đã được lưu vào 'hcm_traffic_data_final.json'.")

if __name__ == "__main__":
    generate_traffic_dataset()