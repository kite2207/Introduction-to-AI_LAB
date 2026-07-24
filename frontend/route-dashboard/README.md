# Route Dashboard

A small React + Tailwind + lucide-react project that recreates and enhances
a route-planning dashboard UI, with an animated node/edge graph, a search
flow, and a step-by-step route "visualizer."

## Structure

```
src/
├── App.jsx                  # Owns all state, wires everything together
├── index.jsx                # Entry point (mounts <App /> into #root)
├── index.css                # Tailwind directives
├── hooks/
│   └── useRouteGraph.js     # Generates the road-network graph + BFS path
└── components/
    ├── Sidebar.jsx          # Left panel shell (header + inputs + settings + search)
    ├── RouteInputs.jsx      # Start / End location fields, "Add Stop"
    ├── RouteSettings.jsx    # Optimization method toggle + algorithm dropdown
    ├── RouteResults.jsx     # Visualizer controls, AI explanation, reset (post-search)
    ├── StatsPanel.jsx       # Floating "Route Statistics" card (post-search)
    ├── MapArea.jsx          # Map background + SVG graph rendering
    └── ZoomControl.jsx      # Floating +/- zoom buttons
```

## How it works

- `useRouteGraph` builds a deterministic pseudo-random grid of nodes, connects
  them with edges, guarantees the whole graph is a single connected network
  (via union-find), then finds a long real route between two nodes using BFS.
- `App` holds the `hasSearched` / `step` / `zoom` state and derives which
  nodes are "revealed" (orange) based on the current step.
- `MapArea` recolors nodes orange and edges blue only when both endpoints of
  an edge are in the currently revealed set — everything else stays grey.

## Running it

This is a standard Vite + React + Tailwind project. From the project root:

```bash
npm install
npm run dev
```

Then open the local URL Vite prints (usually `http://localhost:5173`).

