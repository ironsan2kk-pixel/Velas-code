import React from 'react';

interface TPLevel {
  level: number;
  price: number;
  percent: number;
  hit: boolean;
}

interface PositionProgressProps {
  side: 'LONG' | 'SHORT';
  entryPrice: number;
  currentPrice: number;
  slPrice: number;
  tpLevels: TPLevel[];
  compact?: boolean;
}

export const PositionProgress: React.FC<PositionProgressProps> = ({
  side,
  entryPrice,
  currentPrice,
  slPrice,
  tpLevels,
  compact = false,
}) => {
  // Calculate progress percentage (0-100 where 50 is entry)
  const isLong = side === 'LONG';
  
  // Range from SL to TP6
  const tp6 = tpLevels[5]?.price || entryPrice * (isLong ? 1.14 : 0.86);
  const range = Math.abs(tp6 - slPrice);
  
  // Current position in range
  const currentPos = isLong
    ? ((currentPrice - slPrice) / range) * 100
    : ((slPrice - currentPrice) / range) * 100;
  
  const entryPos = isLong
    ? ((entryPrice - slPrice) / range) * 100
    : ((slPrice - entryPrice) / range) * 100;

  const clampedPos = Math.max(0, Math.min(100, currentPos));
  const isProfit = isLong ? currentPrice > entryPrice : currentPrice < entryPrice;

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        {/* TP indicators */}
        <div className="flex gap-0.5">
          {tpLevels.map((tp) => (
            <div
              key={tp.level}
              className={`w-4 h-4 rounded text-[10px] flex items-center justify-center font-medium ${
                tp.hit
                  ? 'bg-accent-green text-white'
                  : 'bg-dark-bg-tertiary text-dark-text-muted'
              }`}
            >
              {tp.level}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Progress bar */}
      <div className="relative h-8 bg-dark-bg-tertiary rounded-lg overflow-hidden">
        {/* SL zone */}
        <div 
          className="absolute left-0 top-0 h-full bg-loss/20"
          style={{ width: `${entryPos}%` }}
        />
        
        {/* Profit zone */}
        <div 
          className="absolute top-0 h-full bg-profit/20"
          style={{ left: `${entryPos}%`, width: `${100 - entryPos}%` }}
        />
        
        {/* Entry line */}
        <div 
          className="absolute top-0 h-full w-0.5 bg-dark-text-secondary"
          style={{ left: `${entryPos}%` }}
        />
        
        {/* TP markers */}
        {tpLevels.map((tp) => {
          const tpPos = isLong
            ? ((tp.price - slPrice) / range) * 100
            : ((slPrice - tp.price) / range) * 100;
          
          return (
            <div
              key={tp.level}
              className={`absolute top-1 w-4 h-6 -ml-2 rounded text-[10px] flex items-center justify-center font-medium transition-all ${
                tp.hit
                  ? 'bg-accent-green text-white'
                  : 'bg-dark-border text-dark-text-muted'
              }`}
              style={{ left: `${tpPos}%` }}
            >
              {tp.level}
            </div>
          );
        })}
        
        {/* Current price indicator */}
        <div 
          className={`absolute top-0 h-full w-1 ${isProfit ? 'bg-accent-green' : 'bg-accent-red'} transition-all duration-300`}
          style={{ left: `${clampedPos}%`, transform: 'translateX(-50%)' }}
        />
      </div>
      
      {/* Labels */}
      <div className="flex justify-between text-xs text-dark-text-muted">
        <span className="text-loss">SL: {slPrice.toFixed(2)}</span>
        <span>Entry: {entryPrice.toFixed(2)}</span>
        <span className="text-profit">TP6: {tp6.toFixed(2)}</span>
      </div>
    </div>
  );
};

export default PositionProgress;
