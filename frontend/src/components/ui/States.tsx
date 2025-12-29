import React from 'react';
import { cn } from '@/utils';
import { Button } from './Button';
import {
  Inbox,
  AlertCircle,
  RefreshCw,
  WifiOff,
  FileQuestion,
} from 'lucide-react';

// ===== Empty State =====

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 px-4 text-center',
        className
      )}
    >
      <div className="w-12 h-12 rounded-full bg-dark-bg-tertiary flex items-center justify-center mb-4">
        {icon || <Inbox className="w-6 h-6 text-dark-text-muted" />}
      </div>
      <h3 className="text-lg font-medium text-dark-text-primary mb-1">
        {title}
      </h3>
      {description && (
        <p className="text-sm text-dark-text-secondary max-w-sm mb-4">
          {description}
        </p>
      )}
      {action && (
        <Button variant="secondary" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
};

// ===== Error State =====

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Произошла ошибка',
  message = 'Не удалось загрузить данные. Попробуйте еще раз.',
  onRetry,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 px-4 text-center',
        className
      )}
    >
      <div className="w-12 h-12 rounded-full bg-accent-red/10 flex items-center justify-center mb-4">
        <AlertCircle className="w-6 h-6 text-accent-red-light" />
      </div>
      <h3 className="text-lg font-medium text-dark-text-primary mb-1">
        {title}
      </h3>
      <p className="text-sm text-dark-text-secondary max-w-sm mb-4">
        {message}
      </p>
      {onRetry && (
        <Button
          variant="secondary"
          onClick={onRetry}
          leftIcon={<RefreshCw className="w-4 h-4" />}
        >
          Повторить
        </Button>
      )}
    </div>
  );
};

// ===== Connection Lost State =====

export interface ConnectionLostProps {
  onReconnect?: () => void;
  className?: string;
}

export const ConnectionLost: React.FC<ConnectionLostProps> = ({
  onReconnect,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 px-4 text-center',
        className
      )}
    >
      <div className="w-12 h-12 rounded-full bg-accent-yellow/10 flex items-center justify-center mb-4">
        <WifiOff className="w-6 h-6 text-accent-yellow-light" />
      </div>
      <h3 className="text-lg font-medium text-dark-text-primary mb-1">
        Соединение потеряно
      </h3>
      <p className="text-sm text-dark-text-secondary max-w-sm mb-4">
        Проверьте подключение к интернету и попробуйте снова
      </p>
      {onReconnect && (
        <Button
          variant="secondary"
          onClick={onReconnect}
          leftIcon={<RefreshCw className="w-4 h-4" />}
        >
          Переподключиться
        </Button>
      )}
    </div>
  );
};

// ===== Not Found State =====

export interface NotFoundProps {
  title?: string;
  message?: string;
  className?: string;
}

export const NotFound: React.FC<NotFoundProps> = ({
  title = 'Не найдено',
  message = 'Запрашиваемая страница или ресурс не существует',
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 px-4 text-center',
        className
      )}
    >
      <div className="w-12 h-12 rounded-full bg-dark-bg-tertiary flex items-center justify-center mb-4">
        <FileQuestion className="w-6 h-6 text-dark-text-muted" />
      </div>
      <h3 className="text-lg font-medium text-dark-text-primary mb-1">
        {title}
      </h3>
      <p className="text-sm text-dark-text-secondary max-w-sm">
        {message}
      </p>
    </div>
  );
};

export default EmptyState;
