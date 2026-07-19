"use client";

import { createContext, useContext, useState, ReactNode, useCallback } from "react";
import { X, Clock, Activity, FileText, Database } from "lucide-react";

type DrawerType = "FIR" | "PERSON" | "VEHICLE" | "CAMPAIGN" | "PHONE" | "MASTERMIND" | null;

interface DrawerContextType {
  activeEntity: { id: string, type: DrawerType } | null;
  openDrawer: (id: string, type: DrawerType) => void;
  closeDrawer: () => void;
}

const DrawerContext = createContext<DrawerContextType | undefined>(undefined);

export function DrawerProvider({ children }: { children: ReactNode }) {
  const [activeEntity, setActiveEntity] = useState<{ id: string, type: DrawerType } | null>(null);

  const openDrawer = useCallback((id: string, type: DrawerType) => {
    setActiveEntity({ id, type });
  }, []);

  const closeDrawer = useCallback(() => {
    setActiveEntity(null);
  }, []);

  return (
    <DrawerContext.Provider value={{ activeEntity, openDrawer, closeDrawer }}>
      {children}
      <InvestigationDrawer activeEntity={activeEntity} closeDrawer={closeDrawer} />
    </DrawerContext.Provider>
  );
}

export function useInvestigationDrawer() {
  const ctx = useContext(DrawerContext);
  if (!ctx) throw new Error("Missing DrawerProvider");
  return ctx;
}

function InvestigationDrawer({ activeEntity, closeDrawer }: { activeEntity: { id: string, type: DrawerType } | null, closeDrawer: () => void }) {
  if (!activeEntity) return null;

  return (
    <div className="fixed top-16 right-0 bottom-12 w-[450px] bg-sidebar border-l border-border z-[500] shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
      <div className="flex items-center justify-between p-4 border-b border-border bg-card">
        <div>
          <div className="text-xs font-bold tracking-widest text-primary uppercase">{activeEntity.type} INTELLIGENCE</div>
          <div className="text-lg font-mono font-bold mt-1">{activeEntity.id}</div>
        </div>
        <button onClick={closeDrawer} className="p-2 hover:bg-muted rounded-full transition-colors">
          <X className="w-5 h-5 text-muted-foreground" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
            <Activity className="w-4 h-4 text-primary" /> Risk Profile
          </div>
          <div className="flex items-center justify-between bg-card border border-border p-3 rounded-md">
            <div>
              <div className="text-xs text-muted-foreground uppercase">Threat Level</div>
              <div className="font-bold text-destructive flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-destructive animate-pulse" /> HIGH
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-muted-foreground uppercase">Confidence</div>
              <div className="font-mono text-xl">94%</div>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
            <Database className="w-4 h-4 text-primary" /> Known Aliases & Identifiers
          </div>
          <div className="bg-card border border-border rounded-md p-3 font-mono text-sm space-y-1">
            <div>&gt; PLATES: KA-01-HC-9021</div>
            <div>&gt; PHONE: +91 98765 43210</div>
            <div>&gt; GANG: SYNDICATE-001</div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
            <Clock className="w-4 h-4 text-primary" /> Incident Timeline
          </div>
          <div className="relative border-l border-border ml-2 pl-4 py-2 space-y-4 font-mono text-xs">
            <div className="relative">
              <div className="absolute -left-[21px] top-1 w-2 h-2 bg-primary rounded-full ring-4 ring-background" />
              <div className="text-muted-foreground mb-1">2021-09-12 14:30</div>
              <div className="text-foreground bg-card border border-border p-2 rounded">Incident Spotted on CCTV-Cam-412</div>
            </div>
            <div className="relative">
              <div className="absolute -left-[21px] top-1 w-2 h-2 bg-chart-2 rounded-full ring-4 ring-background" />
              <div className="text-muted-foreground mb-1">2021-09-12 15:45</div>
              <div className="text-foreground bg-card border border-border p-2 rounded">Phone ping at Tower Cell-91</div>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
            <FileText className="w-4 h-4 text-primary" /> Intelligence Story Card
          </div>
          <div className="bg-card border border-border p-4 rounded-md space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase text-primary bg-primary/10 px-2 py-1 rounded">CAMPAIGN: C-14</span>
              <span className="text-xs text-muted-foreground font-bold">Confidence: <span className="text-chart-1">96%</span></span>
            </div>
            
            <p className="text-sm leading-relaxed text-foreground font-mono border-l-2 border-primary pl-3 py-1">
              Entity matches pattern established in Campaign C-14. Probable mastermind connection via financial node tracking.
            </p>
            
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-muted/50 p-2 rounded">
                <div className="text-muted-foreground uppercase mb-1">Detected Via</div>
                <div className="font-bold">Cross-jurisdiction</div>
              </div>
              <div className="bg-muted/50 p-2 rounded">
                <div className="text-muted-foreground uppercase mb-1">Financial Loss</div>
                <div className="font-bold text-destructive">₹2.4 Crores</div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-muted-foreground uppercase">Investigation Progress</span>
                <span className="text-primary font-bold">65%</span>
              </div>
              <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
                <div className="bg-primary h-1.5 rounded-full" style={{ width: '65%' }}></div>
              </div>
            </div>
            
            <div className="pt-3 border-t border-border">
              <div className="text-xs text-muted-foreground font-bold uppercase tracking-widest mb-2 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-chart-2" /> Operational Recommendations
              </div>
              <ul className="text-xs space-y-1.5 font-mono text-foreground ml-3">
                <li>&gt; Deploy 3 targeted patrols</li>
                <li>&gt; Increase CCTV grid monitoring</li>
                <li>&gt; Notify District Command</li>
                <li>&gt; Watch vehicle <span className="text-primary">KA-01-HC-9021</span></li>
                <li>&gt; Flag phone <span className="text-primary">+91 98765 43210</span></li>
              </ul>
            </div>

            <button onClick={() => alert("Generating Case Report PDF...")} className="w-full mt-4 py-2 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 rounded font-bold uppercase tracking-widest text-xs transition-colors flex items-center justify-center gap-2">
              <FileText className="w-4 h-4" /> Generate Case Report
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
