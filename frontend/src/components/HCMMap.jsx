import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
} from "react-leaflet";
import { useMap } from "react-leaflet";
import { useEffect, useMemo } from "react";

import L from "leaflet";

function FitHCM({ nodes }) {
  const map = useMap();

  useEffect(() => {
    if (nodes.length > 0) {
      const bounds = nodes.map((node) => [node.lat, node.lng]);

      map.fitBounds(bounds, {
        padding: [50, 50],
      });
    }
  }, [nodes, map]);

  return null;
}

const normalizePoint = (point) =>
  Array.isArray(point)
    ? [point[0], point[1]]
    : [point.lat, point.lng];

const edgeKey = (source, target) => {
  const a = String(source);
  const b = String(target);

  return a < b ? `${a}::${b}` : `${b}::${a}`;
};

const findGraphEdge = (edges, source, target) =>
  edges.find(
    (edge) =>
      String(edge.source) === String(source) &&
      String(edge.target) === String(target)
  ) ||
  edges.find(
    (edge) =>
      String(edge.source) === String(target) &&
      String(edge.target) === String(source)
  );

const getEdgePositions = (
  edge,
  nodeMap,
  source = edge.source,
  target = edge.target
) => {
  let positions;

  if (
    Array.isArray(edge?.geometry) &&
    edge.geometry.length > 1
  ) {
    positions = edge.geometry.map(normalizePoint);
  } else {
    const from = nodeMap[source];
    const to = nodeMap[target];

    if (!from || !to) {
      return null;
    }

    positions = [
      [from.lat, from.lng],
      [to.lat, to.lng],
    ];
  }

  // Keep the geometry direction consistent with the traversal.
  if (String(edge.source) !== String(source)) {
    positions = [...positions].reverse();
  }

  return positions;
};

const buildSegmentsFromTraceEdges = (
  traceEdges,
  edges,
  nodeMap
) =>
  (traceEdges || [])
    .map((traceEdge, index) => {
      const source = traceEdge.source;
      const target = traceEdge.target;
      const edge = findGraphEdge(
        edges,
        source,
        target
      );

      if (!edge) {
        return null;
      }

      const positions = getEdgePositions(
        edge,
        nodeMap,
        source,
        target
      );

      if (!positions || positions.length < 2) {
        return null;
      }

      return {
        key: `trace-${index}-${edgeKey(source, target)}`,
        source,
        target,
        edge,
        positions,
      };
    })
    .filter(Boolean);

const buildRouteSegments = (
  path,
  edges,
  nodeMap
) => {
  if (!path || path.length < 2) {
    return [];
  }

  const result = [];

  for (let i = 0; i < path.length - 1; i += 1) {
    const source = path[i];
    const target = path[i + 1];

    const edge = findGraphEdge(
      edges,
      source,
      target
    );

    if (!edge) {
      continue;
    }

    const positions = getEdgePositions(
      edge,
      nodeMap,
      source,
      target
    );

    if (!positions || positions.length < 2) {
      continue;
    }

    result.push({
      key: `route-${i}-${edgeKey(source, target)}`,
      source,
      target,
      edge,
      positions,
    });
  }

  return result;
};

export default function HCMMap({
  nodeMap,
  nodes = [],
  edges = [],
  start,
  end,
  waypoints = [],
  path = [],
  simulation = null,
  onNodeClick,
}) {
  const hcmBounds = [
    [10.35, 106.35],
    [11.15, 107.05],
  ];

  const exploredEdges =
    simulation?.exploredEdges || [];

  const previousExploredEdges =
    simulation?.previousExploredEdges || [];

  const currentNode =
    simulation?.current || null;

  const previousKeys = useMemo(
    () =>
      new Set(
        previousExploredEdges.map((edge) =>
          edgeKey(edge.source, edge.target)
        )
      ),
    [previousExploredEdges]
  );

  const newEdgeTrace = exploredEdges.filter(
    (traceEdge) =>
      !previousKeys.has(
        edgeKey(traceEdge.source, traceEdge.target)
      )
  );

  const oldEdgeTrace = exploredEdges.filter(
    (traceEdge) =>
      previousKeys.has(
        edgeKey(traceEdge.source, traceEdge.target)
      )
  );

  const oldEdgeSegments = useMemo(
    () =>
      buildSegmentsFromTraceEdges(
        oldEdgeTrace,
        edges,
        nodeMap
      ),
    [oldEdgeTrace, edges, nodeMap]
  );

  const newEdgeSegments = useMemo(
    () =>
      buildSegmentsFromTraceEdges(
        newEdgeTrace,
        edges,
        nodeMap
      ),
    [newEdgeTrace, edges, nodeMap]
  );

  const routeSegments = useMemo(
    () =>
      buildRouteSegments(
        path,
        edges,
        nodeMap
      ),
    [path, edges, nodeMap]
  );

  const exploredNodeIds =
    simulation?.exploredNodes || [];

  const frontierNodeIds =
    simulation?.frontierNodes || [];

  return (
    <MapContainer
      center={[10.7769, 106.7009]}
      zoom={13}
      minZoom={11}
      maxZoom={18}
      maxBounds={hcmBounds}
      maxBoundsViscosity={1}
      whenReady={(e) => {
        setTimeout(() => {
          e.target.invalidateSize();
        }, 300);
      }}
      style={{
        height: "100%",
        width: "100%",
      }}
    >
      <FitHCM nodes={nodes} />

      <TileLayer
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {/* Base graph: always remains visible underneath. */}
      {edges.map((edge) => {
        const positions = getEdgePositions(
          edge,
          nodeMap
        );

        if (!positions) {
          return null;
        }

        return (
          <Polyline
            key={`base-${edge.source}-${edge.target}`}
            positions={positions}
            pathOptions={{
              color: "#94a3b8",
              weight: 2,
              opacity: 0.28,
            }}
          />
        );
      })}

      {/* Edges explored in previous steps: BLUE. */}
      {oldEdgeSegments.map((segment) => (
        <Polyline
          key={segment.key}
          positions={segment.positions}
          pathOptions={{
            color: "#2563eb",
            weight: 6,
            opacity: 0.9,
          }}
        />
      ))}

      {/* Edge(s) newly discovered at the CURRENT step: PURPLE. */}
      {newEdgeSegments.map((segment) => (
        <Polyline
          key={segment.key}
          positions={segment.positions}
          pathOptions={{
            color: "#7c3aed",
            weight: 8,
            opacity: 0.98,
          }}
        />
      ))}

      {/* Final selected route: RED. */}
      {routeSegments.map((segment) => (
        <Polyline
          key={segment.key}
          positions={segment.positions}
          pathOptions={{
            color: "#dc2626",
            weight: 9,
            opacity: 0.96,
          }}
        />
      ))}

      {nodes.map((node) => {
        let color = "#9ca3af";

        if (frontierNodeIds.includes(node.id)) {
          color = "#f59e0b";
        }

        if (exploredNodeIds.includes(node.id)) {
          color = "#2563eb";
        }

        if (node.id === currentNode) {
          color = "#7c3aed";
        }

        if (waypoints.includes(node.id)) {
          color = "#f97316";
        }

        if (node.id === start) {
          color = "#16a34a";
        }

        if (node.id === end) {
          color = "#dc2626";
        }

        const icon = new L.DivIcon({
          html: `
            <div style="
              background:${color};
              width:15px;
              height:15px;
              border-radius:50%;
              border:2px solid white;
              box-shadow:0 1px 3px rgba(0,0,0,.35);
            "></div>
          `,
          className: "",
        });

        return (
          <Marker
            key={node.id}
            position={[node.lat, node.lng]}
            icon={icon}
            eventHandlers={{
              click: () => onNodeClick(node.id),
            }}
          >
            <Popup>
              <strong>{node.name}</strong>
              <br />
              ID: {node.id}
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  );
}
