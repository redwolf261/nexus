"use client";

import { useNotificationInbox } from "@/hooks/useApi";
import { NotificationInbox } from "@/components/notification/NotificationInbox";
import { Bell, RefreshCw } from "lucide-react";

export default function NotificationsPage() {
  const { data, isLoading, error, refetch } = useNotificationInbox();
  
  const notifications = Array.isArray(data) ? data : (data as any)?.notifications ?? [];
  const unreadCount = notifications.filter((n: any) => !n.acknowledged).length;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bell className="w-5 h-5 text-indigo-400" />
          <div>
            <h1 className="text-2xl font-bold font-mono text-slate-100">Notification Center</h1>
            <p className="text-slate-400 text-sm">
              Inbox · {unreadCount > 0 ? <span className="text-amber-400">{unreadCount} unread</span> : "All read"} · Real-time alerts
            </p>
          </div>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {isLoading && (
        <div className="flex items-center gap-3 p-8 text-slate-400 font-mono text-sm animate-pulse">
          <RefreshCw className="w-4 h-4 animate-spin" />
          Loading notifications...
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-950/30 border border-rose-800/50 rounded-lg text-rose-300 text-sm font-mono">
          ⚠ Failed to load notifications.
        </div>
      )}

      {!isLoading && (
        <NotificationInbox
          notifications={notifications}
          unreadCount={unreadCount}
          onRefresh={() => refetch()}
        />
      )}
    </div>
  );
}
