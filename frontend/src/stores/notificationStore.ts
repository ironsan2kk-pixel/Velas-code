import { create } from 'zustand';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number;
  timestamp: number;
}

interface NotificationState {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => string;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  
  addNotification: (notification) => {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: Date.now(),
      duration: notification.duration ?? 5000,
    };
    
    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));
    
    // Auto-remove after duration
    if (newNotification.duration > 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, newNotification.duration);
    }
    
    return id;
  },
  
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  
  clearAll: () => set({ notifications: [] }),
}));

// Helper functions
export const toast = {
  success: (title: string, message?: string, duration?: number) =>
    useNotificationStore.getState().addNotification({ type: 'success', title, message, duration }),
  
  error: (title: string, message?: string, duration?: number) =>
    useNotificationStore.getState().addNotification({ type: 'error', title, message, duration }),
  
  warning: (title: string, message?: string, duration?: number) =>
    useNotificationStore.getState().addNotification({ type: 'warning', title, message, duration }),
  
  info: (title: string, message?: string, duration?: number) =>
    useNotificationStore.getState().addNotification({ type: 'info', title, message, duration }),
};

export default useNotificationStore;
