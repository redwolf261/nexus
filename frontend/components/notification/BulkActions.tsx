import React from "react";

interface BulkActionsProps {
  isOpen: boolean;
  onClose: () => void;
  selectedCount: number;
  onBulkAcknowledge: () => Promise<void>;
  onBulkDismiss: () => Promise<void>;
  onBulkArchive: () => Promise<void>;
  isProcessing?: boolean;
}

export const BulkActions: React.FC<BulkActionsProps> = ({
  isOpen,
  onClose,
  selectedCount,
  onBulkAcknowledge,
  onBulkDismiss,
  onBulkArchive,
  isProcessing = false,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-sm w-full p-5 space-y-4 shadow-2xl font-mono text-xs">
        <div className="flex justify-between items-center border-b border-slate-800 pb-2">
          <h3 className="font-bold text-slate-100 flex items-center gap-2">
            <span>Bulk Operations</span>
            <span className="px-2 py-0.5 bg-purple-950 text-purple-300 border border-purple-800 rounded text-[10px]">
              {selectedCount} Selected
            </span>
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-lg">
            &times;
          </button>
        </div>

        <p className="text-slate-400 text-[11px]">
          Select operational bulk action for {selectedCount} items.
        </p>

        <div className="space-y-2">
          <button
            disabled={isProcessing}
            onClick={async () => {
              await onBulkAcknowledge();
              onClose();
            }}
            className="w-full p-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-semibold text-left flex justify-between items-center"
          >
            <span>Bulk Acknowledge</span>
            <span className="text-[10px] opacity-80">&check; Ack</span>
          </button>

          <button
            disabled={isProcessing}
            onClick={async () => {
              await onBulkDismiss();
              onClose();
            }}
            className="w-full p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg font-semibold text-left flex justify-between items-center"
          >
            <span>Bulk Dismiss</span>
            <span className="text-[10px] text-slate-400">Dismiss</span>
          </button>

          <button
            disabled={isProcessing}
            onClick={async () => {
              await onBulkArchive();
              onClose();
            }}
            className="w-full p-2.5 bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-300 rounded-lg font-semibold text-left flex justify-between items-center"
          >
            <span>Bulk Archive</span>
            <span className="text-[10px] text-slate-400">Archive</span>
          </button>
        </div>
      </div>
    </div>
  );
};
