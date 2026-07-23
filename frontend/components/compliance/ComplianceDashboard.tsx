import React, { useState } from 'react';
import { RiskGauge } from './RiskGauge';
import { ViolationsTable, ComplianceViolation } from './ViolationsTable';
import { RuleViewer, ComplianceRule } from './RuleViewer';
import { RemediationPanel } from './RemediationPanel';
import { ComplianceTimeline } from './ComplianceTimeline';
import { ScanStatus } from './ScanStatus';
import { ComplianceFilters } from './ComplianceFilters';

interface ComplianceDashboardProps {
  dashboardData: any;
  rules: ComplianceRule[];
  onTriggerScan?: () => Promise<any>;
  onExport?: (format: 'json' | 'csv' | 'ndjson') => void;
  onResolveViolation?: (id: string) => void;
}

export const ComplianceDashboard: React.FC<ComplianceDashboardProps> = ({
  dashboardData,
  rules,
  onTriggerScan,
  onExport,
  onResolveViolation,
}) => {
  const [selectedViolation, setSelectedViolation] = useState<ComplianceViolation | null>(null);

  const risk = dashboardData?.risk_summary || { overall_score: 0, risk_band: 'LOW' };
  const violations = dashboardData?.active_violations || [];

  return (
    <div className="p-6 bg-slate-950 min-h-screen text-slate-100 font-mono space-y-6">
      <div className="flex justify-between items-center pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-cyan-400">
            NEXUS Operational Compliance & Risk Monitoring Dashboard
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Continuous Policy Evaluation • Audit Ledger Provenance • Deterministic Risk Assessment
          </p>
        </div>
        <div className="text-right text-xs text-slate-400">
          <div>Compliance Rating: <span className="font-bold text-emerald-400">{(dashboardData?.compliance_score || 100).toFixed(1)}%</span></div>
          <div>Active Violations: <span className="font-bold text-rose-400">{dashboardData?.outstanding_remediation_count || 0}</span></div>
        </div>
      </div>

      <ScanStatus onTriggerScan={onTriggerScan} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <RiskGauge
          score={risk.overall_score || 0}
          riskBand={risk.risk_band || 'LOW'}
          complianceScore={dashboardData?.compliance_score}
        />

        <div className="lg:col-span-2 p-4 bg-slate-900 border border-slate-800 rounded-lg space-y-3 text-xs">
          <h3 className="text-xs font-bold text-slate-400 uppercase">Subsystem Risk Breakdown</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {Object.entries(risk.subsystem_breakdown || {}).map(([sub, sc]: [string, any]) => (
              <div key={sub} className="p-2.5 bg-slate-950 border border-slate-800 rounded text-center">
                <div className="text-[10px] text-slate-500">{sub}</div>
                <div className={`text-sm font-extrabold mt-1 ${sc > 50 ? 'text-rose-400' : sc > 25 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {sc.toFixed(0)} pts
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <ComplianceFilters onSearch={() => {}} onExport={onExport} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-sm font-bold text-cyan-400">Active Unresolved Policy Violations</h3>
          <ViolationsTable
            violations={violations}
            onSelectViolation={(v) => setSelectedViolation(v)}
          />
        </div>

        <div>
          <RemediationPanel
            violation={selectedViolation}
            onResolve={onResolveViolation}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RuleViewer rules={rules} />
        <ComplianceTimeline
          trend7d={dashboardData?.trend_7d || []}
          trend30d={dashboardData?.trend_30d || []}
        />
      </div>
    </div>
  );
};
