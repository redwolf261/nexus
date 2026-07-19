"use client";

import { useState, useEffect } from "react";
import { Play, Pause, SkipForward, SkipBack } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useDemo } from "@/contexts/DemoContext";

export function CampaignReplay({ onFrameChange }: { onFrameChange: (frame: any) => void }) {
  const { stage } = useDemo();
  const { data: animation } = useQuery({
    queryKey: ["animation"],
    queryFn: async () => {
      const res = await fetch("/demo/animation.json");
      return res.json();
    }
  });

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);

  useEffect(() => {
    if (stage === "REPLAY") {
      setIsPlaying(true);
    }
  }, [stage]);

  useEffect(() => {
    if (!isPlaying || !animation) return;

    const interval = setInterval(() => {
      setCurrentFrame((prev) => {
        if (prev >= animation.frames.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [isPlaying, animation]);

  useEffect(() => {
    if (animation?.frames[currentFrame]) {
      onFrameChange(animation.frames[currentFrame]);
    }
  }, [currentFrame, animation, onFrameChange]);

  if (!animation) return null;

  const frameData = animation.frames[currentFrame];

  return (
    <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-[1000] bg-card/90 backdrop-blur-md border border-border rounded-lg p-4 w-[500px] shadow-xl">
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
            CAMPAIGN REPLAY: {animation.campaign_id}
          </div>
          <div className="text-xs font-mono text-primary bg-primary/10 px-2 py-1 rounded">
            FRAME {currentFrame + 1} / {animation.frames.length}
          </div>
        </div>

        <div className="text-sm font-mono leading-relaxed h-10 flex items-center">
          &gt; {frameData?.description}
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
            onClick={() => setCurrentFrame(Math.min(animation.frames.length - 1, currentFrame + 1))}
            className="p-2 hover:bg-muted rounded transition-colors"
          >
            <SkipForward className="w-4 h-4 text-foreground" />
          </button>

          <div className="flex-1 ml-4 h-1 bg-muted rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${((currentFrame + 1) / animation.frames.length) * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
