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
  const routePositions = path
    .map((id) => {
      const node = nodes.find((n) => n.id === id);

      if (!node) return null;

      return [node.lat, node.lng];
    })
    .filter(Boolean);
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
        const from = nodeMap[edge.source];
        const to = nodeMap[edge.target];

        if (!from || !to) return null;

        return (
          <Polyline
            key={edge.source + edge.target}
            positions={[
              [from.lat, from.lng],
              [to.lat, to.lng],
            ]}
            pathOptions={{
              color: "#5795ff",
              weight: 1,
              opacity: 0.4,
            }}
          />
        );
      })}

      <Polyline positions={routePositions} color="red" weight={6} />

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
