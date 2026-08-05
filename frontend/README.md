# Route Dashboard Frontend

Frontend của đồ án **Introduction to Artificial Intelligence**.

Ứng dụng mô phỏng hệ thống tìm đường thông minh trên bản đồ TP. Hồ Chí Minh, cho phép người dùng lựa chọn điểm bắt đầu, điểm kết thúc, thêm điểm dừng và gửi yêu cầu đến backend để tìm đường bằng các thuật toán AI.

---

## Features

### Interactive Map

- Hiển thị bản đồ TP. Hồ Chí Minh bằng OpenStreetMap.
- Hiển thị các node giao thông từ `nodes.json`.
- Giới hạn thao tác trong khu vực TP.HCM.
- Zoom và pan trên bản đồ.

### Route Selection

- Chọn Start bằng cách click node.
- Chọn End bằng cách click node.
- Hỗ trợ thêm nhiều điểm dừng (Waypoint).
- Đổi màu node:
  - 🟢 Start
  - 🔴 End
  - 🟠 Waypoint
  - 🔵 Normal Node

### Search Settings

Người dùng có thể lựa chọn:

- Optimization Method
  - Default
  - Time
  - Distance
  - Cost

- Search Algorithm
  - Depth-first Search (DFS)
  - (Chuẩn bị hỗ trợ BFS, UCS, A*)

### Visualization

- Hiển thị đường đi trả về từ backend.
- Chuẩn bị hỗ trợ từng bước (Step Visualization).

---

## Technologies

- React
- Vite
- TailwindCSS
- React Leaflet
- Leaflet
- OpenStreetMap

---

## Project Structure

```
frontend/
│
├── src/
│   ├── components/
│   │   ├── HCMMap.jsx
│   │   ├── Sidebar.jsx
│   │   └── ...
│   │
│   ├── data/
│   │   └── nodes.json
|   │   └── ...
│   │
│   ├── App.jsx
│   ├── index.css
│   └── index.jsx
│
├── Dockerfile
├── nginx.conf
├── package.json
└── vite.config.js
└── ...
```

---

## Installation
### Cách 1

Di chuyển vào thư mục frontend

```bash
cd frontend
```

Cài dependencies

```bash
npm install
```

Chạy development server

```bash
npm run dev
```

Frontend sẽ chạy tại

```
http://localhost:5173
```

---

Build

```bash
npm run build
```

Build output sẽ nằm trong

```
dist/
```

---
### Cách 2
- Docker

Build image
Từ root

```bash
docker compose build 
```

Run container

```bash
docker compose up
```

Truy cập

```
http://localhost:3000
```

---

## Backend Integration

Frontend được thiết kế để gọi REST API từ backend.

Ví dụ request:

```http
POST /search
```

Request Body

```json
{
    "start": "N01",
    "end": "N15",
    "stops": [
        "N08",
        "N12"
    ],
    "algorithm": "astar",
    "optimization": "distance"
}
```

Ví dụ Response

```json
{
    "path": [
        "N01",
        "N08",
        "N12",
        "N15"
    ],
    "distance": 1820,
    "time": 341
}
```

Frontend sẽ sử dụng trường `path` để hiển thị Polyline trên bản đồ.

---

## Current Status

- ✅ Display OpenStreetMap
- ✅ Display traffic nodes
- ✅ Select Start / End
- ✅ Add Waypoints
- ✅ Route visualization
- ✅ Search settings
- 🔄 Backend API integration
- 🔄 AI Algorithms (Backend)
- 🔄 Step-by-step visualization

---

## Future Improvements

- [ ] Display edge network
- [ ] Animate route traversal
- [ ] Step-by-step visualization
- [ ] Highlight visited nodes during search
- [ ] Loading indicator while searching
---
