import React, { useState } from "react";

export interface PreferenceDTO {
  user_id: string;
  enabled_channels: string[];
  quiet_hours_enabled: boolean;
  quiet_hours_start: string;
  quiet_hours_end: string;
  digest_mode: string;
  min_priority: string;
}

interface NotificationPreferencesProps {
  preferences: PreferenceDTO;
  onSave: (updated: Partial<PreferenceDTO>) => Promise<void>;
  isSaving?: boolean;
}

export const NotificationPreferences: React.FC<NotificationPreferencesProps> = ({
  preferences,
  onSave,
  isSaving = false,
}) => {
  const [enabledChannels, setEnabledChannels] = useState<string[]>(preferences.enabled_channels || ["IN_APP", "WEBSOCKET"]);
  const [quietHoursEnabled, setQuietHoursEnabled] = useState<boolean>(preferences.quiet_hours_enabled);
  const [quietHoursStart, setQuietHoursStart] = useState<string>(preferences.quiet_hours_start || "22:00");
  const [quietHoursEnd, setQuietHoursEnd] = useState<string>(preferences.quiet_hours_end || "06:00");
  const [digestMode, setDigestMode] = useState<string>(preferences.digest_mode || "IMMEDIATE");
  const [minPriority, setMinPriority] = useState<string>(preferences.min_priority || "LOW");

  const toggleChannel = (ch: string) => {
    if (enabledChannels.includes(ch)) {
      setEnabledChannels(enabledChannels.filter((c) => c !== ch));
    } else {
      setEnabledChannels([...enabledChannels, ch]);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave({
      enabled_channels: enabledChannels,
      quiet_hours_enabled: quietHoursEnabled,
      quiet_hours_start: quietHoursStart,
      quiet_hours_end: quietHoursEnd,
      digest_mode: digestMode,
      min_priority: minPriority,
    });
  };

  return (
    <form onSubmit={handleSave} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 text-xs font-mono">
      <div className="border-b border-slate-800 pb-3">
        <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
          <span>Notification Channel & Routing Preferences</span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
            User Customization
          </span>
        </h3>
        <p className="text-[11px] text-slate-400 mt-1">
          Configure quiet hours, digest modes, and channel subscriptions. Emergency CRITICAL alerts bypass quiet hours.
        </p>
      </div>

      {/* Channel selection */}
      <div className="space-y-2">
        <label className="block text-slate-300 font-semibold">Enabled Delivery Channels</label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {["IN_APP", "WEBSOCKET", "EMAIL", "SMS", "PUSH"].map((ch) => {
            const isSelected = enabledChannels.includes(ch);
            return (
              <button
                type="button"
                key={ch}
                onClick={() => toggleChannel(ch)}
                className={`p-2.5 rounded-lg border text-left flex items-center justify-between transition-all ${
                  isSelected
                    ? "bg-purple-950/60 border-purple-700 text-purple-200"
                    : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <span>{ch}</span>
                <span className={`w-2 h-2 rounded-full ${isSelected ? "bg-purple-400" : "bg-slate-700"}`} />
              </button>
            );
          })}
        </div>
      </div>

      {/* Quiet Hours */}
      <div className="space-y-3 pt-2 border-t border-slate-800">
        <div className="flex items-center justify-between">
          <div>
            <label className="font-semibold text-slate-200">Quiet Hours Filter</label>
            <p className="text-[10px] text-slate-500">Restricts non-critical notifications during off-duty hours.</p>
          </div>
          <input
            type="checkbox"
            checked={quietHoursEnabled}
            onChange={(e) => setQuietHoursEnabled(e.target.checked)}
            className="w-4 h-4 rounded bg-slate-950 border-slate-800 text-purple-600 focus:ring-0"
          />
        </div>

        {quietHoursEnabled && (
          <div className="grid grid-cols-2 gap-3 bg-slate-950 p-3 rounded-lg border border-slate-800">
            <div>
              <label className="block text-[10px] text-slate-400 mb-1">Start Time (HH:MM)</label>
              <input
                type="text"
                value={quietHoursStart}
                onChange={(e) => setQuietHoursStart(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded p-1.5 text-slate-200"
              />
            </div>
            <div>
              <label className="block text-[10px] text-slate-400 mb-1">End Time (HH:MM)</label>
              <input
                type="text"
                value={quietHoursEnd}
                onChange={(e) => setQuietHoursEnd(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded p-1.5 text-slate-200"
              />
            </div>
          </div>
        )}
      </div>

      {/* Digest mode & Priority */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-slate-800">
        <div>
          <label className="block text-slate-300 font-semibold mb-1">Digest Delivery Mode</label>
          <select
            value={digestMode}
            onChange={(e) => setDigestMode(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
          >
            <option value="IMMEDIATE">Immediate Real-time</option>
            <option value="HOURLY_DIGEST">Hourly Digest Summary</option>
            <option value="DAILY_DIGEST">Daily EOD Digest</option>
          </select>
        </div>

        <div>
          <label className="block text-slate-300 font-semibold mb-1">Minimum Priority Threshold</label>
          <select
            value={minPriority}
            onChange={(e) => setMinPriority(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
          >
            <option value="LOW">All Priorities (LOW+)</option>
            <option value="MEDIUM">Medium Priority (MEDIUM+)</option>
            <option value="HIGH">High Priority (HIGH+)</option>
            <option value="CRITICAL">Critical Only (CRITICAL)</option>
          </select>
        </div>
      </div>

      <div className="flex justify-end pt-3 border-t border-slate-800">
        <button
          type="submit"
          disabled={isSaving}
          className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-lg font-semibold shadow-lg"
        >
          {isSaving ? "Saving..." : "Save Preferences"}
        </button>
      </div>
    </form>
  );
};
