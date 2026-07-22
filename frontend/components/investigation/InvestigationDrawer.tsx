"use client";

import { createContext, useContext, useState, ReactNode, useCallback } from "react";
import { X, Clock, Activity, FileText, Database, ShieldAlert, Car, Phone, Plus } from "lucide-react";
import { useFIRDetail, usePersonDetail, useVehicleDetail, useCriminalDetail, useCampaignSummary, useCampaignTimeline } from "@/hooks/useApi";
import { useAddToCase } from "@/components/investigation/AddToCaseProvider";
import { ErrorBoundary } from "@/components/layout/ErrorBoundary";

type DrawerType = "FIR" | "PERSON" | "VEHICLE" | "CAMPAIGN" | "PHONE" | "CRIMINAL" | "MASTERMIND" | null;

interface DrawerContextType {
  activeEntity: { id: string, type: DrawerType } | null;
  openDrawer: (id: string, type: DrawerType) => void;
  closeDrawer: () => void;
}

const DrawerContext = createContext<DrawerContextType | undefined>(undefined);

export function DrawerProvider({ children }: { children: ReactNode }) {
  const [activeEntity, setActiveEntity] = useState<{ id: string, type: DrawerType } | null>(null);

  const openDrawer = useCallback((id: string, type: DrawerType) => {
    setActiveEntity({ id, type });
  }, []);

  const closeDrawer = useCallback(() => {
    setActiveEntity(null);
  }, []);

  return (
    <DrawerContext.Provider value={{ activeEntity, openDrawer, closeDrawer }}>
      {children}
      <InvestigationDrawer activeEntity={activeEntity} closeDrawer={closeDrawer} />
    </DrawerContext.Provider>
  );
}

export function useInvestigationDrawer() {
  const ctx = useContext(DrawerContext);
  if (!ctx) throw new Error("Missing DrawerProvider");
  return ctx;
}

function FIRDrawerContent({ id }: { id: string }) {
  const { data, isLoading, error } = useFIRDetail(id);
  const { openDrawer } = useInvestigationDrawer();

  if (isLoading) return <div className="p-4 font-mono animate-pulse">LOADING...</div>;
  if (error || !data) return <div className="p-4 text-destructive font-mono">UPLINK FAILED: {error?.message || "Not found"}</div>;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
          <Activity className="w-4 h-4 text-primary" /> Incident Details
        </div>
        <div className="bg-card border border-border p-3 rounded-md font-mono text-sm space-y-1">
          <div><span className="text-muted-foreground uppercase">Type:</span> {data.fir.crime_type}</div>
          <div><span className="text-muted-foreground uppercase">Category:</span> {data.fir.crime_category}</div>
          <div><span className="text-muted-foreground uppercase">Status:</span> {data.fir.status}</div>
          <div><span className="text-muted-foreground uppercase">Loss:</span> ₹{data.fir.estimated_loss_inr?.toLocaleString() || "0"}</div>
          {data.fir.is_gang_crime && <div className="text-destructive font-bold mt-2">⚠️ GANG RELATED CRIME</div>}
        </div>
      </div>

      {(data.accused.length > 0 || data.linked_vehicles.length > 0 || data.linked_phones.length > 0) && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
            <Database className="w-4 h-4 text-primary" /> Linked Entities
          </div>
          <div className="bg-card border border-border rounded-md p-3 font-mono text-sm space-y-2">
            {data.accused.map(a => (
              <div key={a.accused_id} className="cursor-pointer hover:text-primary transition-colors" onClick={() => openDrawer(a.accused_id, "CRIMINAL")}>
                &gt; ACCUSED: {a.name_en || a.accused_id} {a.is_arrested ? "(ARRESTED)" : ""}
              </div>
            ))}
            {data.linked_vehicles.map(v => (
              <div key={v.vehicle_id} className="cursor-pointer hover:text-primary transition-colors" onClick={() => openDrawer(v.vehicle_id, "VEHICLE")}>
                &gt; VEHICLE: {v.license_plate} {v.is_stolen ? "(STOLEN)" : ""}
              </div>
            ))}
            {data.linked_phones.map(p => (
              <div key={p.phone_id} className="cursor-pointer hover:text-primary transition-colors" onClick={() => openDrawer(p.phone_id, "PHONE")}>
                &gt; PHONE: {p.phone_number} {p.is_burner ? "(BURNER)" : ""}
              </div>
            ))}
          </div>
        </div>
      )}

      {data.investigation_logs.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
            <Clock className="w-4 h-4 text-primary" /> Investigation Timeline
          </div>
          <div className="relative border-l border-border ml-2 pl-4 py-2 space-y-4 font-mono text-xs">
            {data.investigation_logs.map(log => (
              <div key={log.log_id} className="relative">
                <div className="absolute -left-[21px] top-1 w-2 h-2 bg-primary rounded-full ring-4 ring-background" />
                <div className="text-muted-foreground mb-1">{log.timestamp || "Unknown Time"}</div>
                <div className="text-foreground bg-card border border-border p-2 rounded">
                  <span className="font-bold text-primary">{log.event_type}</span>: {log.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function PersonDrawerContent({ id }: { id: string }) {
  const { data, isLoading, error } = usePersonDetail(id);
  const { openDrawer } = useInvestigationDrawer();

  if (isLoading) return <div className="p-4 font-mono animate-pulse">LOADING...</div>;
  if (error || !data) return <div className="p-4 text-destructive font-mono">UPLINK FAILED: {error?.message || "Not found"}</div>;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
          <Activity className="w-4 h-4 text-primary" /> Profile
        </div>
        <div className="bg-card border border-border p-3 rounded-md font-mono text-sm space-y-1">
          <div><span className="text-muted-foreground uppercase">Name:</span> {data.person.name_en}</div>
          <div><span className="text-muted-foreground uppercase">Age/Gender:</span> {data.person.age} / {data.person.gender}</div>
          <div><span className="text-muted-foreground uppercase">Phone:</span> {data.person.phone_primary}</div>
          <div><span className="text-muted-foreground uppercase">District:</span> {data.person.district_name}</div>
          {data.criminal && (
             <div className="text-destructive font-bold mt-2 cursor-pointer hover:underline" onClick={() => openDrawer(data.criminal!.criminal_id, "CRIMINAL")}>
               ⚠️ CRIMINAL RECORD FOUND (Click to view)
             </div>
          )}
        </div>
      </div>
      
      {(data.vehicles.length > 0 || data.phones.length > 0) && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
            <Database className="w-4 h-4 text-primary" /> Registered Assets
          </div>
          <div className="bg-card border border-border rounded-md p-3 font-mono text-sm space-y-2">
            {data.vehicles.map(v => (
              <div key={v.vehicle_id} className="cursor-pointer hover:text-primary transition-colors" onClick={() => openDrawer(v.vehicle_id, "VEHICLE")}>
                &gt; VEHICLE: {v.license_plate} ({v.make} {v.model})
              </div>
            ))}
            {data.phones.map(p => (
              <div key={p.phone_id} className="cursor-pointer hover:text-primary transition-colors" onClick={() => openDrawer(p.phone_id, "PHONE")}>
                &gt; PHONE: {p.phone_number} ({p.provider})
              </div>
            ))}
          </div>
        </div>
      )}
      
      {data.linked_firs.length > 0 && (
        <div className="space-y-2">
           <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
             <FileText className="w-4 h-4 text-primary" /> Linked FIRs
           </div>
           <div className="bg-card border border-border rounded-md p-3 font-mono text-sm space-y-2">
              {data.linked_firs.map(f => (
                 <div key={f.fir_id} className="cursor-pointer hover:text-primary transition-colors" onClick={() => openDrawer(f.fir_id, "FIR")}>
                   &gt; {f.fir_number || f.fir_id} - {f.crime_type}
                 </div>
              ))}
           </div>
        </div>
      )}
    </div>
  );
}

function VehicleDrawerContent({ id }: { id: string }) {
  const { data, isLoading, error } = useVehicleDetail(id);
  const { openDrawer } = useInvestigationDrawer();

  if (isLoading) return <div className="p-4 font-mono animate-pulse">LOADING...</div>;
  if (error || !data) return <div className="p-4 text-destructive font-mono">UPLINK FAILED: {error?.message || "Not found"}</div>;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
          <Car className="w-4 h-4 text-primary" /> Vehicle Info
        </div>
        <div className="bg-card border border-border p-3 rounded-md font-mono text-sm space-y-1">
          <div><span className="text-muted-foreground uppercase">Plate:</span> {data.vehicle.license_plate}</div>
          <div><span className="text-muted-foreground uppercase">Make/Model:</span> {data.vehicle.make} {data.vehicle.model}</div>
          <div><span className="text-muted-foreground uppercase">Color:</span> {data.vehicle.color}</div>
          {data.vehicle.is_stolen && <div className="text-destructive font-bold mt-2">⚠️ REPORTED STOLEN</div>}
        </div>
      </div>

      {data.owner && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
            <Database className="w-4 h-4 text-primary" /> Registered Owner
          </div>
          <div className="bg-card border border-border rounded-md p-3 font-mono text-sm">
             <div className="cursor-pointer hover:text-primary transition-colors" onClick={() => openDrawer(data.owner!.citizen_id, "PERSON")}>
               &gt; {data.owner.name_en} ({data.owner.citizen_id})
             </div>
          </div>
        </div>
      )}

      {data.linked_firs.length > 0 && (
        <div className="space-y-2">
           <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
             <FileText className="w-4 h-4 text-primary" /> Used in Crimes
           </div>
           <div className="bg-card border border-border rounded-md p-3 font-mono text-sm space-y-2">
              {data.linked_firs.map(f => (
                 <div key={f.fir_id} className="cursor-pointer hover:text-primary transition-colors" onClick={() => openDrawer(f.fir_id, "FIR")}>
                   &gt; {f.fir_number || f.fir_id} - {f.crime_type}
                 </div>
              ))}
           </div>
        </div>
      )}
    </div>
  );
}

function CriminalDrawerContent({ id }: { id: string }) {
  const { data, isLoading, error } = useCriminalDetail(id);
  const { openDrawer } = useInvestigationDrawer();

  if (isLoading) return <div className="p-4 font-mono animate-pulse">LOADING...</div>;
  if (error || !data) return <div className="p-4 text-destructive font-mono">UPLINK FAILED: {error?.message || "Not found"}</div>;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
          <ShieldAlert className="w-4 h-4 text-primary" /> Criminal Dossier
        </div>
        <div className="bg-card border border-border p-3 rounded-md font-mono text-sm space-y-1">
          <div><span className="text-muted-foreground uppercase">Name:</span> {data.criminal.name_en}</div>
          <div><span className="text-muted-foreground uppercase">Risk Level:</span> {data.criminal.risk_level}</div>
          <div><span className="text-muted-foreground uppercase">Expertise:</span> {data.criminal.expertise}</div>
          <div><span className="text-muted-foreground uppercase">Total Crimes:</span> {data.criminal.total_crimes_committed}</div>
          {data.criminal.is_currently_active && <div className="text-destructive font-bold mt-2">⚠️ CURRENTLY ACTIVE</div>}
        </div>
      </div>

      {data.gang && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
            <Database className="w-4 h-4 text-primary" /> Gang Affiliation
          </div>
          <div className="bg-card border border-border rounded-md p-3 font-mono text-sm">
             <div><span className="text-muted-foreground uppercase">Gang:</span> {data.gang.name}</div>
             <div><span className="text-muted-foreground uppercase">Threat:</span> {data.gang.threat_level}</div>
          </div>
        </div>
      )}
      
      {data.arrests.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
            <Clock className="w-4 h-4 text-primary" /> Arrest History
          </div>
          <div className="relative border-l border-border ml-2 pl-4 py-2 space-y-4 font-mono text-xs">
            {data.arrests.map(a => (
              <div key={a.arrest_id} className="relative">
                <div className="absolute -left-[21px] top-1 w-2 h-2 bg-destructive rounded-full ring-4 ring-background" />
                <div className="text-muted-foreground mb-1">{a.arrest_date}</div>
                <div className="text-foreground bg-card border border-border p-2 rounded">
                   Arrested at {a.arrest_location}. {a.bail_granted ? "Granted Bail." : "No Bail."} {a.is_convicted ? "Convicted." : ""}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {data.linked_firs.length > 0 && (
        <div className="space-y-2">
           <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
             <FileText className="w-4 h-4 text-primary" /> Associated Cases
           </div>
           <div className="bg-card border border-border rounded-md p-3 font-mono text-sm space-y-2">
              {data.linked_firs.map(f => (
                 <div key={f.fir_id} className="cursor-pointer hover:text-primary transition-colors" onClick={() => openDrawer(f.fir_id, "FIR")}>
                   &gt; {f.fir_number || f.fir_id} - {f.crime_type}
                 </div>
              ))}
           </div>
        </div>
      )}
    </div>
  );
}

function CampaignDrawerContent({ id }: { id: string }) {
  const { data: summary, isLoading: loadingSum, error: errSum } = useCampaignSummary(id);
  const { data: timeline, isLoading: loadingTime, error: errTime } = useCampaignTimeline(id);
  
  if (loadingSum || loadingTime) return <div className="p-4 font-mono animate-pulse">LOADING...</div>;
  if (errSum || errTime || !summary || !timeline) return <div className="p-4 text-destructive font-mono">UPLINK FAILED: {errSum?.message || errTime?.message || "Not found"}</div>;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
          <Activity className="w-4 h-4 text-primary" /> Campaign Intelligence
        </div>
        <div className="bg-card border border-border p-3 rounded-md font-mono text-sm space-y-1">
          <div><span className="text-muted-foreground uppercase">Category:</span> {summary.crime_category || "Unknown"}</div>
          <div><span className="text-muted-foreground uppercase">Status:</span> {summary.status}</div>
          <div><span className="text-muted-foreground uppercase">Mastermind:</span> {summary.mastermind}</div>
          <div><span className="text-muted-foreground uppercase">Gang:</span> {summary.gang}</div>
        </div>
      </div>
      
      <div className="space-y-2">
         <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
           <Database className="w-4 h-4 text-primary" /> Linked Identifiers
         </div>
         <div className="bg-card border border-border rounded-md p-3 font-mono text-sm space-y-1 text-muted-foreground">
            <div>&gt; VEHICLES: {summary.vehicles.length > 0 ? summary.vehicles.join(", ") : "None detected"}</div>
            <div>&gt; PHONES: {summary.phones.length > 0 ? summary.phones.join(", ") : "None detected"}</div>
         </div>
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground font-bold border-b border-border pb-1">
          <Clock className="w-4 h-4 text-primary" /> Event Timeline
        </div>
        <div className="relative border-l border-border ml-2 pl-4 py-2 space-y-4 font-mono text-xs">
          {timeline.events.map((evt, i) => (
            <div key={i} className="relative">
              <div className="absolute -left-[21px] top-1 w-2 h-2 bg-primary rounded-full ring-4 ring-background" />
              <div className="text-muted-foreground mb-1">Day {evt.day}</div>
              <div className="text-foreground bg-card border border-border p-2 rounded">
                 <span className="font-bold text-primary">{evt.event_type}</span>: {evt.description}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function GenericDrawerContent({ id, type }: { id: string, type: string }) {
  return (
    <div className="p-4 font-mono text-sm space-y-4">
      <div className="bg-muted p-4 rounded border border-border">
        No detailed view implemented for {type} ({id}).
      </div>
    </div>
  );
}


function InvestigationDrawer({ activeEntity, closeDrawer }: { activeEntity: { id: string, type: DrawerType } | null, closeDrawer: () => void }) {
  const { openAddToCase } = useAddToCase();

  if (!activeEntity) return null;

  return (
    <div className="fixed top-16 right-0 bottom-12 w-[450px] bg-sidebar border-l border-border z-[500] shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
      <div className="flex items-center justify-between p-4 border-b border-border bg-card shrink-0">
        <div>
          <div className="text-xs font-bold tracking-widest text-primary uppercase">{activeEntity.type} INTELLIGENCE</div>
          <div className="text-lg font-mono font-bold mt-1 break-all pr-4">{activeEntity.id}</div>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={() => openAddToCase(activeEntity.id, activeEntity.type as string)}
            className="p-2 hover:bg-muted rounded transition-colors text-primary flex items-center gap-1 font-bold text-xs"
            title="Add to Case"
          >
            <Plus className="w-5 h-5" />
            <span className="sr-only">Add to Case</span>
          </button>
          <button onClick={closeDrawer} className="p-2 hover:bg-muted rounded transition-colors text-muted-foreground">
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <ErrorBoundary fallbackMessage="The investigation details failed to load due to a systemic error.">
          {activeEntity.type === "FIR" && <FIRDrawerContent id={activeEntity.id} />}
          {activeEntity.type === "PERSON" && <PersonDrawerContent id={activeEntity.id} />}
          {activeEntity.type === "VEHICLE" && <VehicleDrawerContent id={activeEntity.id} />}
          {(activeEntity.type === "CRIMINAL" || activeEntity.type === "MASTERMIND") && <CriminalDrawerContent id={activeEntity.id} />}
          {activeEntity.type === "CAMPAIGN" && <CampaignDrawerContent id={activeEntity.id} />}
          {activeEntity.type === "PHONE" && <GenericDrawerContent id={activeEntity.id} type="PHONE" />}
        </ErrorBoundary>
      </div>
    </div>
  );
}
