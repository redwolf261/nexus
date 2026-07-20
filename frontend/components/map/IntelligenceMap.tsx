"use client";

import { useEffect, useState, useCallback } from "react";
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useQuery } from "@tanstack/react-query";

// Fix Leaflet default marker icon issue in Next.js
const customIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// A red icon for crimes
const crimeIcon = new L.Icon({
  ...customIcon.options,
  className: "hue-rotate-[150deg] filter" // Quick CSS trick to turn blue marker red
});

import { CampaignReplay } from "./CampaignReplay";
import { useLiveIncident } from "@/hooks/useLiveIncident";
import { useInvestigationDrawer } from "@/components/investigation/InvestigationDrawer";
import { useFIRs } from "@/hooks/useApi";
import { Shield } from "lucide-react";

// Create a custom SVG icon for Patrols
const patrolHtml = `<div style="background-color: #00e5ff; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 10px #00e5ff; border: 2px solid white;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg></div>`;
const patrolIcon = new L.DivIcon({
  html: patrolHtml,
  className: "patrol-icon",
  iconSize: [24, 24],
  iconAnchor: [12, 12]
});

// A simple animated patrol unit
function PatrolUnit({ start, end }: { start: [number, number], end: [number, number] }) {
  const [pos, setPos] = useState(start);

  useEffect(() => {
    let t = 0;
    const interval = setInterval(() => {
      t += 0.05;
      if (t > 1) t = 0; // Loop back
      // Linear interpolation
      setPos([
        start[0] + (end[0] - start[0]) * t,
        start[1] + (end[1] - start[1]) * t
      ]);
    }, 100);
    return () => clearInterval(interval);
  }, [start, end]);

  return (
    <Marker position={pos} icon={patrolIcon}>
      <Popup className="tactical-popup">
        <div className="font-mono text-sm bg-primary/10 text-primary border border-primary p-2 rounded-md">
          <div className="font-bold flex items-center gap-2 mb-1"><Shield className="w-4 h-4" /> PATROL UNIT ALPHA</div>
          <div>STATUS: EN ROUTE</div>
          <div>ETA: 4 MINS</div>
        </div>
      </Popup>
    </Marker>
  );
}

function MapController({ center, zoom }: { center: [number, number], zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, zoom, { duration: 1.5 });
  }, [center, zoom, map]);
  return null;
}

export default function IntelligenceMap() {
  const { activeIncident } = useLiveIncident();
  const { openDrawer } = useInvestigationDrawer();

  const [mapState, setMapState] = useState({
    center: [15.3173, 75.7139] as [number, number],
    zoom: 7,
    highlightNodeId: null as string | null
  });

  const [layers, setLayers] = useState({
    boundaries: true,
    firs: true,
    patrols: true
  });

  const { data: boundaries } = useQuery({
    queryKey: ["boundaries"],
    queryFn: async () => {
      const res = await fetch("/geojson/boundaries.geojson");
      return res.json();
    }
  });

  const { data: firs } = useFIRs({ limit: 500 });

  // If a live incident occurs, fly to it
  useEffect(() => {
    if (activeIncident) {
      setMapState({
        center: [activeIncident.latitude, activeIncident.longitude],
        zoom: 14,
        highlightNodeId: null
      });
    }
  }, [activeIncident]);

  const handleFrameChange = useCallback((frame: any) => {
    setMapState({
      center: [frame.focus_latitude, frame.focus_longitude],
      zoom: frame.zoom,
      highlightNodeId: frame.highlight_node_id
    });
    
    // Automatically open drawer if demo mode is highlighting a node
    if (frame.highlight_node_id) {
      openDrawer(frame.highlight_node_id, "FIR");
    }
  }, [openDrawer]);

  return (
    <div className="w-full h-full relative">
      <MapContainer 
        center={mapState.center} 
        zoom={mapState.zoom} 
        style={{ height: "100%", width: "100%", background: "#0a0a0a" }}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {layers.boundaries && boundaries && (
          <GeoJSON 
            data={boundaries} 
            style={{
              color: "#00e5ff",
              weight: 1,
              opacity: 0.3,
              fillOpacity: 0.05
            }} 
          />
        )}

        {layers.firs && firs?.map((fir) => {
          const isHighlighted = mapState.highlightNodeId === fir.fir_id;
          if (!fir.latitude || !fir.longitude) return null;
          return (
            <Marker 
              key={fir.fir_id}
              position={[fir.latitude, fir.longitude]}
              icon={crimeIcon}
              opacity={mapState.highlightNodeId && !isHighlighted ? 0.2 : 1}
              eventHandlers={{
                click: () => openDrawer(fir.fir_id, "FIR"),
              }}
            >
              <Popup className="tactical-popup">
                <div className="font-mono text-sm bg-card text-card-foreground p-2 rounded-sm border border-border">
                  <div className="text-primary font-bold mb-1">{fir.fir_number || fir.fir_id}</div>
                  <div>TYPE: {fir.crime_type}</div>
                  <div>STATUS: {fir.status}</div>
                  <div>DIST: {fir.district_name || fir.district_id}</div>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {activeIncident && (
          <Marker 
            position={[activeIncident.latitude, activeIncident.longitude]}
            icon={crimeIcon}
            eventHandlers={{
              click: () => openDrawer(activeIncident.id, "FIR"),
            }}
          >
            <Popup className="tactical-popup">
              <div className="font-mono text-sm bg-destructive/10 text-destructive border border-destructive p-3 rounded-md shadow-xl backdrop-blur-md">
                <div className="font-bold text-lg mb-1 flex items-center gap-2 animate-pulse">
                  <span className="w-2 h-2 bg-destructive rounded-full" />
                  LIVE ALERT
                </div>
                <div className="text-destructive font-bold">{activeIncident.id}</div>
                <div>TYPE: {activeIncident.type}</div>
                <div>DIST: {activeIncident.district}</div>
              </div>
            </Popup>
          </Marker>
        )}

        {layers.patrols && (
          <PatrolUnit start={[12.9716, 77.5946]} end={[12.9816, 77.6046]} />
        )}

        <MapController center={mapState.center} zoom={mapState.zoom} />
      </MapContainer>
      
      {/* Overlay UI */}
      <div className="absolute top-4 left-4 z-[400] pointer-events-none">
        <h2 className="text-2xl font-bold tracking-tight text-white drop-shadow-md">KARNATAKA INTELLIGENCE MAP</h2>
        <p className="text-primary font-mono text-sm uppercase">Live Strategic Overview</p>
      </div>

      {/* Layer Manager UI */}
      <div className="absolute top-4 right-4 z-[400] bg-card/90 backdrop-blur-md border border-border p-4 rounded-md shadow-xl w-48">
        <h3 className="text-xs font-bold text-primary tracking-widest uppercase mb-3 border-b border-border pb-1">Tactical Layers</h3>
        <div className="space-y-2 text-sm font-mono">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={layers.boundaries} onChange={(e) => setLayers(l => ({ ...l, boundaries: e.target.checked }))} className="accent-primary" />
            District Borders
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={layers.firs} onChange={(e) => setLayers(l => ({ ...l, firs: e.target.checked }))} className="accent-primary" />
            Active FIRs
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={layers.patrols} onChange={(e) => setLayers(l => ({ ...l, patrols: e.target.checked }))} className="accent-primary" />
            Patrol Routes
          </label>
          <label className="flex items-center gap-2 cursor-pointer opacity-50">
            <input type="checkbox" disabled className="accent-primary" />
            CCTV Network
          </label>
        </div>
      </div>

      {/* Campaign Replay UI */}
      <CampaignReplay onFrameChange={handleFrameChange} />
    </div>
  );
}
