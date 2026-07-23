import React, { useState } from "react";

export type DelegationType = "TEMPORARY_ACTING" | "LEAVE_DELEGATION" | "EMERGENCY_DELEGATION" | "VACATION_DELEGATION";

interface DelegationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (
    delegateeId: string,
    delegateeRole: string,
    delegationType: DelegationType,
    durationHours: number,
    reason: string
  ) => Promise<void>;
  isSubmitting?: boolean;
}

export const DelegationDialog: React.FC<DelegationDialogProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting = false,
}) => {
  const [delegateeId, setDelegateeId] = useState("");
  const [delegateeRole, setDelegateeRole] = useState("supervisor");
  const [delegationType, setDelegationType] = useState<DelegationType>("TEMPORARY_ACTING");
  const [durationHours, setDurationHours] = useState<number>(24);
  const [reason, setReason] = useState("");

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(delegateeId, delegateeRole, delegationType, durationHours, reason);
    setDelegateeId("");
    setReason("");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <span>Delegate Command Authority</span>
            <span className="text-xs px-2 py-0.5 bg-purple-950 text-purple-300 border border-purple-800 rounded font-mono">
              Temporary
            </span>
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200 text-lg leading-none">
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Delegatee Username / ID</label>
            <input
              type="text"
              required
              placeholder="e.g. supervisor_officer2"
              value={delegateeId}
              onChange={(e) => setDelegateeId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Target Role</label>
              <select
                value={delegateeRole}
                onChange={(e) => setDelegateeRole(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-purple-500"
              >
                <option value="supervisor">Supervisor</option>
                <option value="acp">ACP</option>
                <option value="dcp">DCP</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">Duration (Hours)</label>
              <input
                type="number"
                min={1}
                max={720}
                value={durationHours}
                onChange={(e) => setDurationHours(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Delegation Context</label>
            <select
              value={delegationType}
              onChange={(e) => setDelegationType(e.target.value as DelegationType)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
            >
              <option value="TEMPORARY_ACTING">Temporary Acting Supervisor</option>
              <option value="LEAVE_DELEGATION">Leave Delegation</option>
              <option value="EMERGENCY_DELEGATION">Emergency Delegation</option>
              <option value="VACATION_DELEGATION">Vacation Delegation</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Operational Justification</label>
            <textarea
              required
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Enter mandatory justification for delegating command authority..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-purple-500 resize-none"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-lg font-medium shadow-lg"
            >
              {isSubmitting ? "Delegating..." : "Confirm Delegation"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
