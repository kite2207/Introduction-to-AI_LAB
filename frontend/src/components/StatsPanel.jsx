import React from "react";
import {
  Route,
  Clock,
  DollarSign,
  Search,
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
  return n >= 60
    ? `${(n / 60).toFixed(1)} min`
    : `${n.toFixed(0)} s`;
}

function formatNumber(value) {
  if (value == null) return "—";
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  return n.toFixed(2);
}

function getAlgorithmKind(
  algorithm = "",
  algorithmName = ""
) {
  const raw =
    `${algorithm} ${algorithmName}`.toLowerCase();

  if (
    raw.includes("dijkstra") ||
    raw.includes("uniform") ||
    raw.includes("ucs")
  ) return "ucs";

  if (
    raw.includes("a*") ||
    raw.includes("astar")
  ) return "astar";

  if (raw.includes("greedy")) return "greedy";

  if (
    raw.includes("breadth") ||
    raw.includes("bfs")
  ) return "bfs";

  if (
    raw.includes("depth") ||
    raw.includes("dfs")
  ) return "dfs";

  return "unknown";
}

function CandidateComparison({
  candidates,
  kind,
  nextSelected,
  selectionMetric,
}) {
  const metricLabel = {
    ucs: "g(n)",
    astar: "f(n)",
    greedy: "h(n)",
    bfs: "FIFO",
    dfs: "LIFO",
  }[kind] || selectionMetric || "priority";

  if (!candidates?.length) {
    return (
      <div className="text-xs text-gray-400 py-2">
        Không còn node chưa đi qua.
      </div>
    );
  }

  return (
    <div className="space-y-2 max-h-64 overflow-y-auto">
      <div className="text-[10px] text-gray-400">
        Chọn theo {metricLabel}
      </div>

      {candidates.map((candidate, index) => {
        const isNext =
          nextSelected != null &&
          String(candidate.node_id) ===
            String(nextSelected);

        return (
          <div
            key={`${candidate.node_id}-${index}`}
            className={`rounded-md border p-2 ${
              isNext
                ? "border-violet-400 bg-violet-50"
                : "border-gray-100 bg-gray-50"
            }`}
          >
            <div className="flex justify-between gap-2">
              <span className="text-xs font-semibold">
                → {candidate.node_id}
              </span>

              {isNext && (
                <span className="text-[10px] font-bold text-violet-700">
                  NEXT
                </span>
              )}
            </div>

            {kind === "bfs" || kind === "dfs" ? (
              <div className="mt-1 text-[10px] text-gray-500">
                {kind === "bfs"
                  ? `Queue position: ${index + 1}`
                  : `Stack position: ${index + 1}`}
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-x-3 gap-y-1 mt-1.5 text-[11px]">
                <span className="text-gray-500">g(n)</span>
                <span className="text-right">
                  {formatNumber(candidate.g)}
                </span>

                {(kind === "astar" ||
                  kind === "greedy") && (
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

function ExplanationSection({
  explanation,
  algorithmName,
}) {
  if (!explanation) {
    return null;
  }

  const congested =
    explanation.congested_segments || [];
  const comparison = explanation.comparison;

  return (
    <div className="mt-4 pt-4 border-t border-gray-200">
      <div className="flex items-center gap-2 mb-3">
        <Lightbulb className="w-4 h-4 text-blue-600" />
        <h4 className="text-sm font-semibold text-gray-900">
          Why this route?
        </h4>
      </div>

      <div className="space-y-3 text-[11px]">
        <div className="rounded-md bg-blue-50 border border-blue-100 p-3 text-gray-700 leading-5">
          {explanation.why_selected}
        </div>

        <div>
          <div className="font-semibold text-gray-800 mb-1">
            Optimization
          </div>
          <div className="text-gray-500">
            {explanation.headline}
          </div>
        </div>

        <div>
          <div className="font-semibold text-gray-800 mb-1">
            Optimality
          </div>
          <div className="text-gray-500">
            {explanation.optimality}
          </div>
        </div>

        {congested.length > 0 && (
          <div>
            <div className="font-semibold text-gray-800 mb-1">
              Congested segments
            </div>

            <div className="space-y-1.5">
              {congested.slice(0, 4).map(
                (segment, index) => (
                  <div
                    key={`${segment.from}-${segment.to}-${index}`}
                    className="rounded bg-gray-50 p-2"
                  >
                    <div className="font-medium text-gray-700">
                      {segment.from} → {segment.to}
                    </div>

                    <div className="text-gray-500">
                      Congestion {segment.congestion}
                      {segment.risk &&
                      segment.risk !== "none"
                        ? ` · ${segment.risk}`
                        : ""}
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        )}

        {comparison && (
          <div>
            <div className="font-semibold text-gray-800 mb-1">
              Compared with baseline
            </div>

            <div className="rounded bg-gray-50 p-2 space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-500">
                  Distance
                </span>
                <span className="font-medium">
                  {formatDistance(
                    comparison.distance_difference
                  )}
                </span>
              </div>

              <div className="flex justify-between">
                <span className="text-gray-500">
                  Time
                </span>
                <span className="font-medium">
                  {formatTime(
                    comparison.time_difference
                  )}
                </span>
              </div>

              {comparison.cost_difference != null && (
                <div className="flex justify-between">
                  <span className="text-gray-500">
                    Cost
                  </span>
                  <span className="font-medium">
                    {formatNumber(
                      comparison.cost_difference
                    )}
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
}) {
  const kind = getAlgorithmKind(
    algorithm,
    algorithmName
  );

  const metrics = simulation?.metrics || {};
  const frontierNodes =
    simulation?.frontierNodes || [];

  return (
    <div className="w-full min-h-full bg-white p-4">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">
        Route Statistics
      </h3>

      <div className="space-y-2.5">
        <div className="flex items-center gap-2">
          <Route className="w-3.5 h-3.5 text-blue-600" />
          <span className="text-xs text-gray-500 flex-1">
            Distance
          </span>
          <span className="text-xs font-semibold">
            {formatDistance(distance)}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Clock className="w-3.5 h-3.5 text-emerald-600" />
          <span className="text-xs text-gray-500 flex-1">
            Time
          </span>
          <span className="text-xs font-semibold">
            {formatTime(time)}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <DollarSign className="w-3.5 h-3.5 text-amber-600" />
          <span className="text-xs text-gray-500 flex-1">
            Cost
          </span>
          <span className="text-xs font-semibold">
            {cost == null ? "N/A" : formatNumber(cost)}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Search className="w-3.5 h-3.5 text-purple-600" />
          <span className="text-xs text-gray-500 flex-1">
            Explored
          </span>
          <span className="text-xs font-semibold">
            {exploredCount ?? 0}
          </span>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-gray-100">
        <div className="text-[11px] text-gray-500">
          Algorithm
        </div>

        <div className="text-sm font-semibold text-gray-900">
          {algorithmName || algorithm || "—"}
        </div>
      </div>

      {simulation && (
        <div className="mt-4 pt-3 border-t border-gray-100">
          <div className="flex items-center gap-2 mb-2">
            <CircleDot className="w-3.5 h-3.5 text-violet-600" />
            <h4 className="text-xs font-semibold">
              Simulation
            </h4>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] text-gray-500">
                Current
              </div>
              <div className="text-[11px] font-semibold">
                {simulation.current || "—"}
              </div>
            </div>

            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] text-gray-500">
                Frontier
              </div>
              <div className="text-[11px] font-semibold">
                {frontierNodes.length}
              </div>
            </div>
          </div>

          {["ucs", "astar", "greedy"].includes(kind) &&
            Object.keys(metrics).length > 0 && (
              <div className="mt-2 grid grid-cols-3 gap-1">
                {metrics.g != null && (
                  <div className="rounded bg-blue-50 p-1.5 text-center">
                    <div className="text-[9px] text-gray-500">g</div>
                    <div className="text-[10px] font-semibold">
                      {formatNumber(metrics.g)}
                    </div>
                  </div>
                )}

                {["astar", "greedy"].includes(kind) &&
                  metrics.h != null && (
                    <div className="rounded bg-violet-50 p-1.5 text-center">
                      <div className="text-[9px] text-gray-500">h</div>
                      <div className="text-[10px] font-semibold">
                        {formatNumber(metrics.h)}
                      </div>
                    </div>
                  )}

                {kind === "astar" &&
                  metrics.f != null && (
                    <div className="rounded bg-red-50 p-1.5 text-center">
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
              <GitBranch className="w-3.5 h-3.5 text-violet-600" />
              <h4 className="text-xs font-semibold">
                Candidate Comparison
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
          <span className="text-xs text-gray-500">
            Search time
          </span>

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
