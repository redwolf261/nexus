"use client";

import { SupervisorDashboard } from "@/components/command/SupervisorDashboard";
import { Terminal } from "lucide-react";

export default function CommandCenterPage() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <Terminal className="w-5 h-5 text-emerald-400" />
        <div>
          <h1 className="text-2xl font-bold font-mono text-slate-100">Supervisor Command Center</h1>
          <p className="text-slate-400 text-sm">Active cases · Analyst workloads · SLA health · Intelligence feed</p>
        </div>
      </div>

      <SupervisorDashboard />
    </div>
  );
}
