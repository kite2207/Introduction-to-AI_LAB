import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  Polyline,
  Marker,
} from "react-leaflet";
import { useMap, useMapEvents } from "react-leaflet";
import { useEffect, useMemo, useState, Fragment } from "react";
import { divIcon } from "leaflet";

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

function ViewportObserver({ onChange }) {
  const map = useMapEvents({
    moveend: () => onChange({ zoom: map.getZoom(), bounds: map.getBounds() }),
    zoomend: () => onChange({ zoom: map.getZoom(), bounds: map.getBounds() }),
  });

  useEffect(() => {
    onChange({ zoom: map.getZoom(), bounds: map.getBounds() });
  }, [map, onChange]);

  return null;
}

const normalizePoint = (point) =>
  Array.isArray(point) ? [point[0], point[1]] : [point.lat, point.lng];

const bearingFromNorth = (from, to) =>
  (Math.atan2(to[1] - from[1], to[0] - from[0]) * 180) / Math.PI;

const routeArrowIcon = (rotation) =>
  divIcon({
    className: "route-arrow",
    html: `<div style="transform: rotate(${rotation}deg)">
      <svg width="22" height="22" viewBox="0 0 22 22">
        <path
          d="M11 2 L18 18 L11 14 L4 18 Z"
          fill="#ffffff"
          stroke="#7f1d1d"
          stroke-width="1.5"
          stroke-linejoin="round"
        />
      </svg>
    </div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  });

const edgeKey = (source, target) => {
  const a = String(source);
  const b = String(target);

  return a < b ? `${a}::${b}` : `${b}::${a}`;
};

const findGraphEdge = (edges, source, target) =>
  edges.find(
    (edge) =>
      String(edge.source) === String(source) &&
      String(edge.target) === String(target),
  ) ||
  edges.find(
    (edge) =>
      String(edge.source) === String(target) &&
      String(edge.target) === String(source),
  );

const getEdgePositions = (
  edge,
  nodeMap,
  source = edge.source,
  target = edge.target,
) => {
  let positions;

  if (Array.isArray(edge?.geometry) && edge.geometry.length > 1) {
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

const buildSegmentsFromTraceEdges = (traceEdges, edges, nodeMap) =>
  (traceEdges || [])
    .map((traceEdge, index) => {
      const source = traceEdge.source;
      const target = traceEdge.target;
      const edge = findGraphEdge(edges, source, target);

      if (!edge) {
        return null;
      }

      const positions = getEdgePositions(edge, nodeMap, source, target);

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

const buildRouteSegments = (path, edges, nodeMap) => {
  if (!path || path.length < 2) {
    return [];
  }

  const result = [];

  for (let i = 0; i < path.length - 1; i += 1) {
    const source = path[i];
    const target = path[i + 1];

    const edge = findGraphEdge(edges, source, target);

    if (!edge) {
      continue;
    }

    const positions = getEdgePositions(edge, nodeMap, source, target);

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
  const [viewport, setViewport] = useState({ zoom: 13, bounds: null });
  const hcmBounds = [
    [10.35, 106.35],
    [11.15, 107.05],
  ];

  const exploredEdges = simulation?.exploredEdges || [];

  const previousExploredEdges = simulation?.previousExploredEdges || [];

  const currentNode = simulation?.current || null;

  const previousKeys = useMemo(
    () =>
      new Set(
        previousExploredEdges.map((edge) => edgeKey(edge.source, edge.target)),
      ),
    [previousExploredEdges],
  );

  const newEdgeTrace = exploredEdges.filter(
    (traceEdge) =>
      !previousKeys.has(edgeKey(traceEdge.source, traceEdge.target)),
  );

  const oldEdgeTrace = exploredEdges.filter((traceEdge) =>
    previousKeys.has(edgeKey(traceEdge.source, traceEdge.target)),
  );

  const oldEdgeSegments = useMemo(
    () => buildSegmentsFromTraceEdges(oldEdgeTrace, edges, nodeMap),
    [oldEdgeTrace, edges, nodeMap],
  );

  const newEdgeSegments = useMemo(
    () => buildSegmentsFromTraceEdges(newEdgeTrace, edges, nodeMap),
    [newEdgeTrace, edges, nodeMap],
  );

  const routeSegments = useMemo(
    () => buildRouteSegments(path, edges, nodeMap),
    [path, edges, nodeMap],
  );

  const routeArrows = useMemo(
    () =>
      routeSegments.map((segment) => {
        const pts = segment.positions;
        const from = pts[0];
        const to = pts[pts.length - 1];

        return {
          key: `route-arrow-${segment.key}`,
          center: [(from[0] + to[0]) / 2, (from[1] + to[1]) / 2],
          rotation: bearingFromNorth(from, to),
        };
      }),
    [routeSegments],
  );

  const exploredNodeIds = simulation?.exploredNodes || [];

  const frontierNodeIds = simulation?.frontierNodes || [];

  const emphasizedNodeIds = useMemo(
    () =>
      new Set(
        [
          start,
          end,
          currentNode,
          ...waypoints,
          ...path,
          ...exploredNodeIds,
          ...frontierNodeIds,
        ].filter((id) => id != null),
      ),
    [
      start,
      end,
      currentNode,
      waypoints,
      path,
      exploredNodeIds,
      frontierNodeIds,
    ],
  );

  const visibleNodes = useMemo(() => {
    if (viewport.zoom < 15) {
      return nodes.filter((node) => emphasizedNodeIds.has(node.id));
    }

    return nodes.filter(
      (node) =>
        emphasizedNodeIds.has(node.id) ||
        !viewport.bounds ||
        viewport.bounds.contains([node.lat, node.lng]),
    );
  }, [nodes, emphasizedNodeIds, viewport]);

  const visibleBaseEdges = useMemo(() => {
    if (viewport.zoom < 16) {
      return [];
    }

    return edges.filter((edge) => {
      const source = nodeMap[edge.source];
      const target = nodeMap[edge.target];
      if (!source || !target || !viewport.bounds) {
        return Boolean(source && target);
      }
      return (
        viewport.bounds.contains([source.lat, source.lng]) ||
        viewport.bounds.contains([target.lat, target.lng])
      );
    });
  }, [edges, nodeMap, viewport]);

  return (
    <MapContainer
      center={[10.7769, 106.7009]}
      zoom={13}
      minZoom={11}
      maxZoom={18}
      maxBounds={hcmBounds}
      maxBoundsViscosity={1}
      preferCanvas
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
      <ViewportObserver onChange={setViewport} />

      <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />

      {/* Base graph is shown only when zoomed in to avoid visual clutter. */}
      {visibleBaseEdges.map((edge, index) => {
        const positions = getEdgePositions(edge, nodeMap);

        if (!positions) {
          return null;
        }

        return (
          <Polyline
            key={`base-${edge.source}-${edge.target}-${index}`}
            positions={positions}
            pathOptions={{
              color: "#94a3b8",
              weight: 1.5,
              opacity: 0.14,
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
          key={`route-outline-${segment.key}`}
          positions={segment.positions}
          pathOptions={{
            color: "#ffffff",
            weight: 11,
            opacity: 0.82,
          }}
        />
      ))}
      {routeSegments.map((segment) => (
        <Polyline
          key={segment.key}
          positions={segment.positions}
          pathOptions={{
            color: "#dc2626",
            weight: 6,
            opacity: 0.96,
          }}
        />
      ))}

      {/* Direction arrows along the selected route. */}
      {routeArrows.map((arrow) => (
        <Marker
          key={arrow.key}
          position={arrow.center}
          icon={routeArrowIcon(arrow.rotation)}
          interactive={false}
          keyboard={false}
        />
      ))}

      {visibleNodes.map((node) => {
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

        const isEmphasized = emphasizedNodeIds.has(node.id);
        const isSelectedEndpoint =
          node.id === start || node.id === end || waypoints.includes(node.id);

        return (
          <Fragment key={node.id}>
            {isSelectedEndpoint && (
              <CircleMarker
                center={[node.lat, node.lng]}
                radius={13}
                pathOptions={{
                  color,
                  weight: 3,
                  fillColor: color,
                  fillOpacity: 0.22,
                }}
                interactive={false}
              />
            )}

            <CircleMarker
              center={[node.lat, node.lng]}
              radius={isEmphasized ? 9 : 5.5}
              pathOptions={{
                color: "#ffffff",
                weight: isEmphasized ? 3 : 1.5,
                fillColor: color,
                fillOpacity: isEmphasized ? 1 : 0.72,
              }}
              eventHandlers={{
                click: () => onNodeClick(node.id),
              }}
            >
              <Popup>
                <strong>{node.name}</strong>
                <br />
                ID: {node.id}
              </Popup>
            </CircleMarker>
          </Fragment>
        );
      })}
    </MapContainer>
  );
}
