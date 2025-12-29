import React from 'react';
import { cn } from '@/utils';

export type BadgeVariant = 'green' | 'red' | 'blue' | 'yellow' | 'purple' | 'gray';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  dot?: boolean;
}

const variantClasses: Record<BadgeVariant, string> = {
  green: 'badge-green',
  red: 'badge-red',
  blue: 'badge-blue',
  yellow: 'badge-yellow',
  purple: 'badge-purple',
  gray: 'badge-gray',
};

export const Badge: React.FC<BadgeProps> = ({
  variant = 'gray',
  dot = false,
  className,
  children,
  ...props
}) => {
  return (
    <span
      className={cn('badge', variantClasses[variant], className)}
      {...props}
    >
      {dot && (
        <span
          className={cn(
            'w-1.5 h-1.5 rounded-full',
            variant === 'green' && 'bg-accent-green-light',
            variant === 'red' && 'bg-accent-red-light',
            variant === 'blue' && 'bg-accent-blue-light',
            variant === 'yellow' && 'bg-accent-yellow-light',
            variant === 'purple' && 'bg-accent-purple-light',
            variant === 'gray' && 'bg-dark-text-secondary'
          )}
        />
      )}
      {children}
    </span>
  );
};

// Side badge for LONG/SHORT
export type SideBadgeProps = {
  side: 'LONG' | 'SHORT';
  className?: string;
};

export const SideBadge: React.FC<SideBadgeProps> = ({ side, className }) => {
  return (
    <Badge
      variant={side === 'LONG' ? 'green' : 'red'}
      className={cn('font-mono', className)}
    >
      {side}
    </Badge>
  );
};

// Status badge
export type StatusBadgeProps = {
  status: string;
  className?: string;
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className }) => {
  const getVariant = (): BadgeVariant => {
    switch (status.toLowerCase()) {
      case 'online':
      case 'active':
      case 'open':
      case 'filled':
        return 'green';
      case 'offline':
      case 'closed':
      case 'cancelled':
        return 'red';
      case 'degraded':
      case 'warning':
      case 'pending':
        return 'yellow';
      case 'maintenance':
      case 'partial':
        return 'purple';
      default:
        return 'gray';
    }
  };

  return (
    <Badge variant={getVariant()} dot className={className}>
      {status}
    </Badge>
  );
};

export default Badge;
