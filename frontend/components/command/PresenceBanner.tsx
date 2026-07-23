import React from "react";

export interface PresenceUser {
  session_id: string;
  user_id: string;
  username: string;
  role: string;
  district_id?: string;
  current_activity: string;
  last_heartbeat: string;
}

interface PresenceBannerProps {
  presenceList: PresenceUser[];
}

export const PresenceBanner: React.FC<PresenceBannerProps> = ({ presenceList }) => {
  if (!presenceList || presenceList.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs text-slate-400 flex items-center justify-between">
        <span>No other active supervisors currently connected.</span>
        <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 flex flex-wrap items-center gap-3 text-xs text-slate-300">
      <div className="flex items-center gap-2 font-medium text-slate-400">
        <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <span>Active Command Presence ({presenceList.length}):</span>
      </div>
      {presenceList.map((user) => (
        <div key={user.session_id} className="bg-slate-800 px-2.5 py-1 rounded border border-slate-700 flex items-center gap-2">
          <span className="font-semibold text-sky-400">{user.username}</span>
          <span className="text-slate-500">({user.role})</span>
          <span className="text-slate-400 text-[11px]">— {user.current_activity}</span>
        </div>
      ))}
    </div>
  );
};

export default PresenceBanner;
