"use client";

import { useLiveIncident } from "@/hooks/useLiveIncident";
import { useDemo } from "@/contexts/DemoContext";
import { useInvestigationDrawer } from "@/components/investigation/InvestigationDrawer";
import { Search, Zap, PlayCircle, Fingerprint, Car, Hash, ShieldAlert } from "lucide-react";
import { useRouter } from "next/navigation";
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
  const router = useRouter();

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [showSearch, setShowSearch] = useState(false);

  // Debounce the input before calling the hook
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const { data: searchData, isLoading: isSearchLoading } = useSearch(debouncedSearch);
  const searchResults = searchData?.results || [];

  const handleDemoMode = () => {
    startDemo();
  };

  const selectResult = (id: string, type: string) => {
    setSearch("");
    setShowSearch(false);
    openDrawer(id, type as any);
  };

  return (
    <header className="h-16 bg-background border-b border-border flex items-center justify-between px-6 shrink-0 relative z-[450]">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-chart-1 animate-pulse" />
          <span className="text-xs uppercase tracking-wider text-muted-foreground font-mono">System Online</span>
        </div>
      </div>
      
      <div className="relative w-[500px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input 
          type="text" 
          placeholder="Global Search (FIR, Person, Vehicle, Criminal...)" 
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onFocus={() => setShowSearch(true)}
          onBlur={() => setTimeout(() => setShowSearch(false), 200)}
          className="w-full bg-input border border-border rounded-md py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-primary transition-all font-mono shadow-inner"
        />
        
        {showSearch && search.length >= 2 && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-card border border-border rounded-md shadow-2xl overflow-hidden max-h-96 overflow-y-auto">
            <div className="p-2 text-xs font-bold text-muted-foreground uppercase tracking-widest bg-muted/50 border-b border-border flex justify-between">
              <span>Database Matches</span>
              {isSearchLoading && <span className="animate-pulse">Searching...</span>}
            </div>
            
            {!isSearchLoading && searchResults.length === 0 ? (
              <div className="p-4 text-sm text-muted-foreground font-mono">No matches found in operational database.</div>
            ) : (
              searchResults.map(result => {
                const Icon = getIconForType(result.type);
                return (
                  <div 
                    key={`${result.type}-${result.id}`}
                    onClick={() => selectResult(result.id, result.type)}
                    className="p-3 hover:bg-muted border-b border-border last:border-0 cursor-pointer flex items-center gap-3 transition-colors"
                  >
                    <div className="w-8 h-8 rounded bg-primary/10 text-primary flex items-center justify-center shrink-0">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold font-mono text-primary">{result.id} {result.name ? `- ${result.name}` : ''}</div>
                      <div className="text-xs text-muted-foreground uppercase">{result.type} • {result.snippet}</div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <button 
            onClick={triggerIncident}
            className="flex items-center gap-2 bg-destructive/10 hover:bg-destructive/20 text-destructive border border-destructive/30 px-3 py-1.5 rounded text-sm font-bold transition-colors"
          >
            <Zap className="w-4 h-4" />
            SIMULATE INCIDENT
          </button>
          <button 
            onClick={handleDemoMode}
            className="flex items-center gap-2 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30 px-3 py-1.5 rounded text-sm font-bold transition-colors"
          >
            <PlayCircle className="w-4 h-4" />
            START DEMO
          </button>
        </div>
        <div className="text-right">
          <div className="text-sm font-medium">Cmdr. Sarah Jenkins</div>
          <div className="text-xs text-muted-foreground">Command Center Alpha</div>
        </div>
        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
          SJ
        </div>
      </div>
    </header>
  );
}
