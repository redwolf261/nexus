"use client";

import { useState } from "react";
import { SiloBusterGraph } from "@/features/silo-buster/SiloBusterGraph";
import { Search } from "lucide-react";

export default function SiloBusterPage() {
  const [targetFir, setTargetFir] = useState("FIR-RBG-2021-00003");
  const [searchInput, setSearchInput] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput) setTargetFir(searchInput);
  };

  return (
    <div className="flex flex-col h-full w-full">
      <div className="h-16 border-b border-border bg-card px-6 flex items-center justify-between shrink-0 z-10 shadow-sm">
        <div>
          <h1 className="text-lg font-bold">Silo Buster</h1>
          <p className="text-xs text-muted-foreground">Cross-jurisdictional AI link analysis</p>
        </div>
        
        <form onSubmit={handleSearch} className="relative w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input 
            type="text" 
            placeholder="Enter Target FIR ID..." 
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full bg-input border border-border rounded-md py-1.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-ring font-mono uppercase"
          />
        </form>
      </div>
      
      <div className="flex-1 bg-background relative overflow-hidden">
        <SiloBusterGraph targetFir={targetFir} />
      </div>
    </div>
  );
}
