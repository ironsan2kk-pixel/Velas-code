import React from 'react';
import { cn } from '@/utils';
import { useNotificationStore, type Notification, type NotificationType } from '@/stores';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  X,
} from 'lucide-react';

// Icons for each notification type
const icons: Record<NotificationType, React.ReactNode> = {
  success: <CheckCircle className="w-5 h-5 text-accent-green-light" />,
  error: <XCircle className="w-5 h-5 text-accent-red-light" />,
  warning: <AlertTriangle className="w-5 h-5 text-accent-yellow-light" />,
  info: <Info className="w-5 h-5 text-accent-blue-light" />,
};

// Background colors for each type
const bgColors: Record<NotificationType, string> = {
  success: 'bg-accent-green/10 border-accent-green/30',
  error: 'bg-accent-red/10 border-accent-red/30',
  warning: 'bg-accent-yellow/10 border-accent-yellow/30',
  info: 'bg-accent-blue/10 border-accent-blue/30',
};

// Single toast item
interface ToastItemProps {
  notification: Notification;
  onClose: () => void;
}

const ToastItem: React.FC<ToastItemProps> = ({ notification, onClose }) => {
  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border shadow-lg animate-slide-in-right',
        'bg-dark-bg-card',
        bgColors[notification.type]
      )}
      role="alert"
    >
      <div className="flex-shrink-0">{icons[notification.type]}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-dark-text-primary">
          {notification.title}
        </p>
        {notification.message && (
          <p className="mt-1 text-sm text-dark-text-secondary">
            {notification.message}
          </p>
        )}
      </div>
      <button
        onClick={onClose}
        className="flex-shrink-0 p-1 rounded hover:bg-dark-bg-tertiary transition-colors"
        aria-label="Закрыть"
      >
        <X className="w-4 h-4 text-dark-text-muted" />
      </button>
    </div>
  );
};

// Toast container
export const ToastContainer: React.FC = () => {
  const { notifications, removeNotification } = useNotificationStore();

  if (notifications.length === 0) return null;

  return (
    <div
      className={cn(
        'fixed z-50 flex flex-col gap-2',
        'bottom-4 right-4 left-4 sm:left-auto sm:w-96'
      )}
    >
      {notifications.map((notification) => (
        <ToastItem
          key={notification.id}
          notification={notification}
          onClose={() => removeNotification(notification.id)}
        />
      ))}
    </div>
  );
};

export default ToastContainer;
