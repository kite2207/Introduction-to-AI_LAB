import React from "react";
import {
  Compass,
  MapPin,
  Timer,
  Wallet,
  Radar,
  GitBranch,
  CircleDot,
  Lightbulb,
} from "lucide-react";

function formatDistance(value) {
  if (value == null) return "—";
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  return Math.abs(n) >= 1000
    ? `${(n / 1000).toFixed(2)} km`
    : `${n.toFixed(0)} m`;
}

function formatTime(value) {
  if (value == null) return "—";
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  return n >= 60 ? `${(n / 60).toFixed(1)} min` : `${n.toFixed(0)} s`;
}

function formatNumber(value) {
  if (value == null) return "—";
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  return n.toFixed(2);
}

function getAlgorithmKind(algorithm = "", algorithmName = "") {
  const raw = `${algorithm} ${algorithmName}`.toLowerCase();

  if (
    raw.includes("dijkstra") ||
    raw.includes("uniform") ||
    raw.includes("ucs")
  )
    return "ucs";

  if (raw.includes("a*") || raw.includes("astar")) return "astar";

  if (raw.includes("greedy")) return "greedy";

  if (raw.includes("breadth") || raw.includes("bfs")) return "bfs";

  if (raw.includes("depth") || raw.includes("dfs")) return "dfs";

  return "unknown";
}

function CandidateComparison({
  candidates,
  kind,
  nextSelected,
  selectionMetric,
}) {
  const metricLabel =
    {
      ucs: "g(n)",
      astar: "f(n)",
      greedy: "h(n)",
      bfs: "FIFO",
      dfs: "LIFO",
    }[kind] ||
    selectionMetric ||
    "priority";

  if (!candidates?.length) {
    return (
      <div className="text-xs text-gray-400 py-2">
        Không còn node chưa đi qua.
      </div>
    );
  }

  return (
    <div className="space-y-2 max-h-64 overflow-y-auto">
      <div className="text-[10px] text-gray-400">Chọn theo {metricLabel}</div>

      {candidates.map((candidate, index) => {
        const isNext =
          nextSelected != null &&
          String(candidate.node_id) === String(nextSelected);

        return (
          <div
            key={`${candidate.node_id}-${index}`}
            className={`rounded-md border p-2 ${
              isNext
                ? "border-[#A5D48C] bg-[#A5D48C]/15"
                : "border-[#363236]/10 bg-[#F7B558]/5"
            }`}
          >
            <div className="flex justify-between gap-2">
              <span className="text-xs font-semibold text-[#363236]">
                → {candidate.node_id}
              </span>

              {isNext && (
                <span className="text-[10px] font-bold text-[#A5D48C]">
                  TIẾP
                </span>
              )}
            </div>

            {kind === "bfs" || kind === "dfs" ? (
              <div className="mt-1 text-[10px] text-gray-500">
                {kind === "bfs"
                  ? `Vị trí hàng đợi: ${index + 1}`
                  : `Vị trí ngăn xếp: ${index + 1}`}
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-x-3 gap-y-1 mt-1.5 text-[11px]">
                <span className="text-gray-500">g(n)</span>
                <span className="text-right">{formatNumber(candidate.g)}</span>

                {(kind === "astar" || kind === "greedy") && (
                  <>
                    <span className="text-gray-500">h(n)</span>
                    <span className="text-right">
                      {formatNumber(candidate.h)}
                    </span>
                  </>
                )}

                {kind === "astar" && (
                  <>
                    <span className="text-gray-500">f(n)</span>
                    <span className="text-right font-semibold">
                      {formatNumber(candidate.f)}
                    </span>
                  </>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function ExplanationSection({ explanation, algorithmName }) {
  if (!explanation) {
    return null;
  }

  const congested = explanation.congested_segments || [];
  const comparison = explanation.comparison;
  const tspComparison = explanation.tsp_comparison || [];

  return (
    <div className="mt-4">
      <div className="rounded-lg bg-[#F7B558] p-3 mb-3 shadow-sm">
        <div className="flex items-center gap-2">
          <Lightbulb className="w-4 h-4" />
          <h4 className="text-sm font-bold text-[#363236]">
            Vì sao tuyến đường này?
          </h4>
        </div>
      </div>

      <div className="space-y-3 text-[11px]">
        <div className="rounded-lg bg-[#A5D48C]/15 border border-[#A5D48C]/50 p-3 text-[#363236]/80 leading-5 text-xs">
          {explanation.why_selected}
        </div>

        <div>
          <div className="font-semibold text-gray-800 mb-1">Tối ưu hóa</div>
          <div className="text-gray-500">{explanation.headline}</div>
        </div>

        <div>
          <div className="font-semibold text-gray-800 mb-1">Tính tối ưu</div>
          <div className="text-gray-500">{explanation.optimality}</div>
        </div>

        {tspComparison.length > 0 && (
          <div>
            <div className="font-semibold text-gray-800 mb-1">
              So sánh hai thuật toán TSP
            </div>
            <div className="space-y-1.5">
              {tspComparison.map((candidate) => (
                <div
                  key={candidate.algorithm_name}
                  className="rounded bg-gray-50 p-2"
                >
                  <div className="flex justify-between gap-2 font-medium text-gray-700">
                    <span>{candidate.algorithm_name}</span>
                    <span>{formatNumber(candidate.total_cost)}</span>
                  </div>
                  <div className="text-gray-500">
                    {formatDistance(candidate.total_distance)} ·{" "}
                    {formatTime(candidate.total_time)}
                  </div>
                </div>
              ))}
            </div>
            {explanation.visiting_order_names?.length > 0 && (
              <div className="mt-2 text-gray-500 leading-4">
                Thứ tự được chọn: {explanation.visiting_order_names.join(" → ")}
              </div>
            )}
          </div>
        )}

        {congested.length > 0 && (
          <div>
            <div className="font-semibold text-gray-800 mb-1">Đoạn kẹt xe</div>

            <div className="space-y-1.5">
              {congested.slice(0, 4).map((segment, index) => (
                <div
                  key={`${segment.from}-${segment.to}-${index}`}
                  className="rounded bg-gray-50 p-2"
                >
                  <div className="font-medium text-gray-700">
                    {segment.from} → {segment.to}
                  </div>

                  <div className="text-gray-500">
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

        {comparison && (
          <div>
            <div className="font-semibold text-gray-800 mb-1">
              So với mức nền
            </div>

            <div className="rounded bg-gray-50 p-2 space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-500">Khoảng cách</span>
                <span className="font-medium">
                  {formatDistance(comparison.distance_difference)}
                </span>
              </div>

              <div className="flex justify-between">
                <span className="text-gray-500">Thời gian</span>
                <span className="font-medium">
                  {formatTime(comparison.time_difference)}
                </span>
              </div>

              {comparison.cost_difference != null && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Chi phí</span>
                  <span className="font-medium">
                    {formatNumber(comparison.cost_difference)}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="text-[10px] text-gray-400 leading-4">
          {algorithmName || explanation.algorithm}
          {" · "}
          {explanation.comparison_note}
        </div>
      </div>
    </div>
  );
}

export default function StatsPanel({
  algorithm = "",
  algorithmName = "",
  explanation = null,
  distance,
  time,
  cost,
  exploredCount,
  executionTimeMs,
  simulation,
  startName = "",
  endName = "",
  waypointCount = 0,
  nodeCount = 0,
}) {
  const kind = getAlgorithmKind(algorithm, algorithmName);

  const metrics = simulation?.metrics || {};
  const frontierNodes = simulation?.frontierNodes || [];

  return (
    <div className="w-full min-h-full bg-white p-4">
      <div className="rounded-xl bg-[#F7B558] p-3 mb-4 shadow-sm">
        <h3 className="text-sm font-bold flex items-center gap-2 text-[#363236]">
          <Compass className="w-4 h-4" />
          Thống kê tuyến đường
        </h3>
        <p className="text-[10px] text-[#363236]/70 mt-0.5">
          Chi tiết tuyến đường đã chọn
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-lg border-2 border-[#A5D48C] bg-[#A5D48C]/10 p-2.5">
          <div className="flex items-center gap-1.5 text-[10px] text-[#363236]/70 mb-1">
            <MapPin className="w-3 h-3 text-[#A5D48C]" />
            Khoảng cách
          </div>
          <div className="text-sm font-bold text-[#363236]">
            {formatDistance(distance)}
          </div>
        </div>

        <div className="rounded-lg border-2 border-[#F7B558] bg-[#F7B558]/10 p-2.5">
          <div className="flex items-center gap-1.5 text-[10px] text-[#363236]/70 mb-1">
            <Timer className="w-3 h-3 text-[#F7B558]" />
            Thời gian
          </div>
          <div className="text-sm font-bold text-[#363236]">
            {formatTime(time)}
          </div>
        </div>

        <div className="rounded-lg border-2 border-[#363236]/15 bg-white p-2.5">
          <div className="flex items-center gap-1.5 text-[10px] text-[#363236]/70 mb-1">
            <Wallet className="w-3 h-3 text-[#363236]/70" />
            Chi phí
          </div>
          <div className="text-sm font-bold text-[#363236]">
            {cost == null ? "N/A" : formatNumber(cost)}
          </div>
        </div>

        <div className="rounded-lg border-2 border-[#A5D48C] bg-[#A5D48C]/10 p-2.5">
          <div className="flex items-center gap-1.5 text-[10px] text-[#363236]/70 mb-1">
            <Radar className="w-3 h-3 text-[#A5D48C]" />
            Đã khám phá
          </div>
          <div className="text-sm font-bold text-[#363236]">
            {exploredCount ?? 0}
          </div>
        </div>

        <div className="rounded-lg border-2 border-[#363236]/15 bg-white p-2.5">
          <div className="flex items-center gap-1.5 text-[10px] text-[#363236]/70 mb-1">
            <GitBranch className="w-3 h-3 text-[#363236]/70" />
            Số node tuyến
          </div>
          <div className="text-sm font-bold text-[#363236]">
            {nodeCount || "—"}
          </div>
        </div>

        <div className="rounded-lg border-2 border-[#F7B558] bg-[#F7B558]/10 p-2.5">
          <div className="flex items-center gap-1.5 text-[10px] text-[#363236]/70 mb-1">
            <MapPin className="w-3 h-3 text-[#F7B558]" />
            Điểm dừng
          </div>
          <div className="text-sm font-bold text-[#363236]">
            {waypointCount}
          </div>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-[#363236]/10 bg-white p-3">
        <div className="text-[10px] text-[#363236]/50 uppercase tracking-wide mb-2">
          Hành trình
        </div>

        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between gap-2">
            <span className="text-gray-500">Bắt đầu</span>
            <span className="font-semibold text-right">{startName || "—"}</span>
          </div>

          <div className="flex justify-between gap-2">
            <span className="text-gray-500">Kết thúc</span>
            <span className="font-semibold text-right">{endName || "—"}</span>
          </div>

          <div className="flex justify-between gap-2">
            <span className="text-gray-500">Số chặng</span>
            <span className="font-semibold text-right">
              {Math.max(1, waypointCount + 1)}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-[#363236]/10 bg-white p-3">
        <div className="text-[10px] text-[#363236]/50 uppercase tracking-wide mb-1">
          Thuật toán
        </div>

        <div className="text-sm font-bold text-[#363236]">
          {algorithmName || algorithm || "—"}
        </div>
      </div>

      {simulation && (
        <div className="mt-4 pt-3 border-t border-gray-100">
          <div className="flex items-center gap-2 mb-2">
            <CircleDot className="w-3.5 h-3.5 text-[#A5D48C]" />
            <h4 className="text-xs font-semibold text-[#363236]">Mô phỏng</h4>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] text-gray-500">Hiện tại</div>
              <div className="text-[11px] font-semibold">
                {simulation.current || "—"}
              </div>
            </div>

            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] text-gray-500">Biên</div>
              <div className="text-[11px] font-semibold">
                {frontierNodes.length}
              </div>
            </div>
          </div>

          {["ucs", "astar", "greedy"].includes(kind) &&
            Object.keys(metrics).length > 0 && (
              <div className="mt-2 grid grid-cols-3 gap-1">
                {metrics.g != null && (
                  <div className="rounded bg-[#A5D48C]/15 p-1.5 text-center">
                    <div className="text-[9px] text-gray-500">g</div>
                    <div className="text-[10px] font-semibold">
                      {formatNumber(metrics.g)}
                    </div>
                  </div>
                )}

                {["astar", "greedy"].includes(kind) && metrics.h != null && (
                  <div className="rounded bg-[#F7B558]/15 p-1.5 text-center">
                    <div className="text-[9px] text-gray-500">h</div>
                    <div className="text-[10px] font-semibold">
                      {formatNumber(metrics.h)}
                    </div>
                  </div>
                )}

                {kind === "astar" && metrics.f != null && (
                  <div className="rounded bg-[#363236]/10 p-1.5 text-center">
                    <div className="text-[9px] text-gray-500">f</div>
                    <div className="text-[10px] font-semibold">
                      {formatNumber(metrics.f)}
                    </div>
                  </div>
                )}
              </div>
            )}

          <div className="mt-3">
            <div className="flex items-center gap-2 mb-2">
              <GitBranch className="w-3.5 h-3.5 text-[#A5D48C]" />
              <h4 className="text-xs font-semibold text-[#363236]">
                So sánh ứng viên
              </h4>
            </div>

            <CandidateComparison
              candidates={simulation.candidates || []}
              kind={kind}
              nextSelected={simulation.nextSelected}
              selectionMetric={simulation.selectionMetric}
            />
          </div>
        </div>
      )}

      <ExplanationSection
        explanation={explanation}
        algorithmName={algorithmName || algorithm}
      />

      <div className="mt-4 pt-3 border-t border-gray-100">
        <div className="flex justify-between">
          <span className="text-xs text-gray-500">Thời gian tìm kiếm</span>

          <span className="text-xs font-semibold">
            {executionTimeMs != null
              ? `${Number(executionTimeMs).toFixed(2)} ms`
              : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}
