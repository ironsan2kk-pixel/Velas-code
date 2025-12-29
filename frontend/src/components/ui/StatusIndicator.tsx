import React from 'react';
import { cn } from '@/utils';

export type StatusType = 'online' | 'offline' | 'warning' | 'info';

export interface StatusIndicatorProps {
  status: StatusType;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  pulse?: boolean;
  className?: string;
}

const sizeClasses = {
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
  lg: 'w-2.5 h-2.5',
};

const statusClasses: Record<StatusType, string> = {
  online: 'bg-accent-green',
  offline: 'bg-accent-red',
  warning: 'bg-accent-yellow',
  info: 'bg-accent-blue',
};

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  size = 'md',
  pulse = true,
  className,
}) => {
  const shouldPulse = pulse && (status === 'online' || status === 'warning');

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span
        className={cn(
          'rounded-full',
          sizeClasses[size],
          statusClasses[status],
          shouldPulse && 'animate-pulse-slow'
        )}
      />
      {label && (
        <span className="text-sm text-dark-text-secondary">{label}</span>
      )}
    </div>
  );
};

// System status with icon
export interface SystemStatusProps {
  status: 'online' | 'offline' | 'degraded' | 'maintenance';
  className?: string;
}

export const SystemStatus: React.FC<SystemStatusProps> = ({ status, className }) => {
  const getLabel = () => {
    switch (status) {
      case 'online':
        return 'Онлайн';
      case 'offline':
        return 'Оффлайн';
      case 'degraded':
        return 'Деградация';
      case 'maintenance':
        return 'Обслуживание';
    }
  };

  const getStatusType = (): StatusType => {
    switch (status) {
      case 'online':
        return 'online';
      case 'offline':
        return 'offline';
      case 'degraded':
      case 'maintenance':
        return 'warning';
    }
  };

  return (
    <StatusIndicator
      status={getStatusType()}
      label={getLabel()}
      className={className}
    />
  );
};

export default StatusIndicator;
