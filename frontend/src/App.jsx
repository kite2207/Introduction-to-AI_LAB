import { useState } from "react";

import nodesData from "./data/nodes.json";

import Sidebar from "./components/Sidebar";
import HCMMap from "./components/HCMMap";

export default function App() {
  // Convert nodes.json
  // [
  //   {
  //     node_id:"N01",
  //     lat:...
  //   }
  // ]
  //
  // thành:
  // [
  //   {
  //     id:"N01",
  //     lat:...
  //   }
  // ]

  const nodes = nodesData.map((node) => ({
    id: node.node_id,
    ...node,
  }));

  const [start, setStart] = useState(null);

  const [end, setEnd] = useState(null);

  const [waypoints, setWaypoints] = useState([]);

  const [addingStop, setAddingStop] = useState(false);

  const [path, setPath] = useState([]);

  const [algorithm, setAlgorithm] = useState("A*");

  const [optimization, setOptimization] = useState("default");

  const [hasSearched, setHasSearched] = useState(false);

  const [loading, setLoading] = useState(false);

  const [step, setStep] = useState(0);

  const TOTAL_STEPS = 10;

  // Click node trên map

  const handleNodeClick = (id) => {
    // đang ở chế độ thêm điểm dừng
    if (addingStop) {
      if (id !== start && id !== end && !waypoints.includes(id)) {
        setWaypoints([...waypoints, id]);
      }
      setAddingStop(false);

      return;
    }

    // chọn start
    if (start === null) {
      setStart(id);

      return;
    }

    // chọn end
    if (end === null && id !== start) {
      setEnd(id);

      return;
    }

    return;
  };

  const removeWaypoint = (id) => {
    setWaypoints(waypoints.filter((w) => w !== id));

    setHasSearched(false);

    setPath([]);
  };

  const handleSearch = async () => {
    if (!start || !end) return;

    setLoading(true);






    const res = await fetch(
      "http://localhost:8000/search",
      {
        method: "POST",

        headers: {
          "Content-Type": "application/json"
        },

        body: JSON.stringify({

          start: start,

          end: end,

          algorithm: algorithm,

          optimization: optimization

        })

      }
    );


    const data = await res.json();


    setPath(data.path);




    // TEST TẠM
    // nối thẳng start -> end

    setPath([start, ...waypoints, end]);

    setLoading(false);

    setHasSearched(true);

    console.log({
      start,

      end,

      algorithm,

      optimization,
    });
  };

  const handleSettingChange = (setter) => (value) => {
    setter(value);

    // bắt search lại
    setHasSearched(false);

    // xóa đường cũ
    setPath([]);
  };

  const handleReset = () => {
    setStart(null);
    setEnd(null);
    setWaypoints([]);

    setAddingStop(false);

    setAlgorithm("A*");
    setOptimization("default");

    setPath([]);
    setHasSearched(false);
    setStep(0);
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
          start={start}
          end={end}
          addingStop={addingStop}
          setAddingStop={setAddingStop}
          waypoints={waypoints}
          removeWaypoint={removeWaypoint}
          loading={loading}
          optimization={optimization}
          setOptimization={handleSettingChange(setOptimization)}
          algorithm={algorithm}
          setAlgorithm={handleSettingChange(setAlgorithm)}
          hasSearched={hasSearched}
          onSearch={handleSearch}
          step={step}
          totalSteps={TOTAL_STEPS}
          onStepBack={() => {
            setStep(Math.max(0, step - 1));
          }}
          onStepForward={() => {
            setStep(Math.min(TOTAL_STEPS, step + 1));
          }}
          onSkipToStart={() => {
            setStep(0);
          }}
          onSkipToEnd={() => {
            setStep(TOTAL_STEPS);
          }}
          onReset={handleReset}
        />
      </div>

      <div
        style={{
          flex: 1,
          minWidth: 0,
          height: "100vh",
        }}
      >
        <HCMMap
          nodes={nodes}
          start={start}
          end={end}
          waypoints={waypoints}
          path={path}
          onNodeClick={handleNodeClick}
        />
      </div>
    </div>
  );
}
