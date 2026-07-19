"use client";

import dynamic from "next/dynamic";

// Dynamically import the map component with SSR disabled
const IntelligenceMap = dynamic(
  () => import("@/components/map/IntelligenceMap"),
  { 
    ssr: false,
    loading: () => (
      <div className="w-full h-full flex flex-col items-center justify-center bg-card border border-border">
        <div className="text-primary font-mono animate-pulse mb-4">INITIALIZING GEOSPATIAL ENGINE...</div>
        <div className="w-[80%] h-[60%] rounded-md bg-muted opacity-20 animate-pulse" />
      </div>
    )
  }
);

export function MapWrapper() {
  return (
    <div className="w-full h-full absolute inset-0">
      <IntelligenceMap />
    </div>
  );
}
