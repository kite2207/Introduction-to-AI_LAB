# HCM Route Finding Lab

Ứng dụng minh họa các thuật toán tìm kiếm đường đi trên dữ liệu giao thông
TP.HCM. FastAPI cung cấp đồ thị và thực thi thuật toán; React/Vite hiển thị
bản đồ, quá trình duyệt và giải thích kết quả.

## Thành phần

- `backend/`: API FastAPI và phần giải thích kết quả.
- `src/algorithms/`: BFS, DFS, UCS, Dijkstra, A* và Greedy Best-First.
- `src/models.py`: mô hình đồ thị, kiểm tra dữ liệu và hàm chi phí.
- `data/hcm_traffic_data.json`: nguồn dữ liệu đồ thị duy nhất.
- `frontend/`: giao diện React, lấy đồ thị qua `GET /api/graph`.
- `Report/`: mã nguồn và bản báo cáo LaTeX.

## Yêu cầu

- Python 3.11 trở lên.
- Node.js 20 trở lên.
- Docker và Docker Compose nếu chạy bằng container.

## Chạy local

Tại thư mục gốc, cài dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Sau đó chạy ứng dụng (lệnh này tự khởi động cả backend và frontend):

```powershell
cd frontend
npm ci
npm run dev
```

Mở `http://localhost:5173`. Vite tự chuyển tiếp `/api/*` tới backend tại
`http://127.0.0.1:8000`. Nhấn `Ctrl+C` để dừng cả hai tiến trình.

Nếu chỉ muốn chạy frontend và đã tự khởi động backend riêng, dùng
`npm run dev:frontend`.

Để dùng backend khác, sao chép `frontend/.env.example` thành `frontend/.env`
và thay `VITE_API_BASE_URL`.

## Chạy bằng Docker

```powershell
docker compose up --build
```

Mở `http://localhost:3000`. Nginx phục vụ frontend và chuyển các request
`/api/*` sang container backend.

## API chính

- `GET /`: trạng thái backend.
- `GET /api/graph`: toàn bộ node, cạnh và geometry dành cho frontend.
- `GET /api/graph/info`: số lượng node và cạnh.
- `GET /api/nodes`, `GET /api/edges`: danh sách thành phần đồ thị.
- `POST /api/search`: tìm đường và trả về trace mô phỏng.

Ví dụ request tìm đường:

```json
{
  "start": "0",
  "end": "10",
  "algorithm": "astar",
  "optimization": "mixed"
}
```

`optimization` nhận `distance`, `time` hoặc `mixed`. Chi phí `mixed` kết hợp
khoảng cách hiệu dụng và thời gian hiệu dụng, trong đó thời gian được quy đổi
theo 10 mét cho mỗi giây trước khi lấy trung bình.

## Kiểm tra và build

Kiểm tra backend có thể nạp dữ liệu:

```powershell
python -c "import backend.api; print('Backend OK')"
```

Build frontend production:

```powershell
cd frontend
npm ci
npm run build
```

Các script kiểm thử thuật toán cũ trong repository chưa phải test suite tự
động hoàn chỉnh; cần bổ sung assertion và thống nhất chúng với dữ liệu
`hcm_traffic_data.json` trước khi dùng làm kiểm tra regression.

## Tính chất thuật toán

- BFS tối ưu theo số cạnh, không đảm bảo tối ưu theo quãng đường hoặc thời gian.
- DFS và Greedy không đảm bảo đường tối ưu.
- UCS/Dijkstra tối ưu khi mọi chi phí cạnh không âm.
- A* tối ưu khi heuristic admissible và consistent với hàm chi phí đang dùng.
