import React, { useState } from "react";
import { NotificationCard, NotificationDTO } from "./NotificationCard";

interface SearchPanelProps {
  onSearch: (query: string) => Promise<NotificationDTO[]>;
  onSelectNotification?: (notif: NotificationDTO) => void;
}

export const SearchPanel: React.FC<SearchPanelProps> = ({ onSearch, onSelectNotification }) => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<NotificationDTO[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setIsSearching(true);
    try {
      const res = await onSearch(query);
      setResults(res);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 font-mono text-xs shadow-xl">
      <div className="border-b border-slate-800 pb-2">
        <h3 className="text-sm font-bold text-slate-100">Full-Text Operational Notification Search</h3>
        <p className="text-[10px] text-slate-400">Search alerts, case titles, entity IDs, and historical dispatches.</p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          placeholder="Enter title, entity ID, or keyword..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 flex-1 focus:outline-none focus:border-purple-500"
        />
        <button
          type="submit"
          disabled={isSearching}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-semibold rounded-lg shadow"
        >
          {isSearching ? "Searching..." : "Search"}
        </button>
      </form>

      {results.length > 0 && (
        <div className="space-y-2 max-h-[350px] overflow-y-auto pr-1">
          {results.map((item) => (
            <NotificationCard
              key={item.notification_id}
              notification={item}
              onClick={onSelectNotification}
            />
          ))}
        </div>
      )}
    </div>
  );
};
