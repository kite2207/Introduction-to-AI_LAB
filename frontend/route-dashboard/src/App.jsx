import React, { useState, useMemo } from "react";
import Sidebar from "./components/Sidebar";
import StatsPanel from "./components/StatsPanel";
import MapArea from "./components/MapArea";
import { useRouteGraph } from "./hooks/useRouteGraph";

const TOTAL_STEPS = 24;

export default function App() {
  const [optimization, setOptimization] = useState("Default");
  const [algorithm, setAlgorithm] = useState("Depth-first Search");
  const [hasSearched, setHasSearched] = useState(false);
  const [step, setStep] = useState(5);
  const [zoom, setZoom] = useState(1);

  const { nodes, edges, path } = useRouteGraph();

  const zoomIn = () => setZoom((z) => Math.min(2.5, +(z + 0.25).toFixed(2)));
  const zoomOut = () => setZoom((z) => Math.max(0.5, +(z - 0.25).toFixed(2)));

  const handleSearch = () => {
    setHasSearched(true);
    setStep(5);
  };
  const handleReset = () => setHasSearched(false);

  const stepBack = () => setStep((s) => Math.max(1, s - 1));
  const stepForward = () => setStep((s) => Math.min(TOTAL_STEPS, s + 1));
  const skipToStart = () => setStep(1);
  const skipToEnd = () => setStep(TOTAL_STEPS);

  // How much of the path to reveal, based on step progress
  const revealedPath = useMemo(() => {
    const pathProgress = step / TOTAL_STEPS;
    const revealCount = Math.max(1, Math.round(path.length * pathProgress));
    return path.slice(0, revealCount);
  }, [path, step]);

  const activeNode = revealedPath[revealedPath.length - 1];
  const selectedNodeIds = useMemo(
    () => new Set(revealedPath.map((n) => n.id)),
    [revealedPath]
  );

  return (
    <div className="flex h-screen w-full bg-white overflow-hidden font-sans relative">
      <Sidebar
        optimization={optimization}
        setOptimization={setOptimization}
        algorithm={algorithm}
        setAlgorithm={setAlgorithm}
        hasSearched={hasSearched}
        onSearch={handleSearch}
        step={step}
        totalSteps={TOTAL_STEPS}
        onStepBack={stepBack}
        onStepForward={stepForward}
        onSkipToStart={skipToStart}
        onSkipToEnd={skipToEnd}
        onReset={handleReset}
      />

      {hasSearched && <StatsPanel />}

      <MapArea
        nodes={nodes}
        edges={edges}
        hasSearched={hasSearched}
        selectedNodeIds={selectedNodeIds}
        activeNode={activeNode}
        zoom={zoom}
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
      />
    </div>
  );
}
