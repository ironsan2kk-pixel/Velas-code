import type { WSEvent } from '@/types';

type WSEventHandler = (event: WSEvent) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private reconnectDelay: number = 1000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private handlers: Map<string, Set<WSEventHandler>> = new Map();
  private globalHandlers: Set<WSEventHandler> = new Set();
  private isManualClose: boolean = false;
  private subscribedChannels: string[] = [];

  constructor(url?: string) {
    this.url = url || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;
  }

  connect(channels: string[] = ['signals', 'positions', 'system']): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.isManualClose = false;
      this.subscribedChannels = channels;

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('[WS] Connected');
          this.reconnectAttempts = 0;
          
          // Subscribe to channels
          this.send({
            type: 'subscribe',
            channels: this.subscribedChannels,
          });

          // Start ping interval
          this.startPing();
          
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data) as WSEvent;
            this.handleMessage(message);
          } catch (err) {
            console.error('[WS] Failed to parse message:', err);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WS] Error:', error);
        };

        this.ws.onclose = (event) => {
          console.log('[WS] Disconnected:', event.code, event.reason);
          this.stopPing();
          
          if (!this.isManualClose) {
            this.attemptReconnect();
          }
        };

      } catch (error) {
        console.error('[WS] Connection error:', error);
        reject(error);
      }
    });
  }

  disconnect(): void {
    this.isManualClose = true;
    this.stopPing();
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WS] Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect(this.subscribedChannels);
    }, delay);
  }

  private startPing(): void {
    this.pingTimer = setInterval(() => {
      this.send({ type: 'ping' });
    }, 30000);
  }

  private stopPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  private send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private handleMessage(message: WSEvent): void {
    // Call global handlers
    this.globalHandlers.forEach((handler) => {
      try {
        handler(message);
      } catch (err) {
        console.error('[WS] Handler error:', err);
      }
    });

    // Call type-specific handlers
    const typeHandlers = this.handlers.get(message.type);
    if (typeHandlers) {
      typeHandlers.forEach((handler) => {
        try {
          handler(message);
        } catch (err) {
          console.error('[WS] Handler error:', err);
        }
      });
    }
  }

  // Subscribe to all messages
  onMessage(handler: WSEventHandler): () => void {
    this.globalHandlers.add(handler);
    return () => this.globalHandlers.delete(handler);
  }

  // Subscribe to specific message type
  on(type: string, handler: WSEventHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);
    return () => this.handlers.get(type)?.delete(handler);
  }

  // Get connection state
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  get state(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}

// Singleton instance
export const wsService = new WebSocketService();

export default wsService;
