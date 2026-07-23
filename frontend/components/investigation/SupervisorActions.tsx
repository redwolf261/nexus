import React, { useState } from "react";

interface SupervisorActionsProps {
  investigationId: string;
  onActionExecute: (actionType: string, payload: any) => Promise<void>;
}

export const SupervisorActions: React.FC<SupervisorActionsProps> = ({ investigationId, onActionExecute }) => {
  const [selectedAction, setSelectedAction] = useState<string>("");
  const [reason, setReason] = useState<string>("");
  const [targetOfficer, setTargetOfficer] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const actions = [
    { type: "ASSIGN", label: "Assign Analyst" },
    { type: "REASSIGN", label: "Reassign Analyst" },
    { type: "APPROVE", label: "Approve Workflow" },
    { type: "REJECT", label: "Reject Request" },
    { type: "ESCALATE", label: "Escalate to ACP" },
    { type: "PAUSE", label: "Pause Investigation" },
    { type: "RESUME", label: "Resume Investigation" },
    { type: "CREATE_NOTE", label: "Add Operational Note" },
    { type: "CLOSE", label: "Close Case" },
    { type: "REOPEN", label: "Reopen Case" },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAction) return;
    setIsSubmitting(true);
    try {
      await onActionExecute(selectedAction, {
        action_type: selectedAction,
        reason,
        target_officer_id: targetOfficer || undefined,
      });
      setSelectedAction("");
      setReason("");
      setTargetOfficer("");
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3 text-xs">
      <div className="border-b border-slate-800 pb-2">
        <h3 className="font-semibold text-slate-200">Supervisor Operational Action Center</h3>
        <p className="text-[11px] text-slate-400">Direct operational interventions with state governance checks.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-slate-300 font-medium mb-1">Select Action:</label>
          <select
            value={selectedAction}
            onChange={(e) => setSelectedAction(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 text-xs"
          >
            <option value="">-- Choose Action --</option>
            {actions.map((a) => (
              <option key={a.type} value={a.type}>
                {a.label} ({a.type})
              </option>
            ))}
          </select>
        </div>

        {["ASSIGN", "REASSIGN"].includes(selectedAction) && (
          <div>
            <label className="block text-slate-300 font-medium mb-1">Target Investigator ID:</label>
            <input
              type="text"
              value={targetOfficer}
              onChange={(e) => setTargetOfficer(e.target.value)}
              placeholder="e.g. OFF-102"
              className="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 text-xs font-mono"
            />
          </div>
        )}

        {selectedAction && (
          <div>
            <label className="block text-slate-300 font-medium mb-1">Audit Rationale / Notes:</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Enter operational rationale for audit logging..."
              rows={2}
              className="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 text-xs"
            />
          </div>
        )}

        {selectedAction && (
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-medium text-xs transition-colors disabled:opacity-50"
          >
            {isSubmitting ? "Executing..." : `Confirm Action (${selectedAction})`}
          </button>
        )}
      </form>
    </div>
  );
};

export default SupervisorActions;
