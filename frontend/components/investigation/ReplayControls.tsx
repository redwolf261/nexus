import { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipForward, SkipBack, Rewind, FastForward } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function ReplayControls({ caseId, onReplayEvent }: { caseId: string, onReplayEvent: (event: any) => void }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [currentIndex, setCurrentIndex] = useState(0);
  
  // Fetch historical event stream
  const { data: events, isLoading } = useQuery({
    queryKey: ['events', caseId],
    queryFn: async () => {
        const res = await api.get(`/api/events?case_id=${caseId}`);
        return res.data;
    }
  });

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const stepForward = () => {
      if (events && currentIndex < events.length) {
          onReplayEvent(events[currentIndex]);
          setCurrentIndex(prev => prev + 1);
      } else {
          setIsPlaying(false);
      }
  };

  const stepBack = () => {
     // Replay mode backwards implies rebuilding state from 0 to currentIndex - 1
     // For simplicity in this UI, we just decrement index and rely on consumer to handle state rebuild if they want to.
     if (currentIndex > 0) {
         setCurrentIndex(prev => prev - 1);
     }
  };

  useEffect(() => {
    if (isPlaying) {
      const interval = 1000 / speed;
      timerRef.current = setInterval(stepForward, interval);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, currentIndex, speed, events]);

  if (isLoading) return <div className="text-xs font-mono text-muted-foreground">LOADING REPLAY...</div>;
  if (!events || events.length === 0) return <div className="text-xs font-mono text-muted-foreground">NO EVENTS TO REPLAY</div>;

  return (
    <div className="flex items-center gap-2 bg-card border border-border rounded-lg p-2 font-mono text-xs shadow-sm">
      <div className="text-primary font-bold mr-2">REPLAY: {currentIndex}/{events.length}</div>
      <button onClick={stepBack} className="p-1 hover:bg-muted rounded"><SkipBack className="w-4 h-4"/></button>
      <button onClick={() => setIsPlaying(!isPlaying)} className="p-1 hover:bg-muted rounded text-primary">
        {isPlaying ? <Pause className="w-4 h-4 fill-current"/> : <Play className="w-4 h-4 fill-current"/>}
      </button>
      <button onClick={stepForward} className="p-1 hover:bg-muted rounded"><SkipForward className="w-4 h-4"/></button>
      
      <div className="h-4 w-px bg-border mx-2"></div>
      
      <button onClick={() => setSpeed(1)} className={`px-2 py-1 rounded ${speed === 1 ? 'bg-primary/20 text-primary' : 'hover:bg-muted'}`}>1x</button>
      <button onClick={() => setSpeed(2)} className={`px-2 py-1 rounded ${speed === 2 ? 'bg-primary/20 text-primary' : 'hover:bg-muted'}`}>2x</button>
      <button onClick={() => setSpeed(5)} className={`px-2 py-1 rounded ${speed === 5 ? 'bg-primary/20 text-primary' : 'hover:bg-muted'}`}>5x</button>
    </div>
  );
}
