import React from 'react';

interface PerformanceBarProps {
  value: number;
  maxValue?: number;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const PerformanceBar: React.FC<PerformanceBarProps> = ({
  value,
  maxValue = 10,
  showLabel = true,
  size = 'md',
}) => {
  const isPositive = value >= 0;
  const absValue = Math.abs(value);
  const width = Math.min((absValue / maxValue) * 100, 100);

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  };

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-dark-bg-tertiary rounded-full overflow-hidden">
        <div
          className={`${sizeClasses[size]} rounded-full transition-all duration-300 ${
            isPositive ? 'bg-accent-green' : 'bg-accent-red'
          }`}
          style={{ width: `${width}%` }}
        />
      </div>
      {showLabel && (
        <span
          className={`text-sm font-medium min-w-[50px] text-right ${
            isPositive ? 'text-profit' : 'text-loss'
          }`}
        >
          {isPositive ? '+' : ''}{value.toFixed(1)}%
        </span>
      )}
    </div>
  );
};

export default PerformanceBar;
