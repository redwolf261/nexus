export default function GraphPage() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center h-full text-center relative overflow-hidden">
      {/* Tactical wireframe background pattern */}
      <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px] pointer-events-none" />
      
      <div className="relative z-10 border border-border bg-card p-12 rounded-lg max-w-xl shadow-2xl">
        <div className="text-primary font-mono font-bold text-lg mb-4 flex items-center justify-center gap-3">
          <span className="w-3 h-3 rounded-full bg-primary animate-pulse" />
          SYSTEM INITIALIZING
        </div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">Global Knowledge Graph</h1>
        <p className="text-muted-foreground leading-relaxed">
          The full Neo4j Global Knowledge Graph explorer is currently indexing the latest state-wide telecommunication feeds. Please use the targeted <strong>Silo Buster</strong> for immediate campaign analysis.
        </p>
      </div>
    </div>
  );
}
