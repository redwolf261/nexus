"use client";

import { AlertTriangle, Info, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { useLiveIncident } from "@/hooks/useLiveIncident";
import { useExecutiveDashboard, useFIRs } from "@/hooks/useApi";

type AlertType = { id: string | number; type: "critical" | "warning" | "info"; msg: string; time: string };

export function AlertFeed() {
  const { activeIncident } = useLiveIncident();
  const { data: dashData } = useExecutiveDashboard();
  const { data: gangFirs } = useFIRs({ is_gang_crime: true, limit: 1 });
  
  const [alerts, setAlerts] = useState<AlertType[]>([]);

  useEffect(() => {
    let initialAlerts: AlertType[] = [];
    
    if (dashData?.new_intelligence_alerts) {
      initialAlerts.push({
        id: "intel",
        type: "info",
        msg: `${dashData.new_intelligence_alerts} new intelligence alerts pending review`,
        time: "Just now"
      });
    }
    if (dashData?.predicted_hotspots) {
      initialAlerts.push({
        id: "hotspots",
        type: "warning",
        msg: `${dashData.predicted_hotspots} new hotspots predicted statewide`,
        time: "2m ago"
      });
    }
    if (gangFirs && gangFirs.length > 0) {
      initialAlerts.push({
        id: "gang",
        type: "critical",
        msg: `Recent gang activity: ${gangFirs[0].crime_type} in ${gangFirs[0].district_name || gangFirs[0].district_id}`,
        time: "15m ago"
      });
    }

    if (initialAlerts.length === 0) {
       initialAlerts = [
         { id: "fallback", type: "info", msg: "System nominal. All patrols operating normally.", time: "System" }
       ];
    }
    
    if (activeIncident) {
      initialAlerts = [
        { 
          id: Date.now(), 
          type: "critical", 
          msg: `LIVE INCIDENT: ${activeIncident.type} reported in ${activeIncident.district} (${activeIncident.id})`, 
          time: "LIVE" 
        },
        ...initialAlerts
      ].slice(0, 5);
    }
    
    setAlerts(initialAlerts);
  }, [activeIncident, dashData, gangFirs]);

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
