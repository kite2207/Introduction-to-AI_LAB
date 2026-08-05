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
  Array.isArray(point) ? [point[0], point[1]] : [point.lat, point.lng];

const getEdgePositions = (edge, nodeMap) => {
  if (Array.isArray(edge?.geometry) && edge.geometry.length > 1) {
    return edge.geometry.map(normalizePoint);
  }

  const from = nodeMap[edge.source];
  const to = nodeMap[edge.target];

  if (!from || !to) return null;

  return [
    [from.lat, from.lng],
    [to.lat, to.lng],
  ];
};

const buildRoutePositions = (path, edges, nodeMap) => {
  if (!path || path.length < 2) return [];

  const routePositions = [];

  for (let i = 0; i < path.length - 1; i += 1) {
    const fromId = path[i];
    const toId = path[i + 1];
    const edge = edges.find(
      (candidate) =>
        (candidate.source === fromId && candidate.target === toId) ||
        (candidate.source === toId && candidate.target === fromId),
    );

    const fallbackPositions = [];
    const fromNode = nodeMap[fromId];
    const toNode = nodeMap[toId];

    if (fromNode && toNode) {
      fallbackPositions.push([fromNode.lat, fromNode.lng]);
      fallbackPositions.push([toNode.lat, toNode.lng]);
    }

    const segmentPositions = edge ? getEdgePositions(edge, nodeMap) : fallbackPositions;

    if (!segmentPositions || segmentPositions.length === 0) continue;

    if (routePositions.length === 0) {
      routePositions.push(...segmentPositions);
      continue;
    }

    const lastPoint = routePositions[routePositions.length - 1];
    const firstPoint = segmentPositions[0];
    const isDuplicate =
      lastPoint[0] === firstPoint[0] &&
      lastPoint[1] === firstPoint[1];

    routePositions.push(...(isDuplicate ? segmentPositions.slice(1) : segmentPositions));
  }

  return routePositions;
};

export default function HCMMap({
  nodeMap,
  nodes = [],
  edges = [],
  start,
  end,
  waypoints = [],
  path = [],
  onNodeClick,
}) {
  const routePositions = useMemo(
    () => buildRoutePositions(path, edges, nodeMap),
    [path, edges, nodeMap],
  );

  const hcmBounds = [
      [10.35, 106.35], // góc Tây Nam
      [11.15, 107.05], // góc Đông Bắc
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

        if (!positions) return null;

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

      <Polyline positions={routePositions} color="red" weight={10} />

      {nodes.map((node) => {
        let color = "blue";

        if (node.id === start) color = "green";

        if (node.id === end) color = "red";

        if (waypoints.includes(node.id)) color = "orange";

        const icon = new L.DivIcon({
          html: `

<div style="
background:${color};
width:15px;
height:15px;
border-radius:50%;
border:2px solid white;
">
</div>

`,

          className: "",
        });

        return (
          <Marker
            key={node.id}
            position={[node.lat, node.lng]}
            icon={icon}
            eventHandlers={{
              click: () => {
                onNodeClick(node.id);
              },
            }}
          >
            <Popup>
              {node.name}
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  );
}
