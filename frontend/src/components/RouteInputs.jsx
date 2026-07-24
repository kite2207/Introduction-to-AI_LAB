import React from "react";
import { Target, ArrowRight, Flag, Plus } from "lucide-react";

export default function RouteInputs() {
  return (
    <section className="mb-6">
      <h2 className="text-sm font-semibold text-gray-900 mb-3">Route Inputs</h2>

      <div className="mb-4">
        <label className="block text-xs text-gray-500 mb-1.5">Start Location</label>
        <div className="flex items-center gap-2 rounded-full border border-gray-300 px-3 py-2 focus-within:border-blue-400 focus-within:ring-1 focus-within:ring-blue-400">
          <Target className="w-4 h-4 text-gray-400 shrink-0" />
          <input
            type="text"
            placeholder="Enter starting point"
            className="w-full text-sm text-gray-700 placeholder-gray-400 outline-none bg-transparent"
          />
        </div>
      </div>

      <div className="mb-3">
        <label className="block text-xs text-gray-500 mb-1.5">End Location</label>
        <div className="flex items-center gap-2 rounded-full border border-gray-300 px-3 py-2 focus-within:border-blue-400 focus-within:ring-1 focus-within:ring-blue-400">
          <ArrowRight className="w-4 h-4 text-gray-400 shrink-0" />
          <input
            type="text"
            placeholder="Enter destination"
            className="w-full text-sm text-gray-700 placeholder-gray-400 outline-none bg-transparent"
          />
          <Flag className="w-4 h-4 text-gray-400 shrink-0" />
        </div>
      </div>

      <button className="flex items-center gap-1 text-sm text-blue-600 font-medium hover:text-blue-700">
        <Plus className="w-3.5 h-3.5" />
        Add Stop
      </button>
    </section>
  );
}
