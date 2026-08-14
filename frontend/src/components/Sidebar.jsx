import React, { useMemo } from "react";
import RouteSettings from "./RouteSettings";
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
  routeExplanation,
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

      <div className="mt-6 pt-5 border-t border-gray-200">
        <RouteSettings
          optimization={optimization}
          setOptimization={setOptimization}
          algorithm={algorithm}
          setAlgorithm={setAlgorithm}
        />
      </div>

      {!hasSearched && <div className="flex-1" />}

      <div className="mt-6 pt-5 border-t border-gray-200 space-y-3">
        <button
          onClick={onSearch}
          disabled={hasSearched || loading || !start || !end}
          className={`w-full h-10 text-sm font-semibold rounded-md transition-colors ${
            hasSearched
              ? "bg-blue-100 text-blue-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 text-white"
          }
      `}
        >
          {loading ? "Searching..." : hasSearched ? "Route Found" : "Search"}
        </button>

        {hasSearched && (
          <>
            <div className="mt-6 pt-5 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-900 mb-3">
                Visualizer
              </h3>

              <div className="flex items-center justify-between rounded-md border border-gray-200 bg-white px-3 py-2">
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={onSkipToStart}
                    disabled={step <= 0}
                    title="First step"
                    className="h-10 min-w-10 px-1 rounded border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-35 flex flex-col items-center justify-center leading-none"
                  >
                    <span className="text-sm">|◀</span>
                    <span className="text-[8px] mt-0.5">First</span>
                  </button>

                  <button
                    type="button"
                    onClick={onStepBack}
                    disabled={step <= 0}
                    title="Previous step"
                    className="h-10 w-9 rounded border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-35 flex flex-col items-center justify-center leading-none"
                  >
                    <span className="text-base">‹</span>
                    <span className="text-[8px] mt-0.5">Prev</span>
                  </button>

                  <button
                    type="button"
                    onClick={onStepForward}
                    disabled={step >= totalSteps}
                    title="Next step"
                    className="h-10 w-9 rounded border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-35 flex flex-col items-center justify-center leading-none"
                  >
                    <span className="text-base">›</span>
                    <span className="text-[8px] mt-0.5">Next</span>
                  </button>

                  <button
                    type="button"
                    onClick={onSkipToEnd}
                    disabled={step >= totalSteps}
                    title="Last step"
                    className="h-10 min-w-10 px-1 rounded border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-35 flex flex-col items-center justify-center leading-none"
                  >
                    <span className="text-sm">▶|</span>
                    <span className="text-[8px] mt-0.5">Last</span>
                  </button>
                </div>

                <span className="text-xs text-gray-500 whitespace-nowrap">
                  Step {step} / {totalSteps}
                </span>
              </div>
            </div>

            {routeExplanation && (
              <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <div className="h-7 w-7 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-semibold">
                    ?
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-blue-900">
                      Why this route?
                    </h3>
                    <p className="text-[10px] text-blue-600 mt-0.5">
                      Route explanation
                    </p>
                  </div>
                </div>

                <div className="space-y-3 text-[11px] leading-5 text-blue-900">
                  <div>
                    <div className="font-semibold mb-1">Why selected</div>
                    <div className="text-blue-800">
                      {routeExplanation.why_selected}
                    </div>
                  </div>

                  <div>
                    <div className="font-semibold mb-1">Optimization</div>
                    <div className="text-blue-800">
                      {routeExplanation.headline}
                    </div>
                  </div>

                  <div className="border-t border-blue-200 pt-3">
                    <div className="font-semibold mb-2">
                      Optimality reference
                    </div>

                    <div className="rounded-md bg-white/70 border border-blue-100 p-2.5 space-y-2">
                      <div className="font-medium text-blue-900">
                        Dijkstra ·{" "}
                        {routeExplanation.optimality_reference?.optimization}
                      </div>

                      <div>
                        <div className="text-[10px] text-blue-600">
                          Reference route
                        </div>
                        <div className="text-blue-900 leading-4 break-words">
                          {(
                            routeExplanation.optimality_reference
                              ?.route_names || []
                          ).join(" → ")}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[10px]">
                        <span className="text-blue-600">Cost</span>
                        <span className="text-right font-medium">
                          {routeExplanation.optimality_reference?.cost == null
                            ? "—"
                            : Number(
                                routeExplanation.optimality_reference.cost,
                              ).toFixed(2)}
                        </span>
                        <span className="text-blue-600">Distance</span>
                        <span className="text-right font-medium">
                          {routeExplanation.optimality_reference?.distance ==
                          null
                            ? "—"
                            : `${Number(routeExplanation.optimality_reference.distance).toFixed(0)} m`}
                        </span>
                        <span className="text-blue-600">Time</span>
                        <span className="text-right font-medium">
                          {routeExplanation.optimality_reference?.time == null
                            ? "—"
                            : `${Number(routeExplanation.optimality_reference.time).toFixed(1)} s`}
                        </span>
                      </div>

                      <div className="pt-2 border-t border-blue-100 font-semibold text-blue-900">
                        {routeExplanation.optimality_reference
                          ?.same_cost_as_selected
                          ? "Same objective cost as the Dijkstra reference."
                          : "Different from the Dijkstra reference."}
                      </div>
                    </div>

                    <div className="mt-2 text-blue-800">
                      {routeExplanation.optimality}
                    </div>
                  </div>

                  <div className="border-t border-blue-200 pt-3">
                    <div className="font-semibold mb-2">Route alternatives</div>

                    <div className="space-y-2">
                      {[
                        [
                          "Selected route",
                          routeExplanation.route_comparison?.selected,
                        ],
                        [
                          "Shortest-distance route",
                          routeExplanation.route_comparison?.shortest_distance,
                        ],
                        [
                          "Fastest-time route",
                          routeExplanation.route_comparison?.fastest_time,
                        ],
                      ].map(([label, route]) =>
                        route ? (
                          <div
                            key={label}
                            className="rounded-md bg-white/70 border border-blue-100 p-2.5"
                          >
                            <div className="text-[10px] font-semibold text-blue-600 mb-1">
                              {label}
                            </div>

                            <div className="text-blue-900 leading-4 break-words">
                              {(route.route_names || []).join(" → ")}
                            </div>

                            <div className="grid grid-cols-3 gap-1 mt-2 text-[10px]">
                              <div>
                                <div className="text-blue-600">Distance</div>
                                <div className="font-medium">
                                  {Number(route.distance || 0).toFixed(0)} m
                                </div>
                              </div>
                              <div>
                                <div className="text-blue-600">Time</div>
                                <div className="font-medium">
                                  {Number(route.time || 0).toFixed(1)} s
                                </div>
                              </div>
                              <div>
                                <div className="text-blue-600">Cost</div>
                                <div className="font-medium">
                                  {route.cost == null
                                    ? "—"
                                    : Number(route.cost).toFixed(2)}
                                </div>
                              </div>
                            </div>

                            {label !== "Selected route" && (
                              <div className="mt-2 pt-2 border-t border-blue-100 grid grid-cols-3 gap-1 text-[9px]">
                                <div>
                                  <div className="text-blue-600">
                                    Δ distance
                                  </div>
                                  <div>
                                    {Number(
                                      route.distance_difference || 0,
                                    ).toFixed(0)}{" "}
                                    m
                                  </div>
                                </div>
                                <div>
                                  <div className="text-blue-600">Δ time</div>
                                  <div>
                                    {Number(route.time_difference || 0).toFixed(
                                      1,
                                    )}{" "}
                                    s
                                  </div>
                                </div>
                                <div>
                                  <div className="text-blue-600">Δ cost</div>
                                  <div>
                                    {route.cost_difference == null
                                      ? "—"
                                      : Number(route.cost_difference).toFixed(
                                          2,
                                        )}
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        ) : null,
                      )}
                    </div>
                  </div>

                  {routeExplanation.congested_segments?.length > 0 && (
                    <div className="border-t border-blue-200 pt-3">
                      <div className="font-semibold mb-2">High congestion</div>

                      <div className="space-y-1.5">
                        {routeExplanation.congested_segments
                          .slice(0, 5)
                          .map((segment, index) => (
                            <div
                              key={`${segment.from}-${segment.to}-${index}`}
                              className="rounded bg-white/70 px-2.5 py-2 border border-blue-100"
                            >
                              <div className="font-medium text-blue-900">
                                {segment.from} → {segment.to}
                              </div>
                              <div className="text-[10px] text-blue-700">
                                Congestion {segment.congestion}
                                {segment.risk && segment.risk !== "none"
                                  ? ` · ${segment.risk}`
                                  : ""}
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  <div className="pt-1 text-[10px] text-blue-600 leading-4">
                    {routeExplanation.comparison_note}
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        <div className="mt-5 pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={onReset}
            className="w-full h-10 rounded-md border border-gray-300 bg-white text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Reset
          </button>
        </div>
      </div>
    </aside>
  );
}
