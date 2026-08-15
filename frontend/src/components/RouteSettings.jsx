import React from "react";

const ALGORITHM_OPTIONS = [
  {
    value: "bfs",
    label: "Tìm kiếm theo chiều rộng (BFS)",
  },
  {
    value: "dfs",
    label: "Tìm kiếm theo chiều sâu (DFS)",
  },
  {
    value: "ucs",
    label: "Tìm kiếm chi phí đồng nhất (UCS)",
  },
  {
    value: "dijkstra",
    label: "Thuật toán Dijkstra",
  },
  {
    value: "astar",
    label: "Tìm kiếm A*",
  },
  {
    value: "greedy",
    label: "Tìm kiếm tham lam (Greedy Best-first)",
  },
];

const OPTIMIZATION_OPTIONS = [
  {
    value: "time",
    label: "Thời gian",
  },
  {
    value: "distance",
    label: "Khoảng cách",
  },
  {
    value: "mixed",
    label: "Kết hợp",
  },
];

export default function RouteSettings({
  optimization,
  setOptimization,
  algorithm,
  setAlgorithm,
}) {
  return (
    <div className="mt-5">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-[#363236] mb-3">
        Cài đặt
      </h3>

      <div className="mb-4">
        <label className="block text-xs text-gray-500 mb-1">
          Phương pháp tối ưu
        </label>

        <div className="flex border-2 border-[#363236]/15 rounded-md overflow-hidden">
          {OPTIMIZATION_OPTIONS.map((option, index) => {
            const active = optimization === option.value;

            return (
              <button
                key={option.value}
                type="button"
                onClick={() => setOptimization(option.value)}
                className={`flex-1 py-2 text-xs transition-colors ${
                  active
                    ? "bg-[#F7B558] text-[#363236] font-medium"
                    : "bg-white text-[#363236]/70 hover:bg-[#A5D48C]/15"
                } ${index > 0 ? "border-l-2 border-[#363236]/10" : ""}`}
              >
                {active && <span className="mr-1">✓</span>}
                {option.label}
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <label className="block text-xs text-gray-500 mb-1">Thuật toán</label>

        <select
          value={algorithm}
          onChange={(event) => setAlgorithm(event.target.value)}
          className="
            w-full
            h-10
            rounded-md
            border-2
            border-[#363236]/15
            bg-white
            px-3
            text-sm
            text-[#363236]
            outline-none
            focus:border-[#F7B558]
            focus:ring-2
            focus:ring-[#F7B558]/30
          "
        >
          {ALGORITHM_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

export { ALGORITHM_OPTIONS, OPTIMIZATION_OPTIONS };
