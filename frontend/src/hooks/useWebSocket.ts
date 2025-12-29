/**
 * VELAS Trading System - WebSocket Hook
 * Real-time updates через WebSocket
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from './useApi';
import type { WebSocketMessage, WebSocketSubscription } from '@/types';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
const RECONNECT_DELAY = 3000; // 3 секунды
const MAX_RECONNECT_ATTEMPTS = 10;

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

  /**
   * Обработка входящих сообщений
   */
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      // Вызываем пользовательский обработчик
      if (onMessage) {
        onMessage(message);
      }

      // Автоматическое обновление кэша React Query
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
          queryClient.invalidateQueries({ queryKey: queryKeys.dashboardMetrics });
          break;
          
        case 'tp_hit':
        case 'sl_hit':
          queryClient.invalidateQueries({ queryKey: queryKeys.positions() });
          queryClient.invalidateQueries({ queryKey: queryKeys.dashboardSummary });
          queryClient.invalidateQueries({ queryKey: queryKeys.history() });
          break;
          
        case 'system_status':
          queryClient.invalidateQueries({ queryKey: queryKeys.systemStatus });
          break;
          
        case 'error':
          console.error('WebSocket message error:', message.data);
          break;
          
        case 'subscribed':
          console.log('Subscribed to channels:', message.data);
          break;
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }, [onMessage, queryClient]);

  /**
   * Подписка на каналы
   */
  const subscribe = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const subscription: WebSocketSubscription = {
        type: 'subscribe',
        channels,
      };
      wsRef.current.send(JSON.stringify(subscription));
    }
  }, [channels]);

  /**
   * Подключение к WebSocket
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Уже подключены
    }

    setConnectionStatus('connecting');
    
    try {
      const ws = new WebSocket(WS_URL);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        
        // Подписываемся на каналы
        subscribe();
      };

      ws.onmessage = handleMessage;

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
        if (onError) {
          onError(error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        wsRef.current = null;
        
        if (onClose) {
          onClose(event);
        }

        // Автоматическое переподключение
        if (autoReconnect && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current += 1;
          console.log(`Reconnecting... (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, RECONNECT_DELAY);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionStatus('error');
    }
  }, [autoReconnect, handleMessage, onClose, onError, subscribe]);

  /**
   * Отключение от WebSocket
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  /**
   * Отправка сообщения
   */
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
    }
  }, []);

  /**
   * Подключение при монтировании
   */
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    connectionStatus,
    connect,
    disconnect,
    sendMessage,
  };
};

export default useWebSocket;
