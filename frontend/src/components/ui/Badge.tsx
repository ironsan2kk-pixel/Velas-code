/**
 * VELAS UI - Badge Component
 */

import React from 'react';
import { cn } from '@/utils/cn';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'danger' | 'warning' | 'info' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className,
}) => {
  const variantClasses = {
    default: 'bg-dark-bg-tertiary text-dark-text-primary border-dark-border',
    success: 'bg-accent-green/10 text-accent-green border-accent-green/20',
    danger: 'bg-accent-red/10 text-accent-red border-accent-red/20',
    warning: 'bg-accent-yellow/10 text-accent-yellow border-accent-yellow/20',
    info: 'bg-accent-blue/10 text-accent-blue border-accent-blue/20',
    secondary: 'bg-dark-bg-secondary text-dark-text-secondary border-dark-border',
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium border rounded-md',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {children}
    </span>
  );
};
