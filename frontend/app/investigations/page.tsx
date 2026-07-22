"use client";

import { useInvestigations, useInvestigationMutations } from "@/hooks/useApi";
import { Shield, Plus, FolderOpen, ArrowRight } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export default function InvestigationsList() {
  const { data: investigations, isLoading } = useInvestigations();
  const { create } = useInvestigationMutations();
  const [isCreating, setIsCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");

  const handleCreate = async () => {
    if (!newTitle) return;
    setIsCreating(true);
    await create.mutateAsync({ title: newTitle, priority: "Medium" });
    setNewTitle("");
    setIsCreating(false);
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-bold font-mono tracking-widest uppercase flex items-center gap-3 text-primary">
            <Shield className="w-6 h-6" /> Investigation Cases
          </h1>
          <p className="text-muted-foreground mt-1">Manage active intelligence workspaces and evidence boards.</p>
        </div>
        <div className="flex gap-2">
          <input 
            type="text" 
            placeholder="New Case Title..." 
            className="bg-card border border-border rounded px-3 py-1 text-sm font-mono w-64"
            value={newTitle}
            onChange={e => setNewTitle(e.target.value)}
          />
          <button 
            onClick={handleCreate}
            disabled={isCreating || !newTitle}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-1 rounded font-bold hover:bg-primary/90 transition disabled:opacity-50"
          >
            <Plus className="w-4 h-4" /> NEW CASE
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="font-mono text-center py-20 text-muted-foreground animate-pulse">LOADING CASES...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {investigations?.map((inv: any) => (
            <Link key={inv.id} href={`/investigations/${inv.id}`} className="group block h-full">
              <div className="bg-card border border-border rounded-lg p-5 hover:border-primary/50 transition-colors h-full flex flex-col cursor-pointer">
                <div className="flex justify-between items-start mb-2">
                  <div className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-muted text-muted-foreground">{inv.id}</div>
                  <div className={`text-xs font-bold uppercase tracking-wider ${inv.status === 'Open' ? 'text-green-500' : 'text-muted-foreground'}`}>{inv.status}</div>
                </div>
                <h3 className="text-lg font-bold font-mono mb-2 group-hover:text-primary transition-colors line-clamp-2">{inv.title}</h3>
                <div className="text-sm text-muted-foreground mb-4 line-clamp-3 flex-1">{inv.description || "No description provided."}</div>
                
                <div className="flex items-center justify-between pt-3 border-t border-border/50 text-xs text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <FolderOpen className="w-4 h-4" /> {new Date(inv.updated_at).toLocaleDateString()}
                  </div>
                  <div className="flex items-center gap-1 group-hover:text-primary font-bold">
                    OPEN <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </div>
            </Link>
          ))}
          
          {(!investigations || investigations.length === 0) && (
            <div className="col-span-full text-center py-20 border border-dashed border-border rounded-lg bg-card/30">
              <Shield className="w-12 h-12 text-muted-foreground/30 mx-auto mb-3" />
              <div className="font-mono text-muted-foreground">NO ACTIVE INVESTIGATIONS</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
