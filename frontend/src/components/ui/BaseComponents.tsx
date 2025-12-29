/**
 * VELAS UI - Button Component
 */

import React from 'react';
import { cn } from '@/utils/cn';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
  className?: string;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  className,
  disabled,
  ...props
}) => {
  const variantClasses = {
    primary: 'bg-accent-blue hover:bg-accent-blue/90 text-white',
    secondary: 'bg-dark-bg-tertiary hover:bg-dark-bg-hover text-dark-text-primary border border-dark-border',
    success: 'bg-accent-green hover:bg-accent-green/90 text-white',
    danger: 'bg-accent-red hover:bg-accent-red/90 text-white',
    ghost: 'hover:bg-dark-bg-hover text-dark-text-primary',
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-accent-blue/50',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Spinner size="sm" />}
      {!loading && icon}
      {children}
    </button>
  );
};


/**
 * VELAS UI - Spinner Component
 */

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className }) => {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-2',
    lg: 'w-8 h-8 border-3',
  };

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-accent-blue border-t-transparent',
        sizeClasses[size],
        className
      )}
    />
  );
};


/**
 * VELAS UI - StatusIndicator Component
 */

interface StatusIndicatorProps {
  status: 'online' | 'offline' | 'warning' | 'error';
  label?: string;
  pulse?: boolean;
  className?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  pulse = false,
  className,
}) => {
  const statusColors = {
    online: 'bg-accent-green',
    offline: 'bg-gray-500',
    warning: 'bg-accent-yellow',
    error: 'bg-accent-red',
  };

  return (
    <div className={cn('inline-flex items-center gap-2', className)}>
      <div className="relative">
        <div className={cn('w-2 h-2 rounded-full', statusColors[status])} />
        {pulse && (
          <div
            className={cn(
              'absolute inset-0 w-2 h-2 rounded-full animate-ping opacity-75',
              statusColors[status]
            )}
          />
        )}
      </div>
      {label && <span className="text-sm font-medium text-dark-text-primary">{label}</span>}
    </div>
  );
};


/**
 * VELAS UI - Input Component
 */

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, icon, className, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-dark-text-primary mb-1.5">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-text-muted">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            className={cn(
              'w-full px-3 py-2 bg-dark-bg-tertiary border border-dark-border rounded-lg',
              'text-dark-text-primary placeholder:text-dark-text-muted',
              'focus:outline-none focus:ring-2 focus:ring-accent-blue/50 focus:border-accent-blue',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'transition-colors',
              error && 'border-accent-red focus:ring-accent-red/50 focus:border-accent-red',
              icon && 'pl-10',
              className
            )}
            {...props}
          />
        </div>
        {error && <p className="text-sm text-accent-red mt-1">{error}</p>}
        {helperText && !error && (
          <p className="text-sm text-dark-text-muted mt-1">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';


/**
 * VELAS UI - Select Component
 */

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options: { value: string | number; label: string }[];
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, helperText, options, className, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-dark-text-primary mb-1.5">
            {label}
          </label>
        )}
        <select
          ref={ref}
          className={cn(
            'w-full px-3 py-2 bg-dark-bg-tertiary border border-dark-border rounded-lg',
            'text-dark-text-primary',
            'focus:outline-none focus:ring-2 focus:ring-accent-blue/50 focus:border-accent-blue',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'transition-colors',
            error && 'border-accent-red focus:ring-accent-red/50 focus:border-accent-red',
            className
          )}
          {...props}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {error && <p className="text-sm text-accent-red mt-1">{error}</p>}
        {helperText && !error && (
          <p className="text-sm text-dark-text-muted mt-1">{helperText}</p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';
