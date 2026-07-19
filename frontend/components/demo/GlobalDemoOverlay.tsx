"use client";

import { useDemo } from "@/contexts/DemoContext";
import { BootScreen } from "./BootScreen";

export function GlobalDemoOverlay() {
  const { stage, isDemoActive, stopDemo } = useDemo();

  return (
    <>
      {stage === "BOOT" && <BootScreen onComplete={() => {}} />}
      
      {isDemoActive && stage !== "BOOT" && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[9999] pointer-events-auto">
          <div className="bg-primary/20 backdrop-blur border border-primary text-primary px-4 py-2 rounded-full flex items-center gap-4 shadow-[0_0_15px_rgba(0,229,255,0.3)]">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
            </span>
            <span className="text-xs font-bold uppercase tracking-widest font-mono">Autopilot Demo Active: {stage}</span>
            <button 
              onClick={stopDemo}
              className="text-xs font-bold text-foreground bg-primary/20 hover:bg-primary/40 px-2 py-1 rounded ml-2 transition-colors"
            >
              STOP
            </button>
          </div>
        </div>
      )}
    </>
  );
}
