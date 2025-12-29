import React, { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

interface EquityPoint {
  timestamp: string;
  equity: number;
  drawdown: number;
}

interface EquityCurveProps {
  data: EquityPoint[];
  height?: number;
  showDrawdown?: boolean;
  showGrid?: boolean;
  animated?: boolean;
}

const formatDate = (timestamp: string) => {
  const date = new Date(timestamp);
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' });
};

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;
  
  return (
    <div className="bg-dark-bg-secondary border border-dark-border rounded-lg p-3 shadow-xl">
      <p className="text-dark-text-muted text-xs mb-2">
        {new Date(data.timestamp).toLocaleDateString('ru-RU', {
          day: '2-digit',
          month: 'long',
          year: 'numeric',
        })}
      </p>
      <div className="space-y-1">
        <div className="flex justify-between gap-4">
          <span className="text-dark-text-secondary text-sm">Баланс:</span>
          <span className="text-dark-text-primary font-medium">
            {formatCurrency(data.equity)}
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-dark-text-secondary text-sm">Просадка:</span>
          <span className={`font-medium ${data.drawdown > 5 ? 'text-loss' : 'text-dark-text-muted'}`}>
            -{data.drawdown.toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  );
};

export const EquityCurve: React.FC<EquityCurveProps> = ({
  data,
  height = 300,
  showDrawdown = false,
  showGrid = true,
  animated = true,
}) => {
  const chartData = useMemo(() => {
    return data.map(point => ({
      ...point,
      displayDate: formatDate(point.timestamp),
    }));
  }, [data]);

  const { minEquity, maxEquity, startEquity } = useMemo(() => {
    if (!data.length) return { minEquity: 0, maxEquity: 0, startEquity: 0 };
    
    const equities = data.map(d => d.equity);
    return {
      minEquity: Math.min(...equities),
      maxEquity: Math.max(...equities),
      startEquity: data[0].equity,
    };
  }, [data]);

  const yDomain = useMemo(() => {
    const padding = (maxEquity - minEquity) * 0.1;
    return [Math.floor(minEquity - padding), Math.ceil(maxEquity + padding)];
  }, [minEquity, maxEquity]);

  if (!data.length) {
    return (
      <div 
        className="flex items-center justify-center text-dark-text-muted"
        style={{ height }}
      >
        Нет данных для отображения
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#238636" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#238636" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#da3633" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#da3633" stopOpacity={0} />
          </linearGradient>
        </defs>
        
        {showGrid && (
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="#30363d" 
            vertical={false}
          />
        )}
        
        <XAxis
          dataKey="displayDate"
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#8b949e', fontSize: 11 }}
          tickMargin={8}
          interval="preserveStartEnd"
        />
        
        <YAxis
          domain={yDomain}
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#8b949e', fontSize: 11 }}
          tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
          width={50}
        />
        
        <Tooltip content={<CustomTooltip />} />
        
        <ReferenceLine
          y={startEquity}
          stroke="#8b949e"
          strokeDasharray="5 5"
          strokeOpacity={0.5}
        />
        
        <Area
          type="monotone"
          dataKey="equity"
          stroke="#238636"
          strokeWidth={2}
          fill="url(#equityGradient)"
          isAnimationActive={animated}
          animationDuration={1000}
        />
        
        {showDrawdown && (
          <Area
            type="monotone"
            dataKey="drawdown"
            stroke="#da3633"
            strokeWidth={1}
            fill="url(#drawdownGradient)"
            isAnimationActive={animated}
            animationDuration={1000}
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default EquityCurve;
