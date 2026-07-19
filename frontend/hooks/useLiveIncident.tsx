"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface LiveIncident {
  id: string;
  type: string;
  district: string;
  latitude: number;
  longitude: number;
  timestamp: string;
}

interface IncidentContextType {
  activeIncident: LiveIncident | null;
  triggerIncident: () => void;
  clearIncident: () => void;
}

const IncidentContext = createContext<IncidentContextType | undefined>(undefined);

export function IncidentProvider({ children }: { children: ReactNode }) {
  const [activeIncident, setActiveIncident] = useState<LiveIncident | null>(null);

  const triggerIncident = () => {
    setActiveIncident({
      id: `FIR-LIVE-${Math.floor(Math.random() * 10000)}`,
      type: "ARMED ROBBERY",
      district: "Bangalore",
      latitude: 12.9716 + (Math.random() - 0.5) * 0.1,
      longitude: 77.5946 + (Math.random() - 0.5) * 0.1,
      timestamp: new Date().toISOString()
    });
  };

  const clearIncident = () => {
    setActiveIncident(null);
  };

  return (
    <IncidentContext.Provider value={{ activeIncident, triggerIncident, clearIncident }}>
      {children}
    </IncidentContext.Provider>
  );
}

export function useLiveIncident() {
  const context = useContext(IncidentContext);
  if (context === undefined) {
    throw new Error("useLiveIncident must be used within an IncidentProvider");
  }
  return context;
}
