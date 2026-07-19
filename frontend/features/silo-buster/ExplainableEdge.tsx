import { BaseEdge, EdgeLabelRenderer, getBezierPath, EdgeProps } from "@xyflow/react";

export function ExplainableEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <BaseEdge path={edgePath} markerEnd={markerEnd} style={{ ...style, strokeWidth: 2, stroke: 'var(--color-primary)' }} />
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: 'all',
          }}
          className="nodrag nopan bg-background border border-primary text-primary px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider shadow-lg"
        >
          {data?.reason ? String(data.reason) : "LINKED"}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
