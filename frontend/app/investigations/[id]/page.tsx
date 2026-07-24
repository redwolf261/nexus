"use client";

import { useInvestigationMutations } from "@/hooks/useApi";
import { useWorkspaceOrchestrator, useWorkspaceMeta, useWorkspaceEntities, useWorkspaceTimeline, useWorkspaceNotes } from "@/hooks/useWorkspace";
import { useInvestigationDrawer } from "@/components/investigation/InvestigationDrawer";
import { useLiveWorkspace } from "@/hooks/useLiveWorkspace";
import { ReplayControls } from "@/components/investigation/ReplayControls";
import { ArrowLeft, Clock, Save, Trash2, Edit3, ShieldAlert, Activity, Play, Pause, SkipForward } from "lucide-react";
import Link from "next/link";
import { use, useState, useEffect } from "react";

export default function WorkspacePage({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  
  // Real-time Event Subscription
  const { isConnected } = useLiveWorkspace(unwrappedParams.id);

  // Orchestrator loads the data and populates granular caches
  const { isLoading, data: workspaceObj } = useWorkspaceOrchestrator(unwrappedParams.id);
  
  const { data: inv } = useWorkspaceMeta(unwrappedParams.id);
  const { data: entities } = useWorkspaceEntities(unwrappedParams.id);
  const { data: timeline } = useWorkspaceTimeline(unwrappedParams.id);
  const { data: notes } = useWorkspaceNotes(unwrappedParams.id);

  const { createNote, removeEntity } = useInvestigationMutations();
  const { openDrawer } = useInvestigationDrawer();

  const [noteText, setNoteText] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const notesArr = Array.isArray(notes) ? (notes as any[]) : [];

  useEffect(() => {
    if (notesArr.length > 0 && !noteText) {
      setNoteText(notesArr[0].markdown || "");
    }
  }, [notes]);

  // Auto-save debouncer
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (noteText && (notesArr.length === 0 || notesArr[0].markdown !== noteText)) {
        setIsSaving(true);
        await createNote.mutateAsync({ invId: unwrappedParams.id, markdown: noteText });
        setIsSaving(false);
      }
    }, 5000); // 5 sec auto-save
    return () => clearTimeout(timer);
  }, [noteText, unwrappedParams.id, notes, createNote]);

  const [activeTab, setActiveTab] = useState("WORKSPACE");

  if (isLoading) return <div className="p-8 font-mono animate-pulse">ESTABLISHING WORKSPACE LINK...</div>;
  if (!inv) return <div className="p-8 font-mono text-destructive">WORKSPACE NOT FOUND</div>;

  return (
    <div className="h-full flex flex-col bg-background relative overflow-hidden">
      <div className="flex-none p-4 border-b border-border bg-card flex items-center justify-between z-10">
        <div className="flex items-center gap-4">
          <Link href="/investigations" className="text-muted-foreground hover:text-foreground">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="text-xs font-bold text-muted-foreground font-mono">{inv.id} &bull; {inv.status} &bull; {inv.priority} PRIORITY</div>
            <h1 className="text-xl font-bold font-mono text-primary">{inv.title}</h1>
          </div>
        </div>
        <div className="flex gap-4 items-center">
          <div className="flex bg-muted p-1 rounded font-mono text-sm">
            <button className={`px-4 py-1 rounded ${activeTab === 'WORKSPACE' ? 'bg-background shadow-sm text-primary font-bold' : 'text-muted-foreground hover:text-foreground'}`} onClick={() => setActiveTab('WORKSPACE')}>WORKSPACE</button>
            <button className={`px-4 py-1 rounded ${activeTab === 'INTELLIGENCE' ? 'bg-background shadow-sm text-primary font-bold' : 'text-muted-foreground hover:text-foreground'}`} onClick={() => setActiveTab('INTELLIGENCE')}>INTELLIGENCE</button>
          </div>
          <ReplayControls caseId={inv.id} onReplayEvent={(evt) => console.log("Replay Event:", evt)} />
          <div className="text-xs text-muted-foreground flex items-center gap-2 font-mono bg-muted px-3 py-1 rounded">
             {isConnected ? (
                 <span className="flex items-center gap-1 text-chart-2"><div className="w-2 h-2 rounded-full bg-chart-2 animate-pulse"/> LIVE</span>
             ) : (
                 <span className="flex items-center gap-1 text-destructive"><div className="w-2 h-2 rounded-full bg-destructive"/> OFFLINE</span>
             )}
          </div>
          <div className="text-xs text-muted-foreground flex items-center gap-2 font-mono bg-muted px-3 py-1 rounded">
             {isSaving ? (
                 <span className="text-primary animate-pulse">SAVING...</span>
             ) : (
                 <span className="flex items-center gap-1"><Save className="w-3 h-3"/> SYNCED</span>
             )}
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0 border-r border-border overflow-y-auto">
          {activeTab === 'WORKSPACE' ? (
            <>
              {/* Evidence Board */}
              <div className="shrink-0 border-b border-border bg-card/30 p-4">
                <h2 className="text-sm font-bold tracking-widest text-muted-foreground uppercase mb-4 flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4"/> Evidence Board
                </h2>
                
                {(!entities || Object.keys(entities as object).length === 0) ? (
                  <div className="text-center text-sm font-mono text-muted-foreground mt-4 mb-4">NO EVIDENCE ATTACHED YET</div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {Object.entries(entities as Record<string, any[]>).map(([type, entList]) => (
                      entList.map((e: any) => {
                        const entId = e.fir_id || e.citizen_id || e.vehicle_id || e.phone_id || e.criminal_id || e.id;
                        return (
                          <div key={`${type}-${entId}`} className="group bg-card border border-border p-3 rounded-lg relative hover:border-primary transition-colors cursor-pointer" onClick={() => openDrawer(entId, type as any)}>
                            <div className="text-[10px] font-bold text-muted-foreground mb-1">{type}</div>
                            <div className="font-mono text-sm font-bold truncate pr-6">{entId}</div>
                            
                            <button 
                              className="absolute top-2 right-2 p-1 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                              onClick={(evt) => {
                                evt.stopPropagation();
                                removeEntity.mutate({ invId: (inv as any).id, entityType: type, entityId: entId });
                              }}
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        );
                      })
                    ))}
                  </div>
                )}
              </div>

              {/* Notes Editor */}
              <div className="flex-1 flex flex-col p-4 bg-background min-h-[300px]">
                <h2 className="text-sm font-bold tracking-widest text-muted-foreground uppercase mb-4 flex items-center gap-2">
                  <Edit3 className="w-4 h-4"/> Investigator Notes
                </h2>
                <textarea
                  className="flex-1 w-full bg-card border border-border rounded-lg p-4 font-mono text-sm resize-none focus:outline-none focus:ring-1 focus:ring-primary"
                  placeholder="# Case Summary&#10;&#10;Start typing markdown notes here... (Auto-saves every 5s)"
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                />
              </div>
            </>
          ) : (
             <IntelligencePanel caseId={inv.id} workspace={workspaceObj} openDrawer={openDrawer} />
          )}
        </div>

        {/* Right Column: Timeline */}
        <div className="w-80 xl:w-96 bg-card flex flex-col shrink-0">
          <div className="p-4 border-b border-border">
             <h2 className="text-sm font-bold tracking-widest text-muted-foreground uppercase flex items-center gap-2">
              <Clock className="w-4 h-4"/> Unified Timeline
            </h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-xs">
            {timeline?.map((evt: any, i: number) => (
              <div key={i} className="relative pl-4 border-l border-border/50">
                <div className={`absolute -left-[5px] top-1 w-2 h-2 rounded-full ${evt.type === 'Investigation' ? 'bg-primary' : evt.type === 'FIR' ? 'bg-destructive' : evt.type === 'Intelligence' ? 'bg-chart-2' : 'bg-muted-foreground'}`} />
                <div className="text-muted-foreground mb-1 opacity-75">{new Date(evt.date).toLocaleString()}</div>
                <div className="bg-background border border-border p-2 rounded relative">
                   <div className="font-bold text-primary mb-1">[{evt.type}] {evt.event_type}</div>
                   <div>{evt.description}</div>
                   {evt.entity_id && evt.type !== 'Investigation' && (
                     <button className="text-primary hover:underline mt-2 text-[10px]" onClick={() => openDrawer(evt.entity_id, evt.type === 'FIR' ? 'FIR' : 'PERSON')}>
                       VIEW {evt.entity_id}
                     </button>
                   )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

import { useCaseRecommendations, useCaseRisk, useCaseOverlaps } from "@/hooks/useApi";
import { Zap, AlertTriangle, Link as LinkIcon, Network, MapPin } from "lucide-react";
import { ExplainabilityCard } from "@/components/investigation/ExplainabilityCard";

function IntelligencePanel({ caseId, workspace, openDrawer }: { caseId: string, workspace: any, openDrawer: any }) {
  const { data: recs, isLoading: recsLoading } = useCaseRecommendations(caseId);
  const { data: risk, isLoading: riskLoading } = useCaseRisk(caseId);
  const { data: overlaps, isLoading: overlapsLoading } = useCaseOverlaps(caseId);

  const analytical = workspace?.analytical_findings || {};
  const hasPhase7 = analytical.crime_series?.length > 0 || Object.keys(analytical.graph_metrics || {}).length > 0 || analytical.temporal_alerts?.length > 0;

  return (
    <div className="p-6 space-y-8 bg-background">
      
      {/* Risk Meter (Phase 2) */}
      <section>
        <h2 className="text-sm font-bold tracking-widest text-primary uppercase mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4"/> Case Risk Meter
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {riskLoading ? <div className="animate-pulse font-mono text-muted-foreground">CALCULATING RISK...</div> : risk && (
            <>
              <div className="bg-card border border-border p-4 rounded-lg text-center">
                <div className="text-3xl font-mono font-bold text-destructive mb-1">{risk.case_threat_score}%</div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-bold">Threat Score</div>
              </div>
              <div className="bg-card border border-border p-4 rounded-lg text-center">
                <div className="text-3xl font-mono font-bold text-chart-2 mb-1">{risk.gang_involvement}%</div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-bold">Gang Influence</div>
              </div>
              <div className="bg-card border border-border p-4 rounded-lg text-center">
                <div className="text-3xl font-mono font-bold text-primary mb-1">{risk.network_complexity}%</div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-bold">Network Complexity</div>
              </div>
              <div className="bg-card border border-border p-4 rounded-lg text-center">
                <div className="text-3xl font-mono font-bold text-muted-foreground mb-1">{risk.evidence_completeness}%</div>
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-bold">Evidence Coverage</div>
              </div>
            </>
          )}
        </div>
      </section>

      {/* Phase 7.1: Analytical Intelligence Engine (Explainable AI) */}
      {hasPhase7 && (
        <section>
          <h2 className="text-sm font-bold tracking-widest text-primary uppercase mb-4 flex items-center gap-2 border-b border-border pb-2">
            <Network className="w-4 h-4"/> Analytical Intelligence Engine
          </h2>
          <div className="space-y-4">
            
            {/* Temporal Alerts */}
            {analytical.temporal_alerts?.map((alert: any, i: number) => (
              <ExplainabilityCard key={`temp-${i}`} expl={alert.explanation} />
            ))}

            {/* Crime Series */}
            {analytical.crime_series?.map((series: any, i: number) => (
              <ExplainabilityCard key={`cs-${i}`} expl={series.explanation} />
            ))}

            {/* Graph Metrics (Extracted from dict to flat array) */}
            {Object.entries(analytical.graph_metrics || {}).map(([entityId, metrics]: [string, any]) => (
               Object.entries(metrics).map(([metricName, data]: [string, any], j) => (
                 <div key={`graph-${entityId}-${metricName}`} className="bg-card border border-border rounded-lg p-4 flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                       <div className="flex items-center gap-2">
                         <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-muted text-primary uppercase">GRAPH {metricName}</span>
                         <span className="text-sm font-bold font-mono text-foreground">{entityId}</span>
                       </div>
                       <span className="text-xs text-muted-foreground font-mono">Score: {Number(data.score).toFixed(4)}</span>
                    </div>
                    <div className="text-xs text-muted-foreground font-mono border-t border-border/50 pt-2 mt-1">
                      Algorithm: {data.algorithm}
                    </div>
                 </div>
               ))
            ))}

          </div>
        </section>
      )}

      {/* Cross-case Overlaps (Phase 2) */}
      <section>
        <h2 className="text-sm font-bold tracking-widest text-chart-2 uppercase mb-4 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4"/> Cross-Case Discoveries
        </h2>
        <div className="space-y-3">
           {overlapsLoading ? <div className="animate-pulse font-mono text-muted-foreground">SCANNING NETWORK...</div> : (overlaps as any)?.length > 0 ? (overlaps as any[]).map((o: any, i: number) => (
             <div key={i} className="bg-card border border-chart-2/30 p-4 rounded-lg flex items-center justify-between">
                <div>
                   <div className="text-chart-2 font-bold font-mono text-sm mb-1">{o.reason}</div>
                   <div className="text-xs text-muted-foreground">Investigation {o.investigation_id} shares this entity. Confidence: {o.confidence}</div>
                </div>
                <Link href={`/investigations/${o.investigation_id}`} className="px-3 py-1 bg-muted hover:bg-chart-2/20 text-xs font-mono font-bold rounded text-chart-2 transition-colors">
                  VIEW CASE
                </Link>
             </div>
           )) : (
             <div className="text-sm font-mono text-muted-foreground bg-card p-4 rounded border border-border">No cross-case overlaps detected.</div>
           )}
        </div>
      </section>

      {/* Ranked Leads (Phase 2) */}
      <section>
        <h2 className="text-sm font-bold tracking-widest text-primary uppercase mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4"/> Ranked Leads & Suggested Actions
        </h2>
        <div className="space-y-3">
           {recsLoading ? <div className="animate-pulse font-mono text-muted-foreground">GENERATING LEADS...</div> : recs?.length > 0 ? recs.map((r: any, i: number) => (
             <div key={i} className="bg-card border border-border p-4 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${r.priority === 'High' || r.priority === 'Critical' ? 'bg-destructive/20 text-destructive' : 'bg-primary/20 text-primary'}`}>{r.priority} PRIORITY</span>
                  <span className="text-xs font-mono text-muted-foreground">[{r.type}]</span>
                </div>
                <div className="font-medium text-sm mb-2">{r.suggestion}</div>
                <div className="text-xs font-mono text-muted-foreground border-t border-border/50 pt-2 flex items-center gap-2">
                  <LinkIcon className="w-3 h-3"/> Evidence: {r.evidence}
                </div>
             </div>
           )) : (
             <div className="text-sm font-mono text-muted-foreground bg-card p-4 rounded border border-border">No active intelligence leads available. Attach more evidence to generate suggestions.</div>
           )}
        </div>
      </section>

    </div>
  );
}
