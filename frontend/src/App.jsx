import { useMemo, useState } from "react";

import trafficData from "./data/hcm_traffic_data.json";

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

  const [algorithm, setAlgorithm] = useState("astar");
  const [algorithmName, setAlgorithmName] = useState("");
  const [optimization, setOptimization] = useState("default");

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

  const totalSteps = exploredNodes.length;

  const resetSearchResult = () => {
    setHasSearched(false);
    setPath([]);
    setRoutePositions([]);
    setPathNodeNames([]);
    setExploredNodes([]);
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

      setPath(combinedPath);
      setRoutePositions(combinedCoordinates);
      setPathNodeNames(combinedNames);
      setExploredNodes([...new Set(explored)]);
      setStep(0);

      setRouteStats({
        distance: totalDistance,
        time: totalTime,
        cost: hasCost ? totalCost : null,
        exploredCount: totalExploredCount,
        executionTimeMs: totalExecutionTime,
      });

      setHasSearched(true);
    } catch (error) {
      console.error("Search error:", error);
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
    setOptimization("default");
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
          routePositions={routePositions}
          start={start}
          end={end}
          waypoints={waypoints}
          path={path}
          // Chỉ hiển thị explored nodes khi người dùng đang xem lại thuật toán.
          // step = 0 => không hiển thị explored nodes.
          exploredNodes={step > 0 ? exploredNodes.slice(0, step) : []}
          onNodeClick={handleNodeClick}
        />
      </div>
    </div>
  );
}
