import React from "react";

interface UnreadBadgeProps {
  count: number;
  hasCritical?: boolean;
  size?: "sm" | "md" | "lg";
}

export const UnreadBadge: React.FC<UnreadBadgeProps> = ({
  count,
  hasCritical = false,
  size = "md",
}) => {
  if (count <= 0) return null;

  const displayCount = count > 99 ? "99+" : String(count);

  let sizeClasses = "px-1.5 py-0.5 text-[10px]";
  if (size === "sm") sizeClasses = "px-1 py-0.2 text-[9px]";
  if (size === "lg") sizeClasses = "px-2 py-1 text-xs font-bold";

  let colorClasses = "bg-purple-600 text-white border-purple-400";
  if (hasCritical) {
    colorClasses = "bg-rose-600 text-white border-rose-400 animate-pulse shadow-lg shadow-rose-950/50";
  }

  return (
    <span
      className={`inline-flex items-center justify-center rounded-full border font-mono font-bold leading-none ${sizeClasses} ${colorClasses}`}
    >
      {displayCount}
    </span>
  );
};
