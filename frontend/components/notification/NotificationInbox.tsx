import React, { useState } from "react";
import { BulkActions } from "./BulkActions";
import { InboxToolbar } from "./InboxToolbar";
import { NotificationCard, NotificationDTO } from "./NotificationCard";
import { PinnedNotifications } from "./PinnedNotifications";

interface NotificationInboxProps {
  notifications: NotificationDTO[];
  unreadCount: number;
  onAcknowledge?: (id: string) => void;
  onDismiss?: (id: string) => void;
  onPin?: (id: string) => void;
  onStar?: (id: string) => void;
  onArchive?: (id: string) => void;
  onBulkAcknowledge?: (ids: string[]) => Promise<void>;
  onBulkDismiss?: (ids: string[]) => Promise<void>;
  onBulkArchive?: (ids: string[]) => Promise<void>;
  onRefresh?: () => void;
}

export const NotificationInbox: React.FC<NotificationInboxProps> = ({
  notifications,
  unreadCount,
  onAcknowledge,
  onDismiss,
  onPin,
  onStar,
  onArchive,
  onBulkAcknowledge,
  onBulkDismiss,
  onBulkArchive,
  onRefresh,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [category, setCategory] = useState("ALL");
  const [priority, setPriority] = useState("ALL");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isBulkModalOpen, setIsBulkModalOpen] = useState(false);

  const pinnedItems = (notifications || []).filter((n: any) => n.is_pinned);

  const filtered = (notifications || []).filter((item: any) => {
    if (category !== "ALL" && item.source_entity_type.upper() !== category) return false;
    if (priority !== "ALL" && String(item.priority).toUpperCase() !== priority) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      if (!item.title.toLowerCase().includes(q) && !item.body.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const toggleSelect = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((i) => i !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 font-mono text-xs shadow-2xl">
      {/* Top Header */}
      <div className="flex justify-between items-center border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>Operational Notification Inbox</span>
            <span className="px-2.5 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800 text-xs font-bold">
              {unreadCount} Unread
            </span>
          </h2>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Centralized operational communication hub with multi-channel dispatch governance.
          </p>
        </div>
      </div>

      {/* Pinned Section */}
      <PinnedNotifications pinnedItems={pinnedItems} onUnpin={onPin} />

      {/* Toolbar */}
      <InboxToolbar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        category={category}
        onCategoryChange={setCategory}
        priority={priority}
        onPriorityChange={setPriority}
        selectedCount={selectedIds.length}
        onOpenBulkModal={() => setIsBulkModalOpen(true)}
        onRefresh={onRefresh || (() => {})}
      />

      {/* List */}
      {filtered.length === 0 ? (
        <div className="text-xs text-slate-500 py-8 text-center bg-slate-950/40 rounded-lg border border-slate-800">
          No notifications match current inbox filters.
        </div>
      ) : (
        <div className="space-y-2.5 max-h-[520px] overflow-y-auto pr-1">
          {filtered.map((item) => {
            const isSelected = selectedIds.includes(item.notification_id);
            return (
              <div key={item.notification_id} className="flex items-start gap-2">
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggleSelect(item.notification_id)}
                  className="mt-4 rounded bg-slate-950 border-slate-800 text-purple-600 focus:ring-0 cursor-pointer"
                />
                <div className="flex-1">
                  <NotificationCard
                    notification={item}
                    onAcknowledge={onAcknowledge}
                    onDismiss={onDismiss}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Bulk Action Modal */}
      <BulkActions
        isOpen={isBulkModalOpen}
        onClose={() => setIsBulkModalOpen(false)}
        selectedCount={selectedIds.length}
        onBulkAcknowledge={async () => {
          await onBulkAcknowledge?.(selectedIds);
          setSelectedIds([]);
        }}
        onBulkDismiss={async () => {
          await onBulkDismiss?.(selectedIds);
          setSelectedIds([]);
        }}
        onBulkArchive={async () => {
          await onBulkArchive?.(selectedIds);
          setSelectedIds([]);
        }}
      />
    </div>
  );
};
