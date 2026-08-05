import { useState, useCallback } from "react";

const API_BASE = "/api";

// Map tên thuật toán UI → API key
const ALGO_MAP = {
  "Depth-first Search": "dfs",
  "Breadth-first Search": "bfs",
  "Dijkstra's Algorithm": "dijkstra",
  "UCS": "ucs",
  "A* Search": "astar",
  "Greedy Best-First": "greedy",
};

// Map optimization UI → API key
const OPT_MAP = {
  "Default":  "default",
  "Time":     "time",
  "Distance": "distance",
  "Cost":     "cost",
};

/**
 * Hook quản lý state và logic gọi POST /api/search
 */
export function useSearch() {
  const [result, setResult] = useState(null);    // SearchResponse từ API
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const search = useCallback(async ({ startId, endId, algorithm, optimization }) => {
    if (!startId || !endId) {
      setError("Vui lòng chọn điểm đầu và điểm cuối");
      return false;
    }

    const algoKey = ALGO_MAP[algorithm] || "bfs";
    const optKey  = OPT_MAP[optimization] || "default";
    // A* và Greedy dùng heuristic dựa theo optimization
    const heuristic = optKey === "time" ? "time" : "distance";

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          start_id: startId,
          end_id: endId,
          algorithm: algoKey,
          optimization: optKey,
          heuristic,
        }),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: "Lỗi không xác định" }));
        throw new Error(detail.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      setResult(data);
      return true;
    } catch (err) {
      console.error("[useSearch]", err);
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setLoading(false);
  }, []);

  return { result, loading, error, search, reset };
}
