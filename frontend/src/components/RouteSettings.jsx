import React from "react";

const ALGORITHM_OPTIONS = [
  {
    value: "bfs",
    label: "Breadth-first Search",
  },
  {
    value: "dfs",
    label: "Depth-first Search",
  },
  {
    value: "ucs",
    label: "Uniform-cost Search",
  },
  {
    value: "dijkstra",
    label: "Dijkstra's Algorithm",
  },
  {
    value: "astar",
    label: "A* Search",
  },
  {
    value: "greedy",
    label: "Greedy Best-first Search",
  },
];

const OPTIMIZATION_OPTIONS = [
  {
    value: "default",
    label: "Default",
  },
  {
    value: "time",
    label: "Time",
  },
  {
    value: "distance",
    label: "Distance",
  },
  {
    value: "mixed",
    label: "Mixed",
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
      <h3 className="font-semibold text-gray-900 mb-3">Settings</h3>

      <div className="mb-4">
        <label className="block text-xs text-gray-500 mb-1">
          Optimization Method
        </label>

        <div className="flex border border-gray-300 rounded-md overflow-hidden">
          {OPTIMIZATION_OPTIONS.map((option, index) => {
            const active = optimization === option.value;

            return (
              <button
                key={option.value}
                type="button"
                onClick={() => setOptimization(option.value)}
                className={`flex-1 py-2 text-xs transition-colors ${
                  active
                    ? "bg-gray-100 text-gray-900 font-medium"
                    : "bg-white text-gray-500 hover:bg-gray-50"
                } ${index > 0 ? "border-l border-gray-300" : ""}`}
              >
                {active && <span className="mr-1">✓</span>}
                {option.label}
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <label className="block text-xs text-gray-500 mb-1">Algorithm</label>

        <select
          value={algorithm}
          onChange={(event) => setAlgorithm(event.target.value)}
          className="
            w-full
            h-10
            rounded-md
            border
            border-gray-300
            bg-white
            px-3
            text-sm
            text-gray-700
            outline-none
            focus:border-blue-500
            focus:ring-1
            focus:ring-blue-500
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
