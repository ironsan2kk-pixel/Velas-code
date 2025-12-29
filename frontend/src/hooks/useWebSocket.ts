/**
 * VELAS Trading System - WebSocket Hook
 * Real-time updates через WebSocket
 * 
 * NOTE: Auto-connect disabled until WebSocket endpoint is implemented in API
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from './useApi';
import type { WebSocketMessage, WebSocketSubscription } from '@/types';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/ws';
const RECONNECT_DELAY = 5000;
const MAX_RECONNECT_ATTEMPTS = 3;

// TEMPORARY: Disable WebSocket until API endpoint is ready
const WS_ENABLED = false;

interface UseWebSocketOptions {
  channels?: ('signals' | 'positions' | 'system')[];
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onClose?: (event: CloseEvent) => void;
  autoReconnect?: boolean;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    channels = ['signals', 'positions', 'system'],
    onMessage,
    onError,
    onClose,
    autoReconnect = true,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const queryClient = useQueryClient();

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      if (onMessage) onMessage(message);

      switch (message.type) {
        case 'signal_new':
          queryClient.invalidateQueries({ queryKey: queryKeys.signals() });
          queryClient.invalidateQueries({ queryKey: queryKeys.dashboardSummary });
          break;
        case 'position_opened':
        case 'position_updated':
        case 'position_closed':
          queryClient.invalidateQueries({ queryKey: queryKeys.positions() });
          queryClient.invalidateQueries({ queryKey: queryKeys.dashboardSummary });
          break;
        case 'system_status':
          queryClient.invalidateQueries({ queryKey: queryKeys.systemStatus });
          break;
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }, [onMessage, queryClient]);

  const subscribe = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'subscribe', channels }));
    }
  }, [channels]);

  const connect = useCallback(() => {
    if (!WS_ENABLED) {
      console.log('WebSocket disabled - API endpoint not ready');
      return;
    }
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionStatus('connecting');
    
    try {
      const ws = new WebSocket(WS_URL);
      
      ws.onopen = () => {
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        subscribe();
      };

      ws.onmessage = handleMessage;

      ws.onerror = (error) => {
        setConnectionStatus('error');
        if (onError) onError(error);
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        setConnectionStatus('disconnected');
        wsRef.current = null;
        if (onClose) onClose(event);

        if (autoReconnect && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current += 1;
          reconnectTimeoutRef.current = setTimeout(connect, RECONNECT_DELAY);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      setConnectionStatus('error');
    }
  }, [autoReconnect, handleMessage, onClose, onError, subscribe]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  useEffect(() => {
    // DISABLED: Don't auto-connect until API is ready
    return () => disconnect();
  }, [disconnect]);

  return { isConnected, connectionStatus, connect, disconnect, sendMessage };
};

export const useWSEvent = (eventType: string, callback: (data: any) => void) => {
  const { isConnected } = useWebSocket({
    onMessage: (message) => {
      if (message.type === eventType) callback(message.data);
    },
  });
  return { isConnected };
};

export default useWebSocket;
