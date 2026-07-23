import React, { useState } from 'react';

interface ScanStatusProps {
  onTriggerScan?: () => Promise<any>;
}

export const ScanStatus: React.FC<ScanStatusProps> = ({ onTriggerScan }) => {
  const [isScanning, setIsScanning] = useState(false);
  const [lastScanResult, setLastScanResult] = useState<any>(null);

  const handleScan = async () => {
    if (!onTriggerScan) return;
    setIsScanning(true);
    try {
      const res = await onTriggerScan();
      setLastScanResult(res);
    } catch (err) {
      console.error("Scan error", err);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg font-mono text-xs text-slate-200 flex items-center justify-between">
      <div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
          <h4 className="font-bold text-slate-100">Continuous Compliance Monitor</h4>
        </div>
        <p className="text-[11px] text-slate-400 mt-1">
          {lastScanResult
            ? `Last Incremental Scan: ${lastScanResult.result?.scanned_items || 0} items checked, ${lastScanResult.result?.new_violations || 0} new violations.`
            : 'Event-driven pub/sub listener active. Ready for incremental scans.'}
        </p>
      </div>

      <button
        onClick={handleScan}
        disabled={isScanning}
        className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-slate-950 font-bold rounded text-xs transition-colors"
      >
        {isScanning ? 'Scanning Audit Ledger...' : 'Run Incremental Scan'}
      </button>
    </div>
  );
};
