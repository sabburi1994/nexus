import React, { useMemo } from "react";
import type { AstEdge, BlastRadiusContract } from "../types";

interface Props {
  files: string[];
  edges: AstEdge[];
  selectedTarget: string;
  blastRadius: BlastRadiusContract;
  onSelectFile: (file: string) => void;
}

export const AstDependencyGraph: React.FC<Props> = ({
  files,
  edges,
  selectedTarget,
  blastRadius,
  onSelectFile,
}) => {
  const layout = useMemo(() => {
    const incomingCount: Record<string, number> = {};
    files.forEach((f) => {
      incomingCount[f] = 0;
    });
    edges.forEach((e) => {
      incomingCount[e.target] = (incomingCount[e.target] ?? 0) + 1;
    });

    // Compute simple longest-path topological depth so nodes flow cleanly left -> right.
    const depth: Record<string, number> = {};
    files.forEach((f) => {
      depth[f] = f.toLowerCase().includes("test") ? 3 : 0;
    });

    for (let iter = 0; iter < files.length; iter++) {
      edges.forEach((e) => {
        const nextDepth = (depth[e.source] ?? 0) + 1;
        if (nextDepth > (depth[e.target] ?? 0)) {
          depth[e.target] = Math.min(3, nextDepth);
        }
      });
    }

    const columns = new Map<number, string[]>();
    files.forEach((f) => {
      const col = depth[f] ?? 0;
      const list = columns.get(col) ?? [];
      list.push(f);
      columns.set(col, list);
    });

    const maxRows = Math.max(1, ...Array.from(columns.values()).map((c) => c.length));
    const colKeys = Array.from(columns.keys()).sort((a, b) => a - b);
    const width = 680;
    const height = Math.max(170, maxRows * 58 + 34);
    const colWidth = colKeys.length > 1 ? (width - 170) / (colKeys.length - 1) : 0;

    const coords: Record<string, { x: number; y: number }> = {};
    colKeys.forEach((col, cIdx) => {
      const colFiles = columns.get(col) ?? [];
      const rowStep = height / (colFiles.length + 1);
      colFiles.forEach((f, rIdx) => {
        coords[f] = {
          x: Math.round(85 + cIdx * colWidth),
          y: Math.round(rowStep * (rIdx + 1)),
        };
      });
    });

    return { width, height, coords };
  }, [files, edges]);

  const directSet = new Set(blastRadius.directDependents);
  const indirectSet = new Set(blastRadius.indirectDependents);
  const testSet = new Set(blastRadius.affectedTests);

  const getNodeStyle = (file: string) => {
    if (file === selectedTarget) {
      return { fill: "#172a2e", stroke: "#172a2e", text: "#fffdf8", tag: "TARGET" };
    }
    if (testSet.has(file)) {
      return { fill: "#e6f4ee", stroke: "#0f7657", text: "#0f7657", tag: "TEST" };
    }
    if (directSet.has(file)) {
      return { fill: "#fbece7", stroke: "#bd513d", text: "#7f2419", tag: "DIRECT" };
    }
    if (indirectSet.has(file)) {
      return { fill: "#eef1fb", stroke: "#263aa8", text: "#263aa8", tag: "INDIRECT" };
    }
    return { fill: "#fffdf8", stroke: "#c9d1cf", text: "#3a494b", tag: "CLEAN" };
  };

  if (files.length === 0) return null;

  return (
    <section className="editorial-card p-5">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#e5ddd0] pb-3">
        <div>
          <p className="editorial-kicker">Python ast Import DAG · Click Any Node to Shift Target</p>
          <h3 className="mt-0.5 text-sm font-semibold text-[#172a2e]">Visual Dependency &amp; Blast-Radius Graph</h3>
        </div>
        <div className="flex flex-wrap gap-2 text-[10px] font-mono">
          <span className="rounded bg-[#172a2e] px-2 py-0.5 text-[#fffdf8]">Target</span>
          <span className="rounded border border-[#bd513d] bg-[#fbece7] px-2 py-0.5 text-[#7f2419]">Direct</span>
          <span className="rounded border border-[#263aa8] bg-[#eef1fb] px-2 py-0.5 text-[#263aa8]">Indirect</span>
          <span className="rounded border border-[#0f7657] bg-[#e6f4ee] px-2 py-0.5 text-[#0f7657]">Test Suite</span>
        </div>
      </div>

      <div className="mt-3 overflow-x-auto rounded border border-[#e5ddd0] bg-[#f8f4ec] p-2">
        <svg
          viewBox={`0 0 ${layout.width} ${layout.height}`}
          className="h-auto w-full min-w-[520px]"
          role="img"
          aria-label="AST Dependency Graph"
        >
          <defs>
            <marker id="nx-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#7c8784" />
            </marker>
            <marker
              id="nx-arrow-hot"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#bd513d" />
            </marker>
          </defs>

          {edges.map((edge, idx) => {
            const from = layout.coords[edge.source];
            const to = layout.coords[edge.target];
            if (!from || !to) return null;
            const hot =
              edge.source === selectedTarget ||
              directSet.has(edge.source) ||
              edge.target === selectedTarget;
            const x1 = from.x + 68;
            const x2 = to.x - 72;
            const midX = (x1 + x2) / 2;
            const pathD = `M ${x1} ${from.y} C ${midX} ${from.y}, ${midX} ${to.y}, ${x2} ${to.y}`;
            return (
              <path
                key={`${edge.source}-${edge.target}-${idx}`}
                d={pathD}
                fill="none"
                stroke={hot ? "#bd513d" : "#b8af9f"}
                strokeWidth={hot ? 2 : 1.4}
                markerEnd={hot ? "url(#nx-arrow-hot)" : "url(#nx-arrow)"}
              />
            );
          })}

          {files.map((file) => {
            const pt = layout.coords[file];
            if (!pt) return null;
            const st = getNodeStyle(file);
            const shortName = file.length > 18 ? `...${file.slice(-15)}` : file;
            return (
              <g
                key={file}
                transform={`translate(${pt.x - 68}, ${pt.y - 18})`}
                onClick={() => onSelectFile(file)}
                className="cursor-pointer"
              >
                <rect
                  width={136}
                  height={36}
                  rx={6}
                  fill={st.fill}
                  stroke={st.stroke}
                  strokeWidth={file === selectedTarget ? 2 : 1.5}
                />
                <text
                  x={68}
                  y={16}
                  textAnchor="middle"
                  fill={st.text}
                  style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "10.5px", fontWeight: 600 }}
                >
                  {shortName}
                </text>
                <text
                  x={68}
                  y={29}
                  textAnchor="middle"
                  fill={st.text}
                  opacity={0.78}
                  style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "8.5px", fontWeight: 700 }}
                >
                  {st.tag}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </section>
  );
};
