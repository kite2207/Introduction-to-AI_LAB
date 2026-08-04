import React from "react";
import RouteSettings from "./RouteSettings";
import RouteResults from "./RouteResults";

export default function Sidebar({
  start,
  end,
  addingStop,
  setAddingStop,
  waypoints,
  removeWaypoint,
  loading,
  optimization,
  setOptimization,
  algorithm,
  setAlgorithm,
  hasSearched,
  onSearch,
  step,
  totalSteps,
  onStepBack,
  onStepForward,
  onSkipToStart,
  onSkipToEnd,
  onReset,
}) {
  return (
    <aside
      className="
    w-[360px]
    min-w-[360px]
    h-screen
    overflow-y-auto
    bg-white
    p-5
    border-r
  "
    >
      <h1 className="text-xl font-bold text-gray-900 mb-6">Route Dashboard</h1>
      <div className="mb-5">
        <p>
          Start:
          <span className="text-green-600 ml-2">
            {start ?? "Bấm vào node để chọn điểm bắt đầu"}
          </span>
        </p>

        <p>
          End:
          <span className="text-red-600 ml-2">
            {start ?
            end ?? "Bấm vào node để chọn điểm tiếp theo" : ""
            }
          </span>
        </p>
        <h3 className="font-bold">Điểm dừng</h3>

        {waypoints.length === 0 ? (
          <p className="text-gray-400">Chưa có điểm dừng</p>
        ) : (
          waypoints.map((node, index) => (
            <div key={node} className="flex justify-between items-center">
              <span>
                📍 {index + 1}: {node}
              </span>

              <button
                onClick={() => removeWaypoint(node)}
                className="text-red-500"
              >
                ✕
              </button>
            </div>
          ))
        )}
      </div>
      <button
        onClick={() => setAddingStop(!addingStop)}
        className="w-full border rounded p-2 mt-3"
      >
        {addingStop
          ? "Bấm vào node trên bản đồ để thêm điểm dừng... (Bấm lại để hủy)"
          : "+ Thêm điểm dừng"}
      </button>

      <RouteSettings
        optimization={optimization}
        setOptimization={setOptimization}
        algorithm={algorithm}
        setAlgorithm={setAlgorithm}
      />

      {!hasSearched && <div className="flex-1" />}

      <button
        onClick={onSearch}
        disabled={hasSearched || loading || !start || !end}
        className={`w-full text-sm font-semibold rounded-md py-2.5 transition-colors ${
          hasSearched
            ? "bg-blue-100 text-blue-400 cursor-not-allowed"
            : "bg-blue-600 hover:bg-blue-700 text-white"
        }
        `}
      >
        {loading ? "Searching..." : hasSearched ? "Route Found" : "Search"}
      </button>

      <RouteResults
        hasSearched={hasSearched}
        step={step}
        totalSteps={totalSteps}
        optimization={optimization}
        algorithm={algorithm}
        onStepBack={onStepBack}
        onStepForward={onStepForward}
        onSkipToStart={onSkipToStart}
        onSkipToEnd={onSkipToEnd}
        onReset={onReset}
      />
    </aside>
  );
}
