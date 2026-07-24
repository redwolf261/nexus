import React, { useState } from "react";

export type DecisionAction = "APPROVE" | "REJECT" | "RETURN" | "ESCALATE";

interface ApprovalDecisionDialogProps {
  approvalId: string;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (action: DecisionAction, comments: string, targetRole?: string) => Promise<void>;
  isSubmitting?: boolean;
}

export const ApprovalDecisionDialog: React.FC<ApprovalDecisionDialogProps> = ({
  approvalId,
  isOpen,
  onClose,
  onSubmit,
  isSubmitting = false,
}) => {
  const [action, setAction] = useState<DecisionAction>("APPROVE");
  const [comments, setComments] = useState("");
  const [targetRole, setTargetRole] = useState("acp");

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(action, comments, action === "ESCALATE" ? targetRole : undefined);
    setComments("");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-base font-semibold text-slate-100">
            Submit Governance Decision
          </h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 text-lg leading-none"
          >
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-2">Decision Action</label>
            <div className="grid grid-cols-2 gap-2">
              {(["APPROVE", "REJECT", "RETURN", "ESCALATE"] as DecisionAction[]).map((act) => (
                <button
                  type="button"
                  key={act}
                  onClick={() => setAction(act)}
                  className={`px-3 py-2 rounded-lg font-mono font-semibold border transition-all text-center ${
                    action === act
                      ? act === "APPROVE"
                        ? "bg-emerald-950 border-emerald-500 text-emerald-300"
                        : act === "REJECT"
                        ? "bg-rose-950 border-rose-500 text-rose-300"
                        : act === "RETURN"
                        ? "bg-orange-950 border-orange-500 text-orange-300"
                        : "bg-purple-950 border-purple-500 text-purple-300"
                      : "bg-slate-950 border-slate-800 text-slate-400 hover:bg-slate-800"
                  }`}
                >
                  {act}
                </button>
              ))}
            </div>
          </div>

          {action === "ESCALATE" && (
            <div>
              <label className="block text-slate-300 font-medium mb-1">Escalate To Role</label>
              <select
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-purple-500"
              >
                <option value="acp">ACP (Assistant Commissioner)</option>
                <option value="dcp">DCP (Deputy Commissioner)</option>
                <option value="admin">Administrator</option>
              </select>
            </div>
          )}

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Comments & Operational Rationale
            </label>
            <textarea
              required
              rows={3}
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="Enter mandatory justification or conditions for this decision..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-cyan-500 resize-none"
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
              className={`px-4 py-2 rounded-lg font-medium text-white transition-all ${
                action === "APPROVE"
                  ? "bg-emerald-600 hover:bg-emerald-500"
                  : action === "REJECT"
                  ? "bg-rose-600 hover:bg-rose-500"
                  : action === "RETURN"
                  ? "bg-orange-600 hover:bg-orange-500"
                  : "bg-purple-600 hover:bg-purple-500"
              }`}
            >
              {isSubmitting ? "Submitting..." : `Confirm ${action}`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
