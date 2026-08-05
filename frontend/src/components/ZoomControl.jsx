import React from "react";
import { Plus, Minus } from "lucide-react";

export default function ZoomControl({ zoom, onZoomIn, onZoomOut, min = 0.5, max = 2.5 }) {
  return (
    <div className="absolute bottom-6 right-6 bg-white rounded-full shadow-md flex flex-col items-center overflow-hidden border border-gray-200">
      <button
        onClick={onZoomIn}
        disabled={zoom >= max}
        className="w-9 h-9 flex items-center justify-center text-gray-600 hover:bg-gray-50 disabled:text-gray-300 disabled:hover:bg-white transition-colors"
      >
        <Plus className="w-4 h-4" />
      </button>
      <div className="w-6 h-px bg-gray-200" />
      <button
        onClick={onZoomOut}
        disabled={zoom <= min}
        className="w-9 h-9 flex items-center justify-center text-gray-600 hover:bg-gray-50 disabled:text-gray-300 disabled:hover:bg-white transition-colors"
      >
        <Minus className="w-4 h-4" />
      </button>
    </div>
  );
}
