"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useLiveIncident } from "@/hooks/useLiveIncident";

type DemoStage = 
  | "IDLE" 
  | "BOOT" 
  | "DASHBOARD" 
  | "MAP_ZOOM" 
  | "REPLAY" 
  | "STORY_CARD" 
  | "GRAPH" 
  | "EXPLAIN" 
  | "LIVE_INCIDENT" 
  | "THREAT_UPDATE" 
  | "END";

interface DemoContextType {
  stage: DemoStage;
  startDemo: () => void;
  stopDemo: () => void;
  isDemoActive: boolean;
}

const DemoContext = createContext<DemoContextType | undefined>(undefined);

export function DemoProvider({ children }: { children: ReactNode }) {
  const [stage, setStage] = useState<DemoStage>("IDLE");
  const router = useRouter();
  const pathname = usePathname();
  const { triggerIncident, clearIncident } = useLiveIncident();

  const isDemoActive = stage !== "IDLE" && stage !== "END";

  useEffect(() => {
    if (!isDemoActive) return;

    let timeout: NodeJS.Timeout;

    const advance = (nextStage: DemoStage, delayMs: number) => {
      timeout = setTimeout(() => setStage(nextStage), delayMs);
    };

    switch (stage) {
      case "BOOT":
        // BootScreen handles its own timing, but we'll forcefully advance after 6s max
        advance("DASHBOARD", 6000);
        break;
      
      case "DASHBOARD":
        if (pathname !== "/") router.push("/");
        advance("MAP_ZOOM", 5000); // 5s on dashboard
        break;

      case "MAP_ZOOM":
        if (pathname !== "/map") router.push("/map");
        advance("REPLAY", 4000);
        break;

      case "REPLAY":
        // Wait for replay to finish a few frames
        advance("STORY_CARD", 8000); 
        break;

      case "STORY_CARD":
        advance("GRAPH", 5000);
        break;

      case "GRAPH":
        if (pathname !== "/silo-buster") router.push("/silo-buster");
        advance("EXPLAIN", 4000);
        break;

      case "EXPLAIN":
        advance("LIVE_INCIDENT", 6000);
        break;

      case "LIVE_INCIDENT":
        if (pathname !== "/map") router.push("/map");
        triggerIncident();
        advance("THREAT_UPDATE", 6000);
        break;

      case "THREAT_UPDATE":
        if (pathname !== "/") router.push("/");
        advance("END", 5000);
        break;

      case "END":
        setStage("IDLE");
        clearIncident();
        break;
    }

    return () => clearTimeout(timeout);
  }, [stage, pathname, router, triggerIncident, clearIncident, isDemoActive]);

  const startDemo = () => {
    clearIncident();
    if (pathname !== "/") router.push("/");
    setStage("BOOT");
  };

  const stopDemo = () => {
    setStage("IDLE");
    clearIncident();
  };

  return (
    <DemoContext.Provider value={{ stage, startDemo, stopDemo, isDemoActive }}>
      {children}
    </DemoContext.Provider>
  );
}

export function useDemo() {
  const context = useContext(DemoContext);
  if (context === undefined) {
    throw new Error("useDemo must be used within a DemoProvider");
  }
  return context;
}
