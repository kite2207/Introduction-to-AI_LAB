import React, { useMemo } from "react";
import RouteSettings from "./RouteSettings";
import RouteResults from "./RouteResults";
import Select from "react-select";

export default function Sidebar({
  nodeMap,
  nodeOptions,
  start,
  end,
  setStart,
  setEnd,
  addingStop,
  setAddingStop,
  waypoints,
  setWaypoints,
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
        <div className="mb-4">
          <p className="font-semibold mb-1">Start</p>

          <Select
            options={nodeOptions}
            value={nodeOptions.find((option) => option.value === start) ?? null}
            onChange={(option) => {
              setStart(option?.value ?? null);
            }}
            placeholder="Chọn điểm bắt đầu"
            isSearchable
          />
        </div>

        <div className="mb-4">
          <p className="font-semibold mb-1">End</p>

          <Select
            options={nodeOptions}
            value={nodeOptions.find((option) => option.value === end) ?? null}
            onChange={(option) => {
              setEnd(option?.value ?? null);
            }}
            placeholder="Chọn điểm kết thúc"
            isSearchable
          />
        </div>
        <h3 className="font-bold">Điểm dừng</h3>

        {waypoints.length === 0 ? (
          <p className="text-gray-400">Chưa có điểm dừng</p>
        ) : (
          waypoints.map((node, index) => (
            <div key={node} className="flex justify-between items-center">
              <span>
                📍 {index + 1}: {nodeMap[node]?.name ?? node}
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
        {addingStop ? "Hủy thêm điểm dừng" : "+ Thêm điểm dừng"}
      </button>

      {addingStop && (
        <div className="mt-3">
          <Select
            options={nodeOptions.filter(
              (option) =>
                option.value !== start &&
                option.value !== end &&
                !waypoints.includes(option.value),
            )}
            placeholder="Chọn điểm dừng..."
            isSearchable
            onChange={(option) => {
              if (!option) return;

              setWaypoints((prev) => [...prev, option.value]);

              // Ẩn select
              setAddingStop(false);
            }}
          />
        </div>
      )}

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
