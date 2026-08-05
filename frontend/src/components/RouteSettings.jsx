import React from "react";
import { Check, ChevronDown } from "lucide-react";

const OPTIMIZATION_OPTIONS = [
  { label: "Default", value: "default" },
  { label: "Time", value: "time" },
  { label: "Distance", value: "distance" },
  { label: "Cost", value: "cost" },
];

export default function RouteSettings({ optimization, setOptimization, algorithm, setAlgorithm }) {
  return (
    <section>
      <h2 className="text-sm font-semibold text-gray-900 mb-3">Settings</h2>

      <div className="mb-4">
        <label className="block text-xs text-gray-500 mb-1.5">Optimization Method</label>
        <div className="flex rounded-md border border-gray-300 overflow-hidden text-xs">
          {OPTIMIZATION_OPTIONS.map((option, idx) => {
            const isActive = optimization === option.value;
            console.log("optimization =", optimization);
            return (
              <button
                key={option.value}
                onClick={() => setOptimization(option.value)}
                className={`flex-1 flex items-center justify-center gap-1 py-1.5 px-1.5 transition-colors ${
                  isActive
                    ? "bg-gray-100 text-gray-900 font-medium"
                    : "bg-white text-gray-500 hover:bg-gray-50"
                } ${idx !== 0 ? "border-l border-gray-300" : ""}`}
              >
                {isActive && <Check className="w-3 h-3" />}
                {option.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-xs text-gray-500 mb-1.5">Algorithm</label>
        <div className="relative">
          <select
            value={algorithm}
            onChange={(e) => setAlgorithm(e.target.value)}
            className="w-full appearance-none rounded-md border border-blue-400 ring-1 ring-blue-100 px-3 py-2 pr-8 text-sm text-gray-700 outline-none bg-white cursor-pointer"
          >
            <option>Depth-first Search</option>
            <option>Breadth-first Search</option>
            <option>Dijkstra's Algorithm</option>
            <option>A* Search</option>
          </select>
          <ChevronDown className="w-4 h-4 text-gray-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      </div>
    </section>
  );
}
