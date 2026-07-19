"use client";

import { useState, useEffect } from "react";
import { Shield } from "lucide-react";

const BOOT_SEQUENCE = [
  "Initializing GIS...",
  "Loading FIR Index...",
  "Loading Intelligence Engine...",
  "Loading Neo4j...",
  "Synchronizing Tactical Dashboard...",
  "Ready."
];

export function BootScreen({ onComplete }: { onComplete: () => void }) {
  const [lines, setLines] = useState<number>(0);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (lines < BOOT_SEQUENCE.length) {
      const timer = setTimeout(() => {
        setLines(l => l + 1);
      }, lines === BOOT_SEQUENCE.length - 1 ? 1000 : 500); // Pause longer on "Ready."
      return () => clearTimeout(timer);
    } else {
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(onComplete, 500); // Allow fade out animation
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [lines, onComplete]);

  if (!isVisible) return null;

  return (
    <div className={`fixed inset-0 z-[9999] bg-background flex flex-col items-center justify-center transition-opacity duration-500 ${lines >= BOOT_SEQUENCE.length ? 'opacity-0' : 'opacity-100'}`}>
      <div className="w-[600px] max-w-[90vw]">
        <div className="flex items-center gap-4 mb-12">
          <Shield className="w-16 h-16 text-primary animate-pulse" />
          <div>
            <h1 className="text-4xl font-bold tracking-widest text-primary">NEXUS</h1>
            <p className="text-sm font-mono tracking-widest text-muted-foreground uppercase">Strategic Crime Intelligence Hub</p>
          </div>
        </div>

        <div className="font-mono text-sm space-y-4">
          {BOOT_SEQUENCE.slice(0, lines).map((line, idx) => (
            <div key={idx} className="flex items-center justify-between text-muted-foreground animate-in slide-in-from-bottom-2 fade-in duration-300">
              <span>{line}</span>
              <span className="text-primary font-bold">✓</span>
            </div>
          ))}
          {lines < BOOT_SEQUENCE.length && (
            <div className="flex items-center gap-2 text-muted-foreground animate-pulse">
              <span className="w-2 h-4 bg-primary" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
