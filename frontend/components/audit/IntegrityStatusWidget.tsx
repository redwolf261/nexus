import React, { useState, useEffect } from 'react';

export interface IntegrityReport {
  is_valid: boolean;
  total_records_scanned: number;
  verified_sequences: number;
  corrupted_sequence?: number | null;
  error_message?: string | null;
  verified_at: string;
  genesis_hash: string;
  latest_hash: string;
}

interface IntegrityStatusWidgetProps {
  onVerifyRequest?: () => Promise<IntegrityReport>;
}

export const IntegrityStatusWidget: React.FC<IntegrityStatusWidgetProps> = ({ onVerifyRequest }) => {
  const [report, setReport] = useState<IntegrityReport | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);

  const runVerification = async () => {
    if (!onVerifyRequest) return;
    setIsVerifying(true);
    try {
      const res = await onVerifyRequest();
      setReport(res);
    } catch (err) {
      console.error("Integrity check failed", err);
    } finally {
      setIsVerifying(false);
    }
  };

  useEffect(() => {
    runVerification();
  }, []);

  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg font-mono text-xs text-slate-200">
      <div className="flex justify-between items-center pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <h3 className="text-sm font-bold text-slate-100">Cryptographic Ledger Health</h3>
        </div>
        <button
          onClick={runVerification}
          disabled={isVerifying}
          className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-slate-950 font-bold rounded text-xs transition-colors"
        >
          {isVerifying ? 'Verifying SHA-256 Chain...' : 'Verify Cryptographic Chain'}
        </button>
      </div>

      {report ? (
        <div className="mt-3 space-y-2">
          <div className="flex justify-between items-center p-2 rounded bg-slate-950 border border-slate-800">
            <span className="text-slate-400">Ledger Verification Status:</span>
            <span
              className={`font-bold px-2 py-0.5 rounded text-xs ${
                report.is_valid
                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                  : 'bg-rose-950 text-rose-400 border border-rose-800'
              }`}
            >
              {report.is_valid ? '✅ VALID (TAMPER-FREE)' : '❌ CORRUPTED / TAMPERED'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400">
            <div>Total Scanned Records: <strong className="text-slate-200">{report.total_records_scanned}</strong></div>
            <div>Verified Sequences: <strong className="text-slate-200">{report.verified_sequences}</strong></div>
          </div>

          {report.error_message && (
            <div className="p-2 bg-rose-950/60 border border-rose-800 rounded text-rose-300 text-xs">
              ⚠️ {report.error_message}
            </div>
          )}

          <div className="text-[10px] text-slate-500 truncate pt-1">
            Latest Hash: <span className="text-slate-400">{report.latest_hash}</span>
          </div>
        </div>
      ) : (
        <div className="mt-3 text-slate-400 text-center py-2">
          Click button to execute $O(N)$ cryptographic verification sweep.
        </div>
      )}
    </div>
  );
};
