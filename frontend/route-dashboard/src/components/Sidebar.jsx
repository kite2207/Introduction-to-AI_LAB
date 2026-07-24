import React from "react";
import RouteInputs from "./RouteInputs";
import RouteSettings from "./RouteSettings";
import RouteResults from "./RouteResults";

export default function Sidebar({
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
    <aside className="w-96 shrink-0 border-r border-gray-200 bg-white shadow-lg flex flex-col px-6 py-6 overflow-y-auto z-20">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Route Dashboard</h1>

      <RouteInputs />

      <RouteSettings
        optimization={optimization}
        setOptimization={setOptimization}
        algorithm={algorithm}
        setAlgorithm={setAlgorithm}
      />

      {!hasSearched && <div className="flex-1" />}

      <button
        onClick={onSearch}
        disabled={hasSearched}
        className={`w-full text-sm font-semibold rounded-md py-2.5 transition-colors ${
          hasSearched
            ? "bg-blue-100 text-blue-400 cursor-not-allowed"
            : "bg-blue-600 hover:bg-blue-700 text-white"
        }`}
      >
        {hasSearched ? "Route Found" : "Search"}
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
