import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
} from "react-leaflet";
import { useMap } from "react-leaflet";
import { useEffect } from "react";

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
  Array.isArray(point) ? [point[0], point[1]] : [point.lat, point.lng];

const getExploredEdgeSegments = (exploredPath, edges, nodeMap) => {
  if (!exploredPath || exploredPath.length < 2) {
    return [];
  }

  const segments = [];
  const seen = new Set();

  for (let i = 0; i < exploredPath.length - 1; i += 1) {
    const fromId = exploredPath[i];
    const toId = exploredPath[i + 1];

    // Only draw a line when the two explored nodes are actually connected
    // by an edge in the graph. This prevents the previous "spider web"
    // effect caused by connecting arbitrary exploration-order nodes.
    const edge = edges.find(
      (candidate) =>
        (candidate.source === fromId && candidate.target === toId) ||
        (candidate.source === toId && candidate.target === fromId),
    );

    if (!edge) {
      continue;
    }

    const key = [edge.source, edge.target].sort().join("::");

    if (seen.has(key)) {
      continue;
    }

    const positions = getEdgePositions(edge, nodeMap);

    if (positions && positions.length > 1) {
      seen.add(key);
      segments.push({
        key: `explored-${key}`,
        positions,
      });
    }
  }

  return segments;
};

const getEdgePositions = (edge, nodeMap) => {
  if (Array.isArray(edge?.geometry) && edge.geometry.length > 1) {
    return edge.geometry.map(normalizePoint);
  }

  const from = nodeMap[edge.source];
  const to = nodeMap[edge.target];

  if (!from || !to) {
    return null;
  }

  return [
    [from.lat, from.lng],
    [to.lat, to.lng],
  ];
};

export default function HCMMap({
  nodeMap,
  nodes = [],
  edges = [],
  routePositions = [],
  start,
  end,
  waypoints = [],
  path = [],
  exploredNodes = [],
  onNodeClick,
}) {
  const hcmBounds = [
    [10.35, 106.35],
    [11.15, 107.05],
  ];

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

      <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />

      {edges.map((edge) => {
        const positions = getEdgePositions(edge, nodeMap);

        if (!positions) {
          return null;
        }

        return (
          <Polyline
            key={`${edge.source}-${edge.target}`}
            positions={positions}
            pathOptions={{
              color: "#5795ff",
              weight: 3,
              opacity: 0.4,
            }}
          />
        );
      })}

      {/* Chỉ vẽ explored bằng các EDGE thực sự tồn tại trong graph.
          Không nối trực tiếp hai node chỉ vì chúng đứng cạnh nhau trong
          explored_nodes, nên sẽ không còn đường chéo chằng chịt. */}
      {getExploredEdgeSegments(exploredNodes, edges, nodeMap).map((segment) => (
        <Polyline
          key={segment.key}
          positions={segment.positions}
          pathOptions={{
            color: "#2563eb",
            weight: 5,
            opacity: 0.9,
          }}
        />
      ))}

      {routePositions.length > 1 && (
        <Polyline
          positions={routePositions.map((point) => normalizePoint(point))}
          pathOptions={{
            color: "red",
            weight: 10,
            opacity: 0.95,
          }}
        />
      )}

      {nodes.map((node) => {
        let color = "#9ca3af";

        // App chỉ truyền exploredNodes khi step > 0.
        // Vì vậy map mặc định sẽ không tô toàn bộ node đã explored.
        if (exploredNodes.includes(node.id)) {
          color = "#2563eb";
        }

        if (waypoints.includes(node.id)) {
          color = "orange";
        }

        if (node.id === start) {
          color = "green";
        }

        if (node.id === end) {
          color = "red";
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
