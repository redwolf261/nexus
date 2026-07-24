import React from "react";

export type EscalationStatus = "PENDING" | "ACKNOWLEDGED" | "RESOLVED" | "EXPIRED" | "CANCELLED";

interface EscalationBadgeProps {
  status: EscalationStatus | string;
  size?: "sm" | "md" | "lg";
}

export const EscalationBadge: React.FC<EscalationBadgeProps> = ({ status, size = "md" }) => {
  const st = String(status).toUpperCase();

  let colorClasses = "bg-slate-800 text-slate-300 border-slate-700";

  switch (st) {
    case "PENDING":
      colorClasses = "bg-rose-950/90 text-rose-300 border-rose-800 animate-pulse";
      break;
    case "ACKNOWLEDGED":
      colorClasses = "bg-amber-950/80 text-amber-300 border-amber-800";
      break;
    case "RESOLVED":
      colorClasses = "bg-emerald-950/80 text-emerald-300 border-emerald-800";
      break;
    case "EXPIRED":
    case "CANCELLED":
      colorClasses = "bg-slate-900 text-slate-400 border-slate-800";
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
