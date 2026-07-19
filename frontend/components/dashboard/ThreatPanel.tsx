"use client";

import { AlertTriangle, ChevronUp, ChevronDown } from "lucide-react";

export function ThreatPanel({ level }: { level: "LOW" | "GUARDED" | "ELEVATED" | "HIGH" | "CRITICAL" }) {
  
  const levels = ["LOW", "GUARDED", "ELEVATED", "HIGH", "CRITICAL"];
  const activeIndex = levels.indexOf(level);
  
  const getLevelColor = (idx: number) => {
    if (idx === 0) return "bg-primary";
    if (idx === 1) return "bg-chart-5"; // Greenish
    if (idx === 2) return "bg-chart-2"; // Amberish
    if (idx === 3) return "bg-chart-3"; // Orange/Red
    if (idx === 4) return "bg-destructive"; // Red
    return "bg-muted";
  };

  return (
    <div className="bg-card border border-border p-6 rounded-lg flex flex-col gap-6 h-full relative overflow-hidden">
      
      {/* Background Pulse Effect for high threat */}
      {activeIndex >= 3 && (
        <div className="absolute inset-0 bg-destructive/5 animate-pulse pointer-events-none" />
      )}

      <div>
        <h2 className="text-xl font-bold tracking-tight flex items-center gap-2">
          <AlertTriangle className={activeIndex >= 3 ? "text-destructive" : "text-primary"} />
          THREAT SCORE
        </h2>
        <p className="text-xs font-mono uppercase text-muted-foreground mt-1">Statewide Intelligence Feed</p>
      </div>

      <div className="flex-1 flex flex-col justify-center gap-4">
        {levels.map((l, idx) => {
          const isActive = idx === activeIndex;
          const isPassed = idx < activeIndex;
          
          return (
            <div key={l} className="flex items-center gap-4 group">
              <div className="w-12 text-right font-mono text-xs font-bold text-muted-foreground group-hover:text-foreground transition-colors">
                L-{idx + 1}
              </div>
              <div className="flex-1 h-3 bg-muted rounded-full overflow-hidden relative">
                <div 
                  className={`absolute top-0 bottom-0 left-0 transition-all duration-1000 ${getLevelColor(idx)} ${isActive ? 'animate-pulse w-full' : isPassed ? 'w-full opacity-50' : 'w-0'}`} 
                />
              </div>
              <div className={`w-24 font-bold text-xs tracking-widest ${isActive ? 'text-foreground' : 'text-muted-foreground'}`}>
                {l}
              </div>
            </div>
          );
        })}
      </div>

      <div className="pt-4 border-t border-border flex items-center justify-between">
        <div>
          <div className="text-xs uppercase text-muted-foreground font-bold">7-Day Trend</div>
          <div className="flex items-center gap-1 text-destructive font-mono text-sm mt-1">
            <ChevronUp className="w-4 h-4" />
            ELEVATING
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs uppercase text-muted-foreground font-bold">System Status</div>
          <div className="text-primary font-mono text-sm mt-1 flex items-center justify-end gap-2">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            NOMINAL
          </div>
        </div>
      </div>
    </div>
  );
}
