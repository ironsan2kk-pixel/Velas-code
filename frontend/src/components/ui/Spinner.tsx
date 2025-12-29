import React from 'react';
import { cn } from '@/utils';
import { Loader2 } from 'lucide-react';

// ===== Spinner =====

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const spinnerSizes = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
  xl: 'w-12 h-12',
};

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className }) => {
  return (
    <Loader2
      className={cn(
        'animate-spin text-accent-blue',
        spinnerSizes[size],
        className
      )}
    />
  );
};

// Full page loading spinner
export const PageSpinner: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-screen-minus-header">
      <div className="flex flex-col items-center gap-3">
        <Spinner size="xl" />
        <p className="text-dark-text-secondary">Загрузка...</p>
      </div>
    </div>
  );
};

// ===== Skeleton =====

export interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className,
  variant = 'rectangular',
  width,
  height,
}) => {
  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  return (
    <div
      className={cn(
        'skeleton',
        variant === 'text' && 'h-4 rounded',
        variant === 'circular' && 'rounded-full',
        variant === 'rectangular' && 'rounded-md',
        className
      )}
      style={style}
    />
  );
};

// Skeleton text lines
export interface SkeletonTextProps {
  lines?: number;
  className?: string;
}

export const SkeletonText: React.FC<SkeletonTextProps> = ({
  lines = 3,
  className,
}) => {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          className={cn(
            'h-4',
            i === lines - 1 && 'w-3/4' // Last line is shorter
          )}
        />
      ))}
    </div>
  );
};

// Skeleton card
export const SkeletonCard: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div className={cn('card', className)}>
      <div className="flex items-center gap-4 mb-4">
        <Skeleton variant="circular" width={40} height={40} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" className="w-1/3" />
          <Skeleton variant="text" className="w-1/2" />
        </div>
      </div>
      <SkeletonText lines={2} />
    </div>
  );
};

// Skeleton table row
export const SkeletonTableRow: React.FC<{ columns?: number }> = ({
  columns = 5,
}) => {
  return (
    <tr>
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton variant="text" className="h-4" />
        </td>
      ))}
    </tr>
  );
};

export default Spinner;
