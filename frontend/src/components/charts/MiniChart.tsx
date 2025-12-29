import React from 'react';
import { AreaChart, Area, ResponsiveContainer, YAxis } from 'recharts';

interface MiniChartProps {
  data: { value: number }[];
  color?: 'green' | 'red' | 'blue';
  height?: number;
  width?: number | string;
}

const colors = {
  green: { stroke: '#238636', fill: '#238636' },
  red: { stroke: '#da3633', fill: '#da3633' },
  blue: { stroke: '#1f6feb', fill: '#1f6feb' },
};

export const MiniChart: React.FC<MiniChartProps> = ({
  data,
  color = 'green',
  height = 40,
  width = '100%',
}) => {
  const { stroke, fill } = colors[color];

  if (!data.length) {
    return <div style={{ height, width }} className="bg-dark-bg-tertiary/30 rounded" />;
  }

  return (
    <ResponsiveContainer width={width} height={height}>
      <AreaChart data={data} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id={`miniGradient-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={fill} stopOpacity={0.3} />
            <stop offset="95%" stopColor={fill} stopOpacity={0} />
          </linearGradient>
        </defs>
        <YAxis domain={['dataMin', 'dataMax']} hide />
        <Area
          type="monotone"
          dataKey="value"
          stroke={stroke}
          strokeWidth={1.5}
          fill={`url(#miniGradient-${color})`}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default MiniChart;
