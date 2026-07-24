"use client";

import { createContext, useContext, useState, ReactNode, useCallback } from "react";
import { Plus, X } from "lucide-react";
import { useInvestigations, useInvestigationMutations } from "@/hooks/useApi";

interface AddToCaseContextType {
  openAddToCase: (entityId: string, entityType: string) => void;
}

const AddToCaseContext = createContext<AddToCaseContextType | undefined>(undefined);

export function AddToCaseProvider({ children }: { children: ReactNode }) {
  const [activeDialog, setActiveDialog] = useState<{ id: string, type: string } | null>(null);

  const openAddToCase = useCallback((entityId: string, entityType: string) => {
    setActiveDialog({ id: entityId, type: entityType });
  }, []);

  const closeDialog = () => setActiveDialog(null);

  return (
    <AddToCaseContext.Provider value={{ openAddToCase }}>
      {children}
      {activeDialog && <AddToCaseDialog entityId={activeDialog.id} entityType={activeDialog.type} onClose={closeDialog} />}
    </AddToCaseContext.Provider>
  );
}

export function useAddToCase() {
  const ctx = useContext(AddToCaseContext);
  if (!ctx) throw new Error("Missing AddToCaseProvider");
  return ctx;
}

function AddToCaseDialog({ entityId, entityType, onClose }: { entityId: string, entityType: string, onClose: () => void }) {
  const { data: investigations, isLoading } = useInvestigations("Open");
  const { addEntity } = useInvestigationMutations();

  const handleAttach = async (invId: string) => {
    await addEntity.mutateAsync({ invId, entityType, entityId });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[600] flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="bg-card border border-border w-full max-w-md rounded-lg shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between p-4 border-b border-border bg-muted/50">
          <div className="font-mono font-bold text-sm tracking-widest text-primary uppercase">
            ATTACH {entityType}
          </div>
          <button onClick={onClose} className="p-1 hover:bg-background rounded transition-colors text-muted-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-4 font-mono text-sm border-b border-border">
          <span className="text-muted-foreground">Selected Entity: </span> 
          <span className="font-bold">{entityId}</span>
        </div>

        <div className="flex-1 overflow-y-auto max-h-96 p-2 space-y-2">
          {isLoading ? (
            <div className="p-4 text-center font-mono text-muted-foreground animate-pulse">LOADING OPEN CASES...</div>
          ) : investigations && investigations.length > 0 ? (
            investigations.map((inv: any) => (
              <button 
                key={inv.id}
                onClick={() => handleAttach(inv.id)}
                className="w-full text-left p-3 hover:bg-muted rounded border border-transparent hover:border-primary/50 transition-colors flex items-center justify-between group"
              >
                <div>
                  <div className="text-xs text-muted-foreground font-mono">{inv.id}</div>
                  <div className="font-bold truncate max-w-[300px]">{inv.title}</div>
                </div>
                <Plus className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
              </button>
            ))
          ) : (
            <div className="p-4 text-center font-mono text-muted-foreground">
              NO OPEN INVESTIGATIONS.<br/>CREATE ONE FROM THE DASHBOARD.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
