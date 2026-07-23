import React from "react";
import { UnreadBadge } from "./UnreadBadge";

interface NotificationBellProps {
  unreadCount: number;
  hasCritical?: boolean;
  onClick?: () => void;
}

export const NotificationBell: React.FC<NotificationBellProps> = ({
  unreadCount,
  hasCritical = false,
  onClick,
}) => {
  return (
    <button
      onClick={onClick}
      className="relative p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-purple-600/60 text-slate-300 hover:text-white transition-all shadow-md flex items-center justify-center"
      title="Open Notification Center"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.8}
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>

      {unreadCount > 0 && (
        <span className="absolute -top-1.5 -right-1.5">
          <UnreadBadge count={unreadCount} hasCritical={hasCritical} size="sm" />
        </span>
      )}
    </button>
  );
};
