"use client";

import { AlertTriangle, Info, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { useLiveIncident } from "@/hooks/useLiveIncident";

export function AlertFeed() {
  const { activeIncident } = useLiveIncident();
  
  const [alerts, setAlerts] = useState([
    { id: 1, type: "critical", msg: "New hotspot predicted in Central District", time: "Just now" },
    { id: 2, type: "warning", msg: "Officer overload detected in Zone 4", time: "2m ago" },
    { id: 3, type: "info", msg: "Campaign C-14 mastermind identified", time: "15m ago" },
  ]);

  useEffect(() => {
    if (activeIncident) {
      setAlerts(prev => [
        { 
          id: Date.now(), 
          type: "critical", 
          msg: `LIVE INCIDENT: ${activeIncident.type} reported in ${activeIncident.district} (${activeIncident.id})`, 
          time: "LIVE" 
        },
        ...prev
      ].slice(0, 5));
    }
  }, [activeIncident]);

  return (
    <div className="h-12 bg-sidebar border-t border-border flex items-center px-4 overflow-hidden shrink-0">
      <div className="flex items-center gap-2 mr-6 text-destructive shrink-0">
        <ShieldAlert className="w-4 h-4" />
        <span className="text-xs font-bold uppercase tracking-widest">Live Alerts</span>
      </div>
      
      <div className="flex items-center gap-6 animate-pulse">
        {alerts.map((alert, i) => (
          <div key={alert.id} className="flex items-center gap-2 text-sm whitespace-nowrap animate-in fade-in slide-in-from-left duration-500 fill-mode-both" style={{ animationDelay: `${i * 100}ms` }}>
            {alert.type === "critical" && <AlertTriangle className="w-4 h-4 text-destructive animate-pulse" />}
            {alert.type === "warning" && <AlertTriangle className="w-4 h-4 text-chart-2" />}
            {alert.type === "info" && <Info className="w-4 h-4 text-primary" />}
            <span className="text-muted-foreground">[{alert.time}]</span>
            <span className={alert.type === "critical" ? "text-destructive font-medium uppercase" : "text-muted-foreground"}>
              {alert.msg}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
