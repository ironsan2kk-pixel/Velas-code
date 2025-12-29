import { useEffect, useRef, useCallback, useState } from 'react';
import { wsService } from '@/services/websocket';
import type { WSEvent } from '@/types';

interface UseWebSocketOptions {
  channels?: string[];
  autoConnect?: boolean;
  onMessage?: (event: WSEvent) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    channels = ['signals', 'positions', 'system'],
    autoConnect = true,
    onMessage,
    onConnect,
    onDisconnect,
  } = options;

  const [isConnected, setIsConnected] = useState(wsService.isConnected);
  const mountedRef = useRef(true);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  const connect = useCallback(async () => {
    try {
      await wsService.connect(channels);
      if (mountedRef.current) {
        setIsConnected(true);
        onConnect?.();
      }
    } catch (error) {
      console.error('[useWebSocket] Connection failed:', error);
    }
  }, [channels, onConnect]);

  const disconnect = useCallback(() => {
    wsService.disconnect();
    if (mountedRef.current) {
      setIsConnected(false);
      onDisconnect?.();
    }
  }, [onDisconnect]);

  useEffect(() => {
    mountedRef.current = true;

    // Set up message handler
    if (onMessage) {
      unsubscribeRef.current = wsService.onMessage((event) => {
        if (mountedRef.current) {
          onMessage(event);
        }
      });
    }

    // Auto-connect if enabled
    if (autoConnect) {
      connect();
    }

    // Check connection status periodically
    const statusInterval = setInterval(() => {
      if (mountedRef.current) {
        setIsConnected(wsService.isConnected);
      }
    }, 1000);

    return () => {
      mountedRef.current = false;
      clearInterval(statusInterval);
      unsubscribeRef.current?.();
    };
  }, [autoConnect, connect, onMessage]);

  return {
    isConnected,
    connect,
    disconnect,
  };
}

// Hook for subscribing to specific event types
export function useWSEvent<T extends WSEvent['type']>(
  type: T,
  handler: (event: Extract<WSEvent, { type: T }>) => void
): void {
  useEffect(() => {
    const unsubscribe = wsService.on(type, (event) => {
      handler(event as Extract<WSEvent, { type: T }>);
    });
    return unsubscribe;
  }, [type, handler]);
}

export default useWebSocket;
