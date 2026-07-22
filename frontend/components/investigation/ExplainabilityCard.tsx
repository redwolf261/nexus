import { AlertTriangle, MapPin, Network, Activity, HelpCircle, CheckCircle } from "lucide-react";
import { useState } from "react";

// The IntelligenceExplanation schema from Phase 7.1
export interface EvidenceItem {
  dimension: string;
  description: string;
  raw_value: any;
  weight: number;
  contributed_score: number;
}

export interface ConfidenceScore {
  evidence_quality: number;
  data_completeness: number;
  algorithm_confidence: number;
  source_reliability: number;
  recency_weight: number;
  overall_confidence: number;
}

export interface IntelligenceExplanation {
  inference_type: string;
  observation: string;
  evidence: EvidenceItem[];
  analytical_rule: string;
  inference: string;
  confidence: ConfidenceScore;
  recommended_action?: string;
  alternative_explanations?: string[];
}

function getConfidenceBand(confidence: number): { label: string; color: string; bg: string } {
  if (confidence >= 0.80) {
    return { label: "CRITICAL", color: "text-destructive", bg: "bg-destructive/20" };
  } else if (confidence >= 0.60) {
    return { label: "HIGH", color: "text-chart-2", bg: "bg-chart-2/20" };
  } else if (confidence >= 0.40) {
    return { label: "MEDIUM", color: "text-chart-3", bg: "bg-chart-3/20" };
  } else {
    return { label: "LOW", color: "text-muted-foreground", bg: "bg-muted" };
  }
}

export function ExplainabilityCard({ expl }: { expl: IntelligenceExplanation }) {
  const [expanded, setExpanded] = useState(false);
  const confPct = Math.round(expl.confidence.overall_confidence * 100);
  const confBand = getConfidenceBand(expl.confidence.overall_confidence);

  let Icon = HelpCircle;
  let color = "text-muted-foreground";
  if (expl.inference_type === "CRIME_SERIES") { Icon = MapPin; color = "text-destructive"; }
  else if (expl.inference_type === "GRAPH_COMMUNITY" || expl.inference_type.includes("GRAPH")) { Icon = Network; color = "text-primary"; }
  else if (expl.inference_type === "TEMPORAL_ANOMALY") { Icon = Activity; color = "text-chart-2"; }
  else if (expl.inference_type === "SPATIAL_CLUSTER") { Icon = MapPin; color = "text-chart-4"; }

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden flex flex-col shadow-sm hover:border-primary/50 transition-colors">
      {/* Header Summary */}
      <div 
        className="p-4 flex items-start gap-4 cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        <div className={`p-2 rounded bg-muted ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold tracking-wider px-2 py-0.5 rounded bg-muted uppercase text-foreground">
              {expl.inference_type.replace(/_/g, " ")}
            </span>
            <span className={`text-[10px] font-mono font-bold tracking-wider px-2 py-0.5 rounded ${confBand.bg} ${confBand.color}`}>
              {confBand.label} ({confPct}%)
            </span>
          </div>
          <div className="text-sm font-bold text-foreground mb-1 leading-tight">{expl.inference}</div>
          <div className="text-xs text-muted-foreground truncate">{expl.observation}</div>
        </div>
      </div>

      {/* Expanded Provenance Trace */}
      {expanded && (
        <div className="p-4 pt-0 border-t border-border/50 bg-muted/30 flex flex-col gap-4 mt-2">
           
           {/* Evidence Breakdown */}
           <div>
              <div className="text-[10px] uppercase font-bold text-muted-foreground tracking-widest mb-2 mt-2 flex items-center gap-1">
                <CheckCircle className="w-3 h-3"/> Supporting Evidence
              </div>
              <div className="space-y-1">
                {expl.evidence.map((ev, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs font-mono">
                    <span className="text-primary font-bold min-w-[20px] text-right">{(ev.weight * 100).toFixed(0)}%</span>
                    <span className="text-muted-foreground break-words">{ev.description}</span>
                  </div>
                ))}
              </div>
           </div>

           {/* Analytical Rule */}
           <div>
             <div className="text-[10px] uppercase font-bold text-muted-foreground tracking-widest mb-1">Analytical Rule</div>
             <div className="text-xs font-mono bg-background border border-border p-2 rounded text-foreground">
               {expl.analytical_rule}
             </div>
           </div>

           {/* Recommended Action */}
           {expl.recommended_action && (
             <div className="bg-chart-2/10 border border-chart-2/30 p-2 rounded">
               <div className="text-[10px] uppercase font-bold text-chart-2 tracking-widest mb-1">Recommended Action</div>
               <div className="text-xs text-foreground font-medium">{expl.recommended_action}</div>
             </div>
           )}

           {/* Confidence Trace */}
           <div className="text-[10px] font-mono text-muted-foreground flex flex-wrap gap-2 pt-2 border-t border-border/50">
             <span>Data Quality: {(expl.confidence.evidence_quality * 100).toFixed(0)}%</span>
             <span>Completeness: {(expl.confidence.data_completeness * 100).toFixed(0)}%</span>
             <span>Algorithm: {(expl.confidence.algorithm_confidence * 100).toFixed(0)}%</span>
             <span>Source: {(expl.confidence.source_reliability * 100).toFixed(0)}%</span>
           </div>
        </div>
      )}
    </div>
  );
}
