"use client";

import { useState, useEffect } from "react";
import { useSiloBuster } from "@/hooks/useApi";
import { Background, Controls, Edge, Node, ReactFlow, useReactFlow, ReactFlowProvider } from "@xyflow/react";
import '@xyflow/react/dist/style.css';
import { EntityNode } from "./CustomNode";
import { ExplainableEdge } from "./ExplainableEdge";
import { useInvestigationDrawer } from "@/components/investigation/InvestigationDrawer";
import { Play } from "lucide-react";

const nodeTypes = {
  entity: EntityNode,
};

const edgeTypes = {
  explainable: ExplainableEdge,
};

function SiloBusterGraphInner({ targetFir }: { targetFir: string }) {
  const { data, isLoading, error } = useSiloBuster(targetFir);
  const { openDrawer } = useInvestigationDrawer();
  const { fitView } = useReactFlow();
  
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [isTracing, setIsTracing] = useState(false);

  useEffect(() => {
    if (!data) return;
    
    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];

    // Root FIR Node
    newNodes.push({
      id: data.fir_id,
      type: "entity",
      position: { x: 400, y: 50 },
      data: { id: data.fir_id, type: "FIR", isHighlighted: false }
    });

    data.linked_crimes.forEach((link, index) => {
      const xOffset = index * 250;
      
      if (!newNodes.find(n => n.id === link.entity_id)) {
        newNodes.push({
          id: link.entity_id,
          type: "entity",
          position: { x: 200 + xOffset, y: 250 },
          data: { id: link.entity_id, type: link.shared_type[0], isHighlighted: false }
        });
      }

      if (!newNodes.find(n => n.id === link.linked_fir)) {
        newNodes.push({
          id: link.linked_fir,
          type: "entity",
          position: { x: 200 + xOffset, y: 450 },
          data: { id: link.linked_fir, type: "FIR", isHighlighted: false }
        });
      }

      newEdges.push({
        id: `e-${data.fir_id}-${link.entity_id}`,
        source: data.fir_id,
        target: link.entity_id,
        type: "explainable",
        animated: true,
        style: { strokeOpacity: 0.2 },
        data: { reason: `Shared ${link.shared_type[0]}` }
      });

      newEdges.push({
        id: `e-${link.entity_id}-${link.linked_fir}`,
        source: link.entity_id,
        target: link.linked_fir,
        type: "explainable",
        animated: true,
        style: { strokeOpacity: 0.2 },
        data: { reason: "Used in crime" }
      });
    });

    setNodes(newNodes);
    setEdges(newEdges);
  }, [data]);

  const handleTrace = () => {
    if (isTracing || !nodes.length) return;
    setIsTracing(true);

    let step = 0;
    
    // Reset all highlights
    setNodes(ns => ns.map(n => ({ ...n, data: { ...n.data, isHighlighted: false } })));
    setEdges(es => es.map(e => ({ ...e, style: { strokeOpacity: 0.2 } })));

    const interval = setInterval(() => {
      if (step >= nodes.length) {
        clearInterval(interval);
        setIsTracing(false);
        return;
      }

      const nodeToHighlight = nodes[step];
      
      setNodes(ns => ns.map(n => 
        n.id === nodeToHighlight.id 
          ? { ...n, data: { ...n.data, isHighlighted: true } } 
          : n
      ));

      setEdges(es => es.map(e => 
        e.target === nodeToHighlight.id 
          ? { ...e, style: { strokeOpacity: 1, strokeWidth: 3, stroke: '#00e5ff' } } 
          : e
      ));

      step++;
    }, 1000);
  };

  const onNodeClick = (event: any, node: Node) => {
    openDrawer(node.id, node.data.type as any);
  };

  if (isLoading) return <div className="w-full h-full flex items-center justify-center font-mono animate-pulse">ANALYZING CROSS-JURISDICTIONAL LINKS...</div>;
  if (error || !data) return <div className="w-full h-full flex items-center justify-center text-destructive">LINK ANALYSIS FAILED.</div>;

  return (
    <div className="w-full h-full relative flex">
      <div className="flex-1 h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          onNodeClick={onNodeClick}
          onInit={() => setTimeout(fitView, 100)}
          className="bg-background"
        >
          <Background color="var(--color-border)" gap={24} size={2} />
          <Controls className="bg-card border-border fill-foreground" />
        </ReactFlow>
      </div>
      
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-[400]">
        <button 
          onClick={handleTrace}
          disabled={isTracing}
          className="flex items-center gap-2 bg-primary text-primary-foreground px-6 py-3 rounded-full font-bold shadow-xl hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          <Play className="w-5 h-5" />
          {isTracing ? "TRACING PATH..." : "TRACE INVESTIGATION"}
        </button>
      </div>

      <div className="w-96 h-full border-l border-border bg-sidebar p-6 flex flex-col gap-6">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-primary">Silo Buster Analysis</h2>
          <p className="text-sm text-muted-foreground mt-1">Cross-jurisdictional intelligence report</p>
        </div>
        
        <div className="bg-card border border-border p-4 rounded-md">
          <div className="text-xs uppercase tracking-wider text-muted-foreground mb-1">Target FIR</div>
          <div className="font-mono text-lg">{data.fir_id}</div>
        </div>

        <div className="bg-card border border-border p-4 rounded-md flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-wider text-muted-foreground mb-1">AI Confidence</div>
            <div className="font-bold text-2xl text-chart-1">{data.confidence * 100}%</div>
          </div>
          <div className="text-right">
            <div className="text-xs uppercase tracking-wider text-muted-foreground mb-1">Link Score</div>
            <div className="font-bold text-2xl text-chart-2">{data.score}</div>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-2">Explainability Engine</h3>
          {data.reasons.map((reason, idx) => (
            <div key={idx} className="bg-primary/10 border border-primary/20 text-primary px-3 py-2 rounded text-sm font-mono leading-relaxed">
              &gt; {reason}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function SiloBusterGraph({ targetFir }: { targetFir: string }) {
  return (
    <ReactFlowProvider>
      <SiloBusterGraphInner targetFir={targetFir} />
    </ReactFlowProvider>
  );
}
