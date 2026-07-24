import React from "react";
import ZoomControl from "./ZoomControl";

export default function MapArea({
  nodes,
  edges,
  hasSearched,
  selectedNodeIds,
  activeNode,
  zoom,
  onZoomIn,
  onZoomOut,
}) {
  return (
    <main className="flex-1 relative bg-gray-200 overflow-hidden">
      {/* Grid background */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(0,0,0,0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(0,0,0,0.05) 1px, transparent 1px)",
          backgroundSize: "80px 80px",
        }}
      />

      {/* Light map base */}
      <div className="absolute inset-4 md:inset-8 bg-gray-50 rounded-sm shadow-sm overflow-hidden">
        <svg
          viewBox="-20 -20 740 580"
          className="w-full h-full transition-transform duration-200 ease-out"
          preserveAspectRatio="xMidYMid meet"
          style={{ transform: `scale(${zoom})`, transformOrigin: "center" }}
        >
          {/* Base network: every edge starts grey */}
          {edges.map(([a, b], i) => {
            const isSelectedEdge =
              hasSearched && selectedNodeIds.has(a.id) && selectedNodeIds.has(b.id);
            return (
              <line
                key={i}
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
                stroke={isSelectedEdge ? "#2563eb" : "#c7cbd1"}
                strokeWidth={isSelectedEdge ? 3 : 1}
                strokeLinecap="round"
                className="transition-all duration-300 ease-out"
                style={
                  isSelectedEdge
                    ? { filter: "drop-shadow(0 0 3px rgba(37,99,235,0.5))" }
                    : undefined
                }
              />
            );
          })}

          {/* Nodes: grey by default, orange once selected by the search */}
          {nodes.map((n) => {
            const isSelected = hasSearched && selectedNodeIds.has(n.id);
            return (
              <circle
                key={n.id}
                cx={n.x}
                cy={n.y}
                r={isSelected ? 5 : 3}
                fill={isSelected ? "#f97316" : "#6b7280"}
                stroke={isSelected ? "white" : "none"}
                strokeWidth={isSelected ? 1.5 : 0}
                className="transition-all duration-300 ease-out"
              />
            );
          })}

          {/* Pulse on the most recently revealed orange node */}
          {hasSearched && activeNode && (
            <circle
              cx={activeNode.x}
              cy={activeNode.y}
              r={7}
              fill="none"
              stroke="#f97316"
              strokeWidth="2"
              className="transition-all duration-300 ease-out"
            >
              <animate attributeName="r" values="6;10;6" dur="1.2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.8;0;0.8" dur="1.2s" repeatCount="indefinite" />
            </circle>
          )}
        </svg>
      </div>

      <ZoomControl zoom={zoom} onZoomIn={onZoomIn} onZoomOut={onZoomOut} />
    </main>
  );
}
