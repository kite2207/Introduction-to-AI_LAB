import { useMemo } from "react";

/**
 * Generates a deterministic pseudo-random road-network graph (nodes + edges),
 * guarantees the whole graph is a single connected component, then computes
 * the longest reachable shortest-path from a start node via BFS.
 *
 * Returns:
 *  - nodes: [{ id, x, y, r, c }]
 *  - edges: [[nodeA, nodeB], ...]
 *  - path:  [nodeA, nodeB, ...] ordered route from start to the farthest node
 */
export function useRouteGraph() {
  return useMemo(() => {
    let seed = 42;
    const rand = () => {
      seed = (seed * 9301 + 49297) % 233280;
      return seed / 233280;
    };

    const width = 700;
    const height = 540;
    const cols = 12;
    const rows = 10;
    const nodeList = [];
    const grid = {};

    // --- Place nodes on a jittered grid ---
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (rand() > 0.42) continue;
        const jitterX = (rand() - 0.5) * 28;
        const jitterY = (rand() - 0.5) * 28;
        const x = (c / (cols - 1)) * width + jitterX;
        const y = (r / (rows - 1)) * height + jitterY;
        const node = { id: `${r}-${c}`, x, y, r, c };
        nodeList.push(node);
        grid[`${r}-${c}`] = node;
      }
    }

    // --- Randomly connect grid-adjacent nodes ---
    const edgeList = [];
    const edgeKeySet = new Set();
    const addEdge = (a, b) => {
      const key = a.id < b.id ? `${a.id}|${b.id}` : `${b.id}|${a.id}`;
      if (edgeKeySet.has(key)) return;
      edgeKeySet.add(key);
      edgeList.push([a, b]);
    };

    nodeList.forEach((n) => {
      const right = grid[`${n.r}-${n.c + 1}`];
      const down = grid[`${n.r + 1}-${n.c}`];
      if (right && rand() > 0.15) addEdge(n, right);
      if (down && rand() > 0.15) addEdge(n, down);
    });

    // --- Guarantee the whole graph is a single connected network ---
    // (otherwise a path from start to target can dead-end after a couple hops)
    const parent = {};
    nodeList.forEach((n) => (parent[n.id] = n.id));
    const find = (id) => {
      while (parent[id] !== id) {
        parent[id] = parent[parent[id]];
        id = parent[id];
      }
      return id;
    };
    const union = (a, b) => {
      const ra = find(a);
      const rb = find(b);
      if (ra !== rb) parent[ra] = rb;
    };
    edgeList.forEach(([a, b]) => union(a.id, b.id));

    const getComponents = () => {
      const comps = {};
      nodeList.forEach((n) => {
        const root = find(n.id);
        (comps[root] = comps[root] || []).push(n);
      });
      return comps;
    };

    let comps = getComponents();
    let compKeys = Object.keys(comps);
    let guardLoops = 0;
    while (compKeys.length > 1 && guardLoops < 100) {
      guardLoops++;
      const [rootA, ...rest] = compKeys;
      const groupA = comps[rootA];
      let best = null;
      let bestDist = Infinity;
      rest.forEach((rootB) => {
        const groupB = comps[rootB];
        groupA.forEach((a) => {
          groupB.forEach((b) => {
            const d = Math.hypot(a.x - b.x, a.y - b.y);
            if (d < bestDist) {
              bestDist = d;
              best = [a, b];
            }
          });
        });
      });
      if (best) {
        addEdge(best[0], best[1]);
        union(best[0].id, best[1].id);
      }
      comps = getComponents();
      compKeys = Object.keys(comps);
    }

    // --- BFS: find the longest reachable shortest-path from the start node ---
    const adjacency = {};
    nodeList.forEach((n) => (adjacency[n.id] = []));
    edgeList.forEach(([a, b]) => {
      adjacency[a.id].push(b);
      adjacency[b.id].push(a);
    });

    const bfs = (startNode) => {
      const dist = { [startNode.id]: 0 };
      const prev = {};
      const queue = [startNode];
      let qi = 0;
      while (qi < queue.length) {
        const cur = queue[qi++];
        adjacency[cur.id].forEach((nb) => {
          if (dist[nb.id] === undefined) {
            dist[nb.id] = dist[cur.id] + 1;
            prev[nb.id] = cur;
            queue.push(nb);
          }
        });
      }
      return { dist, prev };
    };

    const start = nodeList.find((n) => n.r <= 1 && n.c <= 1) || nodeList[0];
    const { dist, prev } = bfs(start);

    let target = start;
    let maxDist = 0;
    nodeList.forEach((n) => {
      if (dist[n.id] !== undefined && dist[n.id] > maxDist) {
        maxDist = dist[n.id];
        target = n;
      }
    });

    const pathNodes = [];
    let cur = target;
    while (cur && cur.id !== start.id) {
      pathNodes.unshift(cur);
      cur = prev[cur.id];
    }
    pathNodes.unshift(start);

    return { nodes: nodeList, edges: edgeList, path: pathNodes };
  }, []);
}
