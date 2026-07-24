import { useEffect, useRef, useState, useCallback } from 'react';

export function useWebSocket(channel: string) {
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const processedEvents = useRef<Set<string>>(new Set());

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
    const port = 8000;
    const wsUrl = `${protocol}//${host}:${port}/ws/${channel}`;

    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log(`[WS] Connected to channel: ${channel}`);
      setIsConnected(true);
      reconnectAttempts.current = 0;
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Deduplicate events if event_id is present
        if (data.event_id) {
          if (processedEvents.current.has(data.event_id)) {
            console.log(`[WS] Ignored duplicate event: ${data.event_id}`);
            return;
          }
          processedEvents.current.add(data.event_id);
          
          // Keep set bounded to last 1000 events
          if (processedEvents.current.size > 1000) {
            const iterator = processedEvents.current.values();
            const first = iterator.next().value;
            if (first) {
              processedEvents.current.delete(first);
            }
          }
        }
        
        setLastMessage(data);
      } catch (err) {
        console.error("[WS] Failed to parse message", err);
      }
    };

    socket.onclose = (event) => {
      console.log(`[WS] Disconnected from channel: ${channel}`);
      setIsConnected(false);
      ws.current = null;

      // Exponential backoff reconnect
      if (reconnectAttempts.current < maxReconnectAttempts) {
        const timeout = Math.pow(2, reconnectAttempts.current) * 1000;
        reconnectAttempts.current += 1;
        console.log(`[WS] Reconnecting in ${timeout}ms...`);
        setTimeout(connect, timeout);
      }
    };

    socket.onerror = (err) => {
      console.error(`[WS] Error on channel ${channel}`, err);
    };

    ws.current = socket;
  }, [channel]);

  useEffect(() => {
    connect();
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  return {
    lastMessage,
    isConnected,
    sendMessage: (msg: any) => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify(msg));
      }
    }
  };
}
