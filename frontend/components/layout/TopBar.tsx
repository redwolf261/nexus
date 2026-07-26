"use client";

import { useLiveIncident } from "@/hooks/useLiveIncident";
import { useDemo } from "@/contexts/DemoContext";
import { useInvestigationDrawer } from "@/components/investigation/InvestigationDrawer";
import { Search, Zap, PlayCircle, Fingerprint, Car, Hash, ShieldAlert, Clock } from "lucide-react";
import { useState, useEffect } from "react";
import { useSearch } from "@/hooks/useApi";

const getIconForType = (type: string) => {
  switch (type.toUpperCase()) {
    case "FIR": return Hash;
    case "PERSON": return Fingerprint;
    case "VEHICLE": return Car;
    case "CRIMINAL": return ShieldAlert;
    default: return Search;
  }
};

export function TopBar() {
  const { triggerIncident } = useLiveIncident();
  const { startDemo } = useDemo();
  const { openDrawer } = useInvestigationDrawer();

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [showSearch, setShowSearch] = useState(false);
  const [currentTime, setCurrentTime] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Live clock
  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString("en-IN", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" })
      );
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const { data: searchData, isLoading: isSearchLoading } = useSearch(debouncedSearch);
  const searchResults = searchData?.results || [];

  const selectResult = (id: string, type: string) => {
    setSearch("");
    setShowSearch(false);
    openDrawer(id, type as any);
  };

  return (
    <header className="h-14 bg-sidebar border-b border-sidebar-border flex items-center justify-between px-5 shrink-0 relative z-[450]">
      {/* Left — status */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
          <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-mono">
            Secure Link Active
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] font-mono text-muted-foreground/70">
          <Clock className="w-3 h-3" />
          <span className="tabular-nums">{currentTime} IST</span>
        </div>
      </div>

      {/* Center — global search */}
      <div className="relative w-[440px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground/60" />
        <input
          type="text"
          placeholder="Search FIRs, persons, vehicles, criminals..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onFocus={() => setShowSearch(true)}
          onBlur={() => setTimeout(() => setShowSearch(false), 200)}
          className="w-full bg-background/60 border border-border rounded-lg py-2 pl-9 pr-4 text-xs focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary/50 transition-all font-mono placeholder-muted-foreground/40 backdrop-blur-sm"
        />

        {showSearch && search.length >= 2 && (
          <div className="absolute top-full left-0 right-0 mt-1 glass-card rounded-xl shadow-2xl overflow-hidden max-h-80 overflow-y-auto z-50">
            <div className="px-3 py-2 text-[9px] font-bold text-muted-foreground uppercase tracking-[0.2em] border-b border-border flex justify-between items-center">
              <span>Database Matches</span>
              {isSearchLoading && <span className="animate-pulse text-primary">Scanning...</span>}
            </div>

            {!isSearchLoading && searchResults.length === 0 ? (
              <div className="p-4 text-xs text-muted-foreground font-mono">No matches in operational database.</div>
            ) : (
              searchResults.map((result: any) => {
                const Icon = getIconForType(result.type);
                return (
                  <div
                    key={`${result.type}-${result.id}`}
                    onClick={() => selectResult(result.id, result.type)}
                    className="px-3 py-2.5 hover:bg-muted/40 border-b border-border/50 last:border-0 cursor-pointer flex items-center gap-3 transition-colors"
                  >
                    <div className="w-7 h-7 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <div className="text-xs font-bold font-mono text-primary">{result.id}{result.name ? ` — ${result.name}` : ""}</div>
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wide">{result.type} · {result.snippet}</div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>

      {/* Right — actions + user */}
      <div className="flex items-center gap-3">
        <button
          onClick={triggerIncident}
          className="flex items-center gap-1.5 bg-destructive/10 hover:bg-destructive/20 text-destructive border border-destructive/25 px-2.5 py-1.5 rounded-lg text-[11px] font-bold font-mono tracking-wider transition-all"
        >
          <Zap className="w-3.5 h-3.5" />
          INCIDENT
        </button>
        <button
          onClick={() => startDemo()}
          className="flex items-center gap-1.5 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/25 px-2.5 py-1.5 rounded-lg text-[11px] font-bold font-mono tracking-wider transition-all"
        >
          <PlayCircle className="w-3.5 h-3.5" />
          DEMO
        </button>

        <div className="w-px h-5 bg-border" />

        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-primary/15 border border-primary/20 flex items-center justify-center text-primary text-[10px] font-bold font-mono">
            AD
          </div>
          <div className="text-right hidden xl:block">
            <div className="text-[11px] font-medium text-foreground font-mono">admin</div>
            <div className="text-[9px] text-muted-foreground tracking-wider uppercase">Command Alpha</div>
          </div>
        </div>
      </div>
    </header>
  );
}
