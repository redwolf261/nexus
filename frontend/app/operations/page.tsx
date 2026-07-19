export default function OperationsPage() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center h-full text-center relative overflow-hidden">
      {/* Tactical wireframe background pattern */}
      <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px] pointer-events-none" />
      
      <div className="relative z-10 border border-border bg-card p-12 rounded-lg max-w-xl shadow-2xl">
        <div className="text-destructive font-mono font-bold text-lg mb-4 flex items-center justify-center gap-3">
          <span className="w-3 h-3 rounded-full bg-destructive animate-pulse" />
          CLEARANCE REQUIRED
        </div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">Tactical Operations</h1>
        <p className="text-muted-foreground leading-relaxed">
          The Field Officer Deployment and Tactical Operations module requires Level-4 security clearance. Please insert your biometric key to access live field telemetry.
        </p>
      </div>
    </div>
  );
}
