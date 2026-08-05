import React from "react";
import {
  SkipBack,
  ChevronLeft,
  ChevronRight,
  SkipForward,
  Lightbulb,
  RotateCcw,
} from "lucide-react";

export default function RouteResults({
  hasSearched,
  step,
  totalSteps,
  optimization,
  algorithm,
  onStepBack,
  onStepForward,
  onSkipToStart,
  onSkipToEnd,
  onReset,
}) {
  return (
    <div>
      {/* Reset button */}
      <button
        onClick={onReset}
        className="w-full flex items-center justify-center gap-1.5 text-sm font-medium text-gray-600 border border-gray-300 rounded-md py-2 hover:bg-gray-50 transition-colors"
      >
        <RotateCcw className="w-3.5 h-3.5" />
        Reset
      </button>
      <div
        className={`transition-all duration-500 ease-out overflow-hidden ${
          hasSearched
            ? "max-h-[600px] opacity-100 mt-6"
            : "max-h-0 opacity-0 mt-0"
        }`}
      >
        {/* Visualizer Controls */}
        <div className="mb-4">
          <h2 className="text-sm font-semibold text-gray-900 mb-2">
            Visualizer
          </h2>
          <div className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5">
            <div className="flex items-center gap-1">
              <button
                onClick={onSkipToStart}
                className="p-1.5 rounded hover:bg-gray-200 text-gray-600 transition-colors"
              >
                <SkipBack className="w-4 h-4" />
              </button>
              <button
                onClick={onStepBack}
                className="p-1.5 rounded hover:bg-gray-200 text-gray-600 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={onStepForward}
                className="p-1.5 rounded hover:bg-gray-200 text-gray-600 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
              <button
                onClick={onSkipToEnd}
                className="p-1.5 rounded hover:bg-gray-200 text-gray-600 transition-colors"
              >
                <SkipForward className="w-4 h-4" />
              </button>
            </div>
            <span className="text-xs font-medium text-gray-500 tabular-nums">
              Step {step} / {totalSteps}
            </span>
          </div>
        </div>

        {/* AI Explanation Card */}
        <div className="mb-4 rounded-lg border border-blue-100 bg-blue-50 p-3">
          <div className="flex items-start gap-2">
            <div className="shrink-0 w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center">
              <Lightbulb className="w-3.5 h-3.5 text-blue-600" />
            </div>
            <div>
              <p className="text-xs font-semibold text-blue-900 mb-1">
                Why this route?
              </p>
              <p className="text-xs text-blue-800 leading-relaxed">
                This path minimizes total {optimization.toLowerCase()} cost by
                favoring fewer intersections and avoiding congested segments,
                based on the {algorithm} traversal.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
