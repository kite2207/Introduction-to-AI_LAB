
export default function Graph({nodes, edges, start, end, onNodeClick}) {
  return (
    <svg width="100%" height="100%" viewBox="0 0 850 650">
      {edges.map((e,i)=>{
        const a = nodes[e.from];
        const b = nodes[e.to];

        return (
          <line
            key={i}
            x1={a.x}
            y1={a.y}
            x2={b.x}
            y2={b.y}
            stroke="#888"
            strokeWidth="2"
          />
        )
      })}

      {nodes.map(node=>(
        <g key={node.id}
          onClick={()=>onNodeClick(node.id)}
          style={{cursor:"pointer"}}
        >
          <circle
            cx={node.x}
            cy={node.y}
            r="15"
            fill={
              node.id === start ? "green" :
              node.id === end ? "red" :
              "blue"
            }
          />

          <text
            x={node.x-6}
            y={node.y+5}
            fill="white"
            fontSize="12"
          >
            {node.id}
          </text>
        </g>
      ))}
    </svg>
  );
}
