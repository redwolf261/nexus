import React from "react";

export type ApprovalStatus =
  | "DRAFT"
  | "SUBMITTED"
  | "UNDER_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "RETURNED"
  | "ESCALATED"
  | "EXPIRED"
  | "CANCELLED";

interface ApprovalStatusChipProps {
  status: ApprovalStatus | string;
  size?: "sm" | "md" | "lg";
}

export const ApprovalStatusChip: React.FC<ApprovalStatusChipProps> = ({ status, size = "md" }) => {
  const st = String(status).toUpperCase();

  let colorClasses = "bg-slate-800 text-slate-300 border-slate-700";

  switch (st) {
    case "APPROVED":
      colorClasses = "bg-emerald-950/80 text-emerald-300 border-emerald-800/80";
      break;
    case "REJECTED":
      colorClasses = "bg-rose-950/80 text-rose-300 border-rose-800/80";
      break;
    case "UNDER_REVIEW":
    case "SUBMITTED":
      colorClasses = "bg-amber-950/80 text-amber-300 border-amber-800/80";
      break;
    case "RETURNED":
      colorClasses = "bg-orange-950/80 text-orange-300 border-orange-800/80";
      break;
    case "ESCALATED":
      colorClasses = "bg-purple-950/80 text-purple-300 border-purple-800/80";
      break;
    case "EXPIRED":
    case "CANCELLED":
      colorClasses = "bg-slate-900 text-slate-400 border-slate-800";
      break;
    case "DRAFT":
      colorClasses = "bg-sky-950/80 text-sky-300 border-sky-800/80";
      break;
  }

  const sizeClasses =
    size === "sm"
      ? "text-[10px] px-1.5 py-0.5"
      : size === "lg"
      ? "text-sm px-3 py-1 font-semibold"
      : "text-xs px-2 py-0.5 font-medium";

  return (
    <span className={`inline-flex items-center gap-1 rounded-md border font-mono tracking-wide ${colorClasses} ${sizeClasses}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      {st}
    </span>
  );
};
