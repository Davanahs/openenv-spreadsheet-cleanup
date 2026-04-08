import { useEffect, useRef } from 'react';
import { useStore } from '../store/appStore';

const BASE_DELAY = 1500;   // 1.5s initial reconnect delay
const MAX_DELAY  = 30000;  // cap at 30s

export function useWebSocket(enabled: boolean = false) {
  const addLog = useStore(s => s.addLog);
  const reconnectDelay = useRef(BASE_DELAY);
  const timeoutRef     = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wsRef          = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!enabled) return;

    let cancelled = false;

    const connect = () => {
      if (cancelled) return;

      // Vite injects VITE_* vars; fall back gracefully if not available
      const WS_URL: string =
        (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_WS_URL) ||
        'ws://localhost:8000/ws';
      let ws: WebSocket;

      try {
        ws = new WebSocket(WS_URL);
        wsRef.current = ws;
      } catch {
        scheduleReconnect();
        return;
      }

      ws.onopen = () => {
        reconnectDelay.current = BASE_DELAY; // reset backoff on successful connect
        addLog('🔗 WebSocket connected');
      };

      ws.onmessage = (event) => {
        const text: string = typeof event.data === 'string' ? event.data : '';
        // Try parse JSON first for future structured messages
        try {
          const data = JSON.parse(text);
          if (data.type === 'log') { addLog(`📡 ${data.message}`); return; }
        } catch { /* plain text — fall through */ }

        // Colour-code judge-format logs
        const msg = text.trim();
        if      (msg.startsWith('[START]')) addLog(`🟢 ${msg}`);
        else if (msg.startsWith('[STEP]'))  addLog(`🔵 ${msg}`);
        else if (msg.startsWith('[END]'))   addLog(`🏁 ${msg}`);
        else                                addLog(`📡 ${msg}`);
      };

      ws.onerror = () => { /* suppress noise; onclose handles reconnect */ };

      ws.onclose = () => {
        if (!cancelled) scheduleReconnect();
      };
    };

    const scheduleReconnect = () => {
      if (cancelled) return;
      timeoutRef.current = setTimeout(() => {
        if (!cancelled) {
          reconnectDelay.current = Math.min(reconnectDelay.current * 2, MAX_DELAY);
          connect();
        }
      }, reconnectDelay.current);
    };

    connect();

    return () => {
      cancelled = true;
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, [enabled, addLog]);

  return {};
}
