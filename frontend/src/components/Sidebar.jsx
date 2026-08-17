import React, { useMemo } from "react";
import RouteSettings from "./RouteSettings";
import Select from "react-select";
import {
  Navigation,
  Search,
  RotateCcw,
  MapPin,
  Flag,
  Plus,
  X,
  Compass,
  Lightbulb,
} from "lucide-react";

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
    border-[#363236]/10
  "
    >
      <div className="rounded-2xl bg-[#F7B558] p-4 mb-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-[#A5D48C] flex items-center justify-center">
            <Compass className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold leading-tight text-[#363236]">
              Bảng điều khiển tuyến đường
            </h1>
            <p className="text-[11px] text-[#363236]/70">AI Tìm đường TP.HCM</p>
          </div>
        </div>
      </div>

      <div className="mb-5">
        <div className="mb-4">
          <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-[#363236] mb-1.5">
            <MapPin className="h-3.5 w-3.5 text-[#A5D48C]" />
            Điểm bắt đầu
          </p>

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
          <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-[#363236] mb-1.5">
            <Flag className="h-3.5 w-3.5 text-[#F7B558]" />
            Điểm kết thúc
          </p>

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
        <h3 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-[#363236] mb-1.5">
          <Navigation className="h-3.5 w-3.5 text-[#A5D48C]" />
          Điểm dừng
        </h3>

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
        className={`w-full flex items-center justify-center gap-1.5 rounded-lg border-2 py-2 mt-3 text-sm font-medium transition-colors ${
          addingStop
            ? "border-[#F7B558] bg-[#F7B558]/15 text-[#363236]"
            : "border-[#A5D48C] bg-[#A5D48C]/15 text-[#363236] hover:bg-[#A5D48C]/30"
        }`}
      >
        {addingStop ? (
          <>
            <X className="h-3.5 w-3.5" /> Hủy thêm điểm dừng
          </>
        ) : (
          <>
            <Plus className="h-3.5 w-3.5" /> Thêm điểm dừng
          </>
        )}
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
          className={`w-full h-11 text-sm font-semibold rounded-lg flex items-center justify-center gap-2 transition-all ${
            hasSearched
              ? "bg-[#A5D48C]/40 text-[#363236]/50 cursor-not-allowed"
              : "bg-[#F7B558] hover:bg-[#e2a244] text-[#363236] shadow-sm"
          }`}
        >
          {loading ? (
            "Đang tìm kiếm..."
          ) : (
            <>
              <Search className="h-4 w-4" />
              {hasSearched ? "Đã tìm thấy tuyến" : "Tìm kiếm"}
            </>
          )}
        </button>

        {/* Reset: directly under Search, above the explanation */}
        <button
          type="button"
          onClick={onReset}
          className="w-full h-10 rounded-lg border-2 border-[#363236]/20 bg-white text-sm font-semibold text-[#363236] hover:bg-[#F7B558]/10 transition-colors flex items-center justify-center gap-1.5"
        >
          <RotateCcw className="h-3.5 w-3.5 text-[#363236]/60" />
          Đặt lại
        </button>

        {hasSearched && (
          <>
            <div className="mt-6 pt-5 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-900 mb-3">
                Trình mô phỏng
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
                    <span className="text-[8px] mt-0.5">Đầu</span>
                  </button>

                  <button
                    type="button"
                    onClick={onStepBack}
                    disabled={step <= 0}
                    title="Previous step"
                    className="h-10 w-9 rounded border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-35 flex flex-col items-center justify-center leading-none"
                  >
                    <span className="text-base">‹</span>
                    <span className="text-[8px] mt-0.5">Trước</span>
                  </button>

                  <button
                    type="button"
                    onClick={onStepForward}
                    disabled={step >= totalSteps}
                    title="Next step"
                    className="h-10 w-9 rounded border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-35 flex flex-col items-center justify-center leading-none"
                  >
                    <span className="text-base">›</span>
                    <span className="text-[8px] mt-0.5">Sau</span>
                  </button>

                  <button
                    type="button"
                    onClick={onSkipToEnd}
                    disabled={step >= totalSteps}
                    title="Last step"
                    className="h-10 min-w-10 px-1 rounded border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-35 flex flex-col items-center justify-center leading-none"
                  >
                    <span className="text-sm">▶|</span>
                    <span className="text-[8px] mt-0.5">Cuối</span>
                  </button>
                </div>

                <span className="text-xs text-gray-500 whitespace-nowrap">
                  Bước {step} / {totalSteps}
                </span>
              </div>
            </div>

            {routeExplanation && (
              <div className="mt-4 rounded-2xl border border-[#363236]/10 bg-white p-4 shadow-sm">
                <div className="flex items-center gap-2.5 mb-3">
                  <div className="h-8 w-8 rounded-xl bg-[#A5D48C] text-[#363236] flex items-center justify-center">
                    <Lightbulb className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[#363236]">
                      Vì sao tuyến đường này?
                    </h3>
                    <p className="text-[10px] text-[#363236]/60 mt-0.5">
                      Giải thích tuyến đường
                    </p>
                  </div>
                </div>

                <div className="space-y-3 text-[11px] leading-5 text-[#363236]">
                  <div>
                    <div className="font-semibold mb-1">Lý do chọn</div>
                    <div className="bg-[#A5D48C]/15 border border-[#A5D48C]/50 p-2.5 rounded-md text-[#363236]/80">
                      {routeExplanation.why_selected}
                    </div>
                  </div>

                  {routeExplanation.legs?.length > 0 && (
                    <div>
                      <div className="font-semibold mb-2">
                        Chi tiết từng chặng
                      </div>

                      <div className="space-y-2">
                        {routeExplanation.legs.map((leg) => (
                          <div
                            key={leg.index}
                            className="rounded-md bg-[#F7B558]/10 border border-[#F7B558]/40 p-2.5"
                          >
                            <div className="flex items-center justify-between gap-2 mb-1">
                              <span className="text-[10px] font-semibold text-[#363236]">
                                Chặng {leg.index}: {leg.from} → {leg.to}
                              </span>
                              <span className="text-[10px] text-[#363236]/60">
                                {leg.algorithm_name}
                              </span>
                            </div>

                            <div className="text-[#363236] leading-4 break-words">
                              {(leg.route_names || []).join(" → ")}
                            </div>

                            <div className="grid grid-cols-3 gap-1 mt-2 text-[10px]">
                              <div>
                                <div className="text-[#363236]/60">
                                  Khoảng cách
                                </div>
                                <div className="font-medium">
                                  {Number(leg.distance || 0).toFixed(0)} m
                                </div>
                              </div>
                              <div>
                                <div className="text-[#363236]/60">
                                  Thời gian
                                </div>
                                <div className="font-medium">
                                  {Number(leg.time || 0).toFixed(1)} s
                                </div>
                              </div>
                              <div>
                                <div className="text-[#363236]/60">Chi phí</div>
                                <div className="font-medium">
                                  {leg.cost == null
                                    ? "—"
                                    : Number(leg.cost).toFixed(2)}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div>
                    <div className="font-semibold mb-1">Tối ưu hóa</div>
                    <div className="text-[#363236]/80">
                      {routeExplanation.headline}
                    </div>
                  </div>

                  {routeExplanation.optimality_reference && (
                    <div className="border-t border-[#363236]/10 pt-3">
                      <div className="font-semibold mb-2">
                        Tham chiếu tối ưu
                      </div>

                      <div className="rounded-md bg-[#F7B558]/10 border border-[#F7B558]/40 p-2.5 space-y-2">
                        <div className="font-medium text-[#363236]">
                          Dijkstra ·{" "}
                          {routeExplanation.optimality_reference.optimization}
                        </div>

                        <div>
                          <div className="text-[10px] text-[#363236]/60">
                            Tuyến tham chiếu
                          </div>
                          <div className="text-[#363236] leading-4 break-words">
                            {(
                              routeExplanation.optimality_reference
                                .route_names || []
                            ).join(" → ")}
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[10px]">
                          <span className="text-[#363236]/60">Chi phí</span>
                          <span className="text-right font-medium">
                            {routeExplanation.optimality_reference.cost == null
                              ? "—"
                              : Number(
                                  routeExplanation.optimality_reference.cost,
                                ).toFixed(2)}
                          </span>
                          <span className="text-[#363236]/60">Khoảng cách</span>
                          <span className="text-right font-medium">
                            {routeExplanation.optimality_reference.distance ==
                            null
                              ? "—"
                              : `${Number(routeExplanation.optimality_reference.distance).toFixed(0)} m`}
                          </span>
                          <span className="text-[#363236]/60">Thời gian</span>
                          <span className="text-right font-medium">
                            {routeExplanation.optimality_reference.time == null
                              ? "—"
                              : `${Number(routeExplanation.optimality_reference.time).toFixed(1)} s`}
                          </span>
                        </div>

                        <div className="pt-2 border-t border-[#F7B558]/30 font-semibold text-[#363236]">
                          {routeExplanation.optimality_reference
                            .same_cost_as_selected
                            ? "Cùng chi phí mục tiêu với tham chiếu Dijkstra."
                            : "Khác với tham chiếu Dijkstra."}
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="border-t border-[#363236]/10 pt-3">
                    <div className="font-semibold mb-1">Tính tối ưu</div>
                    <div className="text-[#363236]/80">
                      {routeExplanation.optimality}
                    </div>
                  </div>

                  {routeExplanation.route_comparison && (
                    <div className="border-t border-[#363236]/10 pt-3">
                      <div className="font-semibold mb-2">
                        Phương án thay thế
                      </div>

                      <div className="space-y-2">
                        {[
                          [
                            "Tuyến đã chọn",
                            routeExplanation.route_comparison?.selected,
                          ],
                          [
                            "Tuyến ngắn nhất",
                            routeExplanation.route_comparison
                              ?.shortest_distance,
                          ],
                          [
                            "Tuyến nhanh nhất",
                            routeExplanation.route_comparison?.fastest_time,
                          ],
                        ].map(([label, route]) =>
                          route ? (
                            <div
                              key={label}
                              className="rounded-md bg-white border border-[#363236]/10 p-2.5"
                            >
                              <div className="text-[10px] font-semibold text-[#363236]/60 mb-1">
                                {label}
                              </div>

                              <div className="text-[#363236] leading-4 break-words">
                                {(route.route_names || []).join(" → ")}
                              </div>

                              <div className="grid grid-cols-3 gap-1 mt-2 text-[10px]">
                                <div>
                                  <div className="text-[#363236]/60">
                                    Khoảng cách
                                  </div>
                                  <div className="font-medium">
                                    {Number(route.distance || 0).toFixed(0)} m
                                  </div>
                                </div>
                                <div>
                                  <div className="text-[#363236]/60">
                                    Thời gian
                                  </div>
                                  <div className="font-medium">
                                    {Number(route.time || 0).toFixed(1)} s
                                  </div>
                                </div>
                                <div>
                                  <div className="text-[#363236]/60">Chi phí</div>
                                  <div className="font-medium">
                                    {route.cost == null
                                      ? "—"
                                      : Number(route.cost).toFixed(2)}
                                  </div>
                                </div>
                              </div>

                              {label !== "Tuyến đã chọn" && (
                                <div className="mt-2 pt-2 border-t border-[#363236]/10 grid grid-cols-3 gap-1 text-[9px]">
                                  <div>
                                    <div className="text-[#363236]/60">
                                      Δ khoảng cách
                                    </div>
                                    <div>
                                      {Number(
                                        route.distance_difference || 0,
                                      ).toFixed(0)}{" "}
                                      m
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-[#363236]/60">
                                      Δ thời gian
                                    </div>
                                    <div>
                                      {Number(
                                        route.time_difference || 0,
                                      ).toFixed(1)}{" "}
                                      s
                                    </div>
                                  </div>
                                  <div>
                                    <div className="text-[#363236]/60">
                                      Δ chi phí
                                    </div>
                                    <div>
                                      {route.cost_difference == null
                                        ? "—"
                                        : Number(
                                            route.cost_difference,
                                          ).toFixed(2)}
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          ) : null,
                        )}
                      </div>
                    </div>
                  )}

                  {routeExplanation.congested_segments?.length > 0 && (
                    <div className="border-t border-[#363236]/10 pt-3">
                      <div className="font-semibold mb-2">
                        Kẹt xe nghiêm trọng
                      </div>

                      <div className="space-y-1.5">
                        {routeExplanation.congested_segments
                          .slice(0, 5)
                          .map((segment, index) => (
                            <div
                              key={`${segment.from}-${segment.to}-${index}`}
                              className="rounded bg-[#F7B558]/10 px-2.5 py-2 border border-[#F7B558]/30"
                            >
                              <div className="font-medium text-[#363236]">
                                {segment.from} → {segment.to}
                              </div>
                              <div className="text-[10px] text-[#363236]/70">
                                Kẹt xe {segment.congestion}
                                {segment.risk && segment.risk !== "none"
                                  ? ` · ${segment.risk}`
                                  : ""}
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  <div className="pt-1 text-[10px] text-[#363236]/60 leading-4">
                    {routeExplanation.comparison_note}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </aside>
  );
}
