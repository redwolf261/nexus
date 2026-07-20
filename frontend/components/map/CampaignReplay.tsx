"use client";

import { useState, useEffect } from "react";
import { Play, Pause, SkipForward, SkipBack } from "lucide-react";
import { useCampaignTimeline } from "@/hooks/useApi";
import { useDemo } from "@/contexts/DemoContext";

// Simple pseudo-random function to generate consistent coordinates based on string ID
const generateCoords = (id: string) => {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = id.charCodeAt(i) + ((hash << 5) - hash);
  }
  const latOffset = (hash % 100) / 200; // between -0.5 and +0.5
  const lngOffset = ((hash >> 3) % 100) / 200;
  
  return {
    lat: 15.3173 + latOffset,
    lng: 75.7139 + lngOffset
  };
};

export function CampaignReplay({ onFrameChange }: { onFrameChange: (frame: any) => void }) {
  const { stage } = useDemo();
  
  // We use CAMP-0002 for the demo replay (or we could make it dynamic later)
  const campaignId = "CAMP-0002";
  const { data: timelineData } = useCampaignTimeline(campaignId);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);

  useEffect(() => {
    if (stage === "REPLAY") {
      setIsPlaying(true);
    }
  }, [stage]);

  const frames = timelineData?.events || [];

  useEffect(() => {
    if (!isPlaying || frames.length === 0) return;

    const interval = setInterval(() => {
      setCurrentFrame((prev) => {
        if (prev >= frames.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [isPlaying, frames]);

  useEffect(() => {
    if (frames[currentFrame]) {
      const evt = frames[currentFrame];
      const coords = generateCoords(evt.entity_id);
      
      onFrameChange({
        description: `Day ${evt.day}: ${evt.event_type} - ${evt.description}`,
        focus_latitude: coords.lat,
        focus_longitude: coords.lng,
        zoom: 12,
        highlight_node_id: evt.entity_id
      });
    }
  }, [currentFrame, frames, onFrameChange]);

  if (!timelineData || frames.length === 0) return null;

  const currentEvent = frames[currentFrame];

  return (
    <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-[1000] bg-card/90 backdrop-blur-md border border-border rounded-lg p-4 w-[500px] shadow-xl">
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
            CAMPAIGN REPLAY: {timelineData.campaign_id}
          </div>
          <div className="text-xs font-mono text-primary bg-primary/10 px-2 py-1 rounded">
            FRAME {currentFrame + 1} / {frames.length}
          </div>
        </div>

        <div className="text-sm font-mono leading-relaxed h-10 flex items-center">
          &gt; Day {currentEvent?.day}: {currentEvent?.event_type} - {currentEvent?.description}
        </div>

        <div className="flex items-center gap-4 pt-2 border-t border-border/50">
          <button 
            onClick={() => setCurrentFrame(Math.max(0, currentFrame - 1))}
            className="p-2 hover:bg-muted rounded transition-colors"
          >
            <SkipBack className="w-4 h-4 text-foreground" />
          </button>
          
          <button 
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-3 bg-primary hover:bg-primary/80 rounded-full transition-colors"
          >
            {isPlaying ? (
              <Pause className="w-5 h-5 text-primary-foreground" />
            ) : (
              <Play className="w-5 h-5 text-primary-foreground" />
            )}
          </button>
          
          <button 
            onClick={() => setCurrentFrame(Math.min(frames.length - 1, currentFrame + 1))}
            className="p-2 hover:bg-muted rounded transition-colors"
          >
            <SkipForward className="w-4 h-4 text-foreground" />
          </button>

          <div className="flex-1 ml-4 h-1 bg-muted rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${((currentFrame + 1) / frames.length) * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
