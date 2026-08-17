import { useMemo, useState } from "react";

// Graph data is sourced from the repository root (single source of truth),
// not from a copy inside frontend/src/data.
import trafficData from "../../data/hcm_traffic_data.json";

import Sidebar from "./components/Sidebar";
import HCMMap from "./components/HCMMap";
import StatsPanel from "./components/StatsPanel";

const API_URL = "http://localhost:8000/api/search";

export default function App() {
  const { nodes, edges, nodeMap } = useMemo(() => {
    const nodes = Object.entries(trafficData).map(([id, node]) => ({
      id,
      name: node.name,
      lat: node.lat,
      lng: node.lng,
      type: node.type,
    }));

    const edges = [];

    Object.entries(trafficData).forEach(([sourceId, node]) => {
      node.connected_to.forEach((edge) => {
        edges.push({
          source: sourceId,
          target: edge.target_node,
          distance: edge.distance,
          estimatedTime: edge.estimated_time,
          congestion: edge.congestion_level,
          direction: edge.direction,
          risk: edge.risk_factors,
          geometry: Array.isArray(edge.geometry)
            ? edge.geometry.map((point) =>
                Array.isArray(point)
                  ? [point[0], point[1]]
                  : [point.lat, point.lng],
              )
            : null,
        });
      });
    });

    const nodeMap = Object.fromEntries(nodes.map((node) => [node.id, node]));

    return { nodes, edges, nodeMap };
  }, []);

  const nodeOptions = useMemo(
    () =>
      nodes.map((node) => ({
        value: node.id,
        label: node.name || node.id,
      })),
    [nodes],
  );

  const [start, setStart] = useState(null);
  const [end, setEnd] = useState(null);
  const [waypoints, setWaypoints] = useState([]);
  const [addingStop, setAddingStop] = useState(false);

  const [path, setPath] = useState([]);
  const [routePositions, setRoutePositions] = useState([]);
  const [pathNodeNames, setPathNodeNames] = useState([]);
  const [exploredNodes, setExploredNodes] = useState([]);
  const [simulationSteps, setSimulationSteps] = useState([]);
  const [routeExplanation, setRouteExplanation] = useState(null);

  const [algorithm, setAlgorithm] = useState("astar");
  const [algorithmName, setAlgorithmName] = useState("");
  const [optimization, setOptimization] = useState("mixed");

  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);

  const [routeStats, setRouteStats] = useState({
    distance: null,
    time: null,
    cost: null,
    exploredCount: 0,
    executionTimeMs: 0,
  });

  const totalSteps = simulationSteps.length;

  const resetSearchResult = () => {
    setHasSearched(false);
    setPath([]);
    setRoutePositions([]);
    setPathNodeNames([]);
    setExploredNodes([]);
    setSimulationSteps([]);
    setRouteExplanation(null);
    setStep(0);
    setRouteStats({
      distance: null,
      time: null,
      cost: null,
      exploredCount: 0,
      executionTimeMs: 0,
    });
  };

  const handleNodeClick = (id) => {
    if (addingStop) {
      if (id !== start && id !== end && !waypoints.includes(id)) {
        setWaypoints((prev) => [...prev, id]);
      }

      setAddingStop(false);
      resetSearchResult();
      return;
    }

    if (start === null) {
      setStart(id);
      resetSearchResult();
      return;
    }

    if (end === null && id !== start) {
      setEnd(id);
      resetSearchResult();
    }
  };

  const removeWaypoint = (id) => {
    setWaypoints((prev) => prev.filter((nodeId) => nodeId !== id));
    resetSearchResult();
  };

  const callSearchApi = async (from, to) => {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        start: String(from),
        end: String(to),
        algorithm,
        optimization,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data?.detail || `Search failed (${response.status})`);
    }

    return data;
  };

  const searchRoute = async () => {
    if (!start || !end || loading) {
      return;
    }

    setLoading(true);
    setHasSearched(false);

    try {
      // Current backend API accepts start/end only.
      // When waypoints exist, search each leg sequentially:
      // start -> waypoint 1 -> ... -> waypoint N -> end.
      const stops = [start, ...waypoints, end];

      const results = [];

      for (let i = 0; i < stops.length - 1; i += 1) {
        results.push(await callSearchApi(stops[i], stops[i + 1]));
      }

      const combinedPath = [];
      const combinedCoordinates = [];
      const combinedNames = [];
      const explored = [];
      const combinedSteps = [];
      const explanations = [];

      let totalDistance = 0;
      let totalTime = 0;
      let totalCost = 0;
      let hasCost = true;
      let totalExploredCount = 0;
      let totalExecutionTime = 0;

      results.forEach((result) => {
        const segmentPath = result.path || [];
        const segmentCoordinates = result.path_coordinates || [];
        const segmentNames = result.path_node_names || [];

        combinedPath.push(
          ...(combinedPath.length > 0 ? segmentPath.slice(1) : segmentPath),
        );

        combinedCoordinates.push(
          ...(combinedCoordinates.length > 0
            ? segmentCoordinates.slice(1)
            : segmentCoordinates),
        );

        combinedNames.push(
          ...(combinedNames.length > 0 ? segmentNames.slice(1) : segmentNames),
        );

        explored.push(...(result.explored_nodes || []));

        if (result.explanation) {
          explanations.push(result.explanation);
        }

        const segmentSteps = result.steps || [];
        const stepOffset = combinedSteps.length;

        segmentSteps.forEach((traceStep, index) => {
          const previousExploredEdges =
            index > 0
              ? segmentSteps[index - 1]?.exploredEdges || []
              : combinedSteps.length > 0
                ? combinedSteps[combinedSteps.length - 1]?.exploredEdges || []
                : [];

          combinedSteps.push({
            ...traceStep,
            step: stepOffset + index,
            previousExploredEdges,
          });
        });

        totalDistance += Number(result.total_distance || 0);
        totalTime += Number(result.total_time || 0);

        if (result.total_cost == null) {
          hasCost = false;
        } else {
          totalCost += Number(result.total_cost);
        }

        totalExploredCount += Number(result.explored_count || 0);
        totalExecutionTime += Number(result.execution_time_ms || 0);
      });

      setAlgorithmName(
        results[results.length - 1]?.algorithm_name || algorithm,
      );

      setPath(combinedPath);
      setRoutePositions(combinedCoordinates);
      setPathNodeNames(combinedNames);
      setExploredNodes([...new Set(explored)]);
      setSimulationSteps(combinedSteps);
      setStep(0);

      setRouteExplanation(
        explanations.length === 1
          ? explanations[0]
          : explanations.length > 1
            ? {
                headline: "Tối ưu hóa qua nhiều chặng đường.",
                why_selected: `Tuyến đường gồm ${results.length} chặng được tối ưu theo mục tiêu '${optimization}' bằng thuật toán ${
                  explanations[0]?.algorithm || algorithm
                }.`,
                optimality: explanations[0]?.optimality || "",
                congested_segments: explanations.flatMap(
                  (item) => item?.congested_segments || [],
                ),
                comparison: null,
                // Multi-waypoint: không có tham chiếu Dijkstra hay phương án thay thế.
                optimality_reference: null,
                route_comparison: null,
                comparison_note:
                  "Đã tìm kiếm nhiều chặng vì bạn đã chọn điểm dừng.",
                algorithm: explanations[0]?.algorithm || algorithm,
                // Chi tiết từng chặng để hiển thị rõ hơn.
                legs: results.map((result, index) => ({
                  index: index + 1,
                  from: result.start_name || stops[index],
                  to: result.end_name || stops[index + 1],
                  route_names: result.path_node_names || [],
                  distance: Number(result.total_distance || 0),
                  time: Number(result.total_time || 0),
                  cost:
                    result.total_cost == null
                      ? null
                      : Number(result.total_cost),
                  algorithm_name: result.algorithm_name,
                })),
                totals: {
                  distance: totalDistance,
                  time: totalTime,
                  cost: hasCost ? totalCost : null,
                  explored_count: totalExploredCount,
                  execution_time_ms: totalExecutionTime,
                },
              }
            : null,
      );

      setRouteStats({
        distance: totalDistance,
        time: totalTime,
        cost: hasCost ? totalCost : null,
        exploredCount: totalExploredCount,
        executionTimeMs: totalExecutionTime,
      });

      setHasSearched(true);
    } catch (error) {
      console.error("Lỗi tìm kiếm:", error);
      alert(error.message || "Không thể tìm đường.");
      resetSearchResult();
    } finally {
      setLoading(false);
    }
  };

  const handleSettingChange = (setter) => (value) => {
    setter(value);
    resetSearchResult();
  };

  const handleReset = () => {
    setStart(null);
    setEnd(null);
    setWaypoints([]);
    setAddingStop(false);
    setAlgorithm("astar");
    setAlgorithmName("");
    setOptimization("mixed");
    resetSearchResult();
  };

  return (
    <div
      style={{
        display: "flex",
        width: "100vw",
        height: "100vh",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: "360px",
          minWidth: "360px",
          height: "100vh",
        }}
      >
        <Sidebar
          nodeMap={nodeMap}
          nodeOptions={nodeOptions}
          start={start}
          end={end}
          setStart={(value) => {
            setStart(value);
            resetSearchResult();
          }}
          setEnd={(value) => {
            setEnd(value);
            resetSearchResult();
          }}
          addingStop={addingStop}
          setAddingStop={setAddingStop}
          setWaypoints={setWaypoints}
          waypoints={waypoints}
          removeWaypoint={removeWaypoint}
          loading={loading}
          optimization={optimization}
          setOptimization={handleSettingChange(setOptimization)}
          algorithm={algorithm}
          setAlgorithm={handleSettingChange(setAlgorithm)}
          algorithmName={algorithmName}
          routeExplanation={routeExplanation}
          hasSearched={hasSearched}
          onSearch={searchRoute}
          step={step}
          totalSteps={totalSteps}
          onStepBack={() => {
            setStep((prev) => Math.max(0, prev - 1));
          }}
          onStepForward={() => {
            setStep((prev) => Math.min(totalSteps, prev + 1));
          }}
          onSkipToStart={() => setStep(0)}
          onSkipToEnd={() => setStep(totalSteps)}
          onReset={handleReset}
        />
      </div>

      {hasSearched && (
        <div
          style={{
            width: "260px",
            minWidth: "260px",
            height: "100vh",
            background: "#fff",
            borderRight: "1px solid #ddd",
            overflowY: "auto",
          }}
        >
          <StatsPanel
            algorithm={algorithm}
            algorithmName={algorithmName}
            simulation={simulationSteps[step - 1] || null}
            distance={routeStats.distance}
            time={routeStats.time}
            cost={routeStats.cost}
            exploredCount={routeStats.exploredCount}
            executionTimeMs={routeStats.executionTimeMs}
            pathNodeNames={pathNodeNames}
          />
        </div>
      )}

      <div
        style={{
          flex: 1,
          minWidth: 0,
          height: "100vh",
        }}
      >
        <HCMMap
          nodeMap={nodeMap}
          nodes={nodes}
          edges={edges}
          start={start}
          end={end}
          waypoints={waypoints}
          path={path}
          // Simulation snapshot for the current visualizer step.
          // step = 0 => no explored nodes/edges shown yet.
          simulation={simulationSteps[step - 1] || null}
          onNodeClick={handleNodeClick}
        />
      </div>
    </div>
  );
}
