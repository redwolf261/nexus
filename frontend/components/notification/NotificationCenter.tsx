import React, { useState } from "react";
import { NotificationDTO } from "./NotificationCard";
import { NotificationList } from "./NotificationList";
import { NotificationPreferences, PreferenceDTO } from "./NotificationPreferences";

interface NotificationCenterProps {
  isOpen: boolean;
  onClose: () => void;
  notifications: NotificationDTO[];
  preferences: PreferenceDTO;
  onAcknowledge?: (id: string) => void;
  onDismiss?: (id: string) => void;
  onSavePreferences?: (updated: Partial<PreferenceDTO>) => Promise<void>;
  onRefresh?: () => void;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({
  isOpen,
  onClose,
  notifications,
  preferences,
  onAcknowledge,
  onDismiss,
  onSavePreferences,
  onRefresh,
}) => {
  const [activeTab, setActiveTab] = useState<"LIST" | "PREFERENCES">("LIST");

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex justify-end">
      <div className="bg-slate-900 border-l border-slate-800 max-w-md w-full h-full p-5 space-y-4 shadow-2xl flex flex-col font-mono text-xs">
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <span>Operational Communication Center</span>
            </h2>
            <p className="text-[10px] text-slate-400">Multi-Channel Operational Alerts & Dispatch Governance</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl leading-none">
            &times;
          </button>
        </div>

        {/* Tab Selection */}
        <div className="flex gap-2 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab("LIST")}
            className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all ${
              activeTab === "LIST"
                ? "bg-purple-950/80 border-purple-700 text-purple-200"
                : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
            }`}
          >
            Notifications ({notifications?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab("PREFERENCES")}
            className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all ${
              activeTab === "PREFERENCES"
                ? "bg-purple-950/80 border-purple-700 text-purple-200"
                : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
            }`}
          >
            Preferences
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto pr-1">
          {activeTab === "LIST" ? (
            <NotificationList
              notifications={notifications}
              onAcknowledge={onAcknowledge}
              onDismiss={onDismiss}
              onRefresh={onRefresh}
            />
          ) : (
            <NotificationPreferences
              preferences={preferences}
              onSave={onSavePreferences || (async () => {})}
            />
          )}
        </div>
      </div>
    </div>
  );
};
