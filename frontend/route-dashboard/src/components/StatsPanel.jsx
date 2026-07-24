import React from "react";
import { Route, Clock, DollarSign } from "lucide-react";

export default function StatsPanel() {
  return (
    <div className="absolute left-96 ml-4 top-4 z-10 w-64 bg-white rounded-xl shadow-xl border border-gray-100 p-4 animate-[fadeIn_0.4s_ease-out]">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Route Statistics</h3>
      <div className="space-y-3">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-blue-50 flex items-center justify-center shrink-0">
            <Route className="w-3.5 h-3.5 text-blue-600" />
          </div>
          <div className="flex-1 flex items-center justify-between">
            <span className="text-xs text-gray-500">Total Distance</span>
            <span className="text-xs font-semibold text-gray-900">12.5 km</span>
          </div>
        </div>
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-emerald-50 flex items-center justify-center shrink-0">
            <Clock className="w-3.5 h-3.5 text-emerald-600" />
          </div>
          <div className="flex-1 flex items-center justify-between">
            <span className="text-xs text-gray-500">Estimated Time</span>
            <span className="text-xs font-semibold text-gray-900">45 mins</span>
          </div>
        </div>
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-amber-50 flex items-center justify-center shrink-0">
            <DollarSign className="w-3.5 h-3.5 text-amber-600" />
          </div>
          <div className="flex-1 flex items-center justify-between">
            <span className="text-xs text-gray-500">Total Cost</span>
            <span className="text-xs font-semibold text-gray-900">85.2</span>
          </div>
        </div>
      </div>
    </div>
  );
}
