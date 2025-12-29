/**
 * VELAS - Analytics Page
 * Страница с детальной аналитикой и графиками
 */

import React, { useState } from 'react';
import { Card, CardHeader, CardContent, Badge, Spinner, Select } from '@/components/ui';
import { EquityCurve } from '@/components/charts';
import {
  useAnalyticsEquity,
  useAnalyticsDrawdown,
  useAnalyticsMonthly,
  useAnalyticsPairs,
  useAnalyticsCorrelation,
} from '@/hooks/useApi';
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Activity,
  AlertTriangle,
  Grid3x3,
} from 'lucide-react';

type PeriodOption = 'all' | '1y' | '6m' | '3m' | '1m';

const periodLabels: Record<PeriodOption, string> = {
  all: 'Всё время',
  '1y': '1 год',
  '6m': '6 месяцев',
  '3m': '3 месяца',
  '1m': '1 месяц',
};

const Analytics: React.FC = () => {
  const [equityPeriod, setEquityPeriod] = useState<PeriodOption>('3m');
  const [drawdownPeriod, setDrawdownPeriod] = useState<PeriodOption>('3m');

  const { data: equityResp, isLoading: equityLoading } = useAnalyticsEquity(equityPeriod);
  const { data: drawdownResp, isLoading: drawdownLoading } = useAnalyticsDrawdown(drawdownPeriod);
  const { data: monthlyResp, isLoading: monthlyLoading } = useAnalyticsMonthly();
  const { data: pairsResp, isLoading: pairsLoading } = useAnalyticsPairs();
  const { data: correlationResp, isLoading: correlationLoading } = useAnalyticsCorrelation();

  // Извлекаем данные из API response
  const equityData = equityResp?.data || [];
  const drawdownData = drawdownResp?.data || [];
  const monthlyData = monthlyResp?.data || [];
  const pairsData = pairsResp?.data || [];
  const correlationData = correlationResp?.data;

  // Сортированные пары по P&L
  const sortedPairs = pairsData ? [...pairsData].sort((a, b) => b.pnl_percent - a.pnl_percent) : [];
  const topPairs = sortedPairs.slice(0, 10);

  // Последние 6 месяцев
  const recentMonths = monthlyData?.slice(-6) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-dark-text-primary">Аналитика</h1>
        <p className="text-dark-text-secondary mt-1">
          Детальная статистика и анализ торговых результатов
        </p>
      </div>

      {/* Equity Curve */}
      <Card>
        <CardHeader
          title="Кривая доходности"
          subtitle="Динамика капитала"
          action={
            <Select
              value={equityPeriod}
              onChange={(e) => setEquityPeriod(e.target.value as PeriodOption)}
              options={Object.entries(periodLabels).map(([value, label]) => ({ value, label }))}
              className="w-40"
            />
          }
        />
        <CardContent>
          {equityLoading ? (
            <div className="h-80 flex items-center justify-center">
              <Spinner />
            </div>
          ) : equityData && equityData.length > 0 ? (
            <EquityCurve data={equityData} height={320} showGrid animated />
          ) : (
            <div className="h-80 flex items-center justify-center text-dark-text-muted">
              <div className="text-center">
                <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>Нет данных за выбранный период</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Drawdown Chart */}
      <Card>
        <CardHeader
          title="График просадок"
          subtitle="Максимальные просадки по времени"
          action={
            <Select
              value={drawdownPeriod}
              onChange={(e) => setDrawdownPeriod(e.target.value as PeriodOption)}
              options={Object.entries(periodLabels).map(([value, label]) => ({ value, label }))}
              className="w-40"
            />
          }
        />
        <CardContent>
          {drawdownLoading ? (
            <div className="h-64 flex items-center justify-center">
              <Spinner />
            </div>
          ) : drawdownData && drawdownData.length > 0 ? (
            <div className="h-64">
              {/* Используем простой bar chart для drawdown */}
              <div className="relative h-full flex items-end gap-1">
                {drawdownData.map((point, idx) => {
                  const height = Math.abs(point.drawdown);
                  return (
                    <div
                      key={idx}
                      className="flex-1 bg-accent-red/60 rounded-t"
                      style={{ height: `${height}%` }}
                      title={`${new Date(point.timestamp).toLocaleDateString()}: -${height.toFixed(2)}%`}
                    />
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-dark-text-muted">
              <div className="text-center">
                <AlertTriangle className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>Нет данных о просадках</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Monthly Stats & Pairs Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Statistics */}
        <Card>
          <CardHeader title="Статистика по месяцам" subtitle="Последние 6 месяцев" />
          <CardContent>
            {monthlyLoading ? (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            ) : recentMonths.length > 0 ? (
              <div className="space-y-3">
                {recentMonths.map((month) => (
                  <div
                    key={month.month}
                    className="flex items-center justify-between p-3 rounded-lg bg-dark-bg-tertiary"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-dark-text-primary">
                          {new Date(month.month + '-01').toLocaleDateString('ru-RU', {
                            month: 'long',
                            year: 'numeric',
                          })}
                        </span>
                        <Badge
                          variant={month.pnl_percent >= 0 ? 'success' : 'danger'}
                          size="sm"
                        >
                          {month.pnl_percent >= 0 ? '+' : ''}
                          {month.pnl_percent.toFixed(2)}%
                        </Badge>
                      </div>
                      <div className="text-sm text-dark-text-muted mt-1">
                        <span>Сделок: {month.trades}</span>
                        <span className="mx-2">•</span>
                        <span>WR: {month.win_rate.toFixed(1)}%</span>
                        <span className="mx-2">•</span>
                        <span>Sharpe: {month.sharpe_ratio.toFixed(2)}</span>
                      </div>
                    </div>
                    <div className={`text-2xl font-bold ${
                      month.pnl_percent >= 0 ? 'text-profit' : 'text-loss'
                    }`}>
                      {month.pnl_percent >= 0 ? (
                        <TrendingUp className="w-6 h-6" />
                      ) : (
                        <TrendingDown className="w-6 h-6" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-dark-text-muted">
                <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>Нет месячной статистики</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Pairs Performance */}
        <Card>
          <CardHeader title="Производительность пар" subtitle="Топ 10 по доходности" />
          <CardContent>
            {pairsLoading ? (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            ) : topPairs.length > 0 ? (
              <div className="space-y-2">
                {topPairs.map((pair) => (
                  <div
                    key={pair.symbol}
                    className="flex items-center justify-between py-2 border-b border-dark-border last:border-0"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-medium text-dark-text-primary w-24">
                        {pair.symbol}
                      </span>
                      <div className="text-sm text-dark-text-muted">
                        <span>{pair.trades} сделок</span>
                        <span className="mx-2">•</span>
                        <span>WR: {pair.win_rate.toFixed(1)}%</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-32 h-2 bg-dark-bg-tertiary rounded overflow-hidden">
                        <div
                          className={`h-full ${pair.pnl_percent >= 0 ? 'bg-accent-green' : 'bg-accent-red'}`}
                          style={{ width: `${Math.min(Math.abs(pair.pnl_percent) * 10, 100)}%` }}
                        />
                      </div>
                      <span className={`font-medium w-20 text-right ${
                        pair.pnl_percent >= 0 ? 'text-profit' : 'text-loss'
                      }`}>
                        {pair.pnl_percent >= 0 ? '+' : ''}
                        {pair.pnl_percent.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-dark-text-muted">
                <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>Нет данных по парам</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Correlation Matrix */}
      <Card>
        <CardHeader
          title="Корреляционная матрица"
          subtitle="Корреляция между торговыми парами"
        />
        <CardContent>
          {correlationLoading ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : correlationData && correlationData.pairs.length > 0 ? (
            <div className="overflow-x-auto">
              <div className="inline-block min-w-full">
                <div className="grid gap-0.5" style={{ gridTemplateColumns: `auto repeat(${correlationData.pairs.length}, 1fr)` }}>
                  {/* Header row */}
                  <div className="bg-dark-bg-secondary p-2" />
                  {correlationData.pairs.map((pair) => (
                    <div
                      key={`header-${pair}`}
                      className="bg-dark-bg-secondary p-2 text-xs font-medium text-dark-text-primary text-center"
                    >
                      {pair}
                    </div>
                  ))}
                  
                  {/* Matrix rows */}
                  {correlationData.matrix.map((row, i) => (
                    <React.Fragment key={`row-${i}`}>
                      <div className="bg-dark-bg-secondary p-2 text-xs font-medium text-dark-text-primary">
                        {correlationData.pairs[i]}
                      </div>
                      {row.map((value, j) => {
                        const intensity = Math.abs(value);
                        const color = value >= 0 
                          ? `rgba(0, 200, 83, ${intensity})` 
                          : `rgba(255, 82, 82, ${intensity})`;
                        
                        return (
                          <div
                            key={`cell-${i}-${j}`}
                            className="p-2 text-xs font-mono text-center"
                            style={{ backgroundColor: color }}
                            title={`${correlationData.pairs[i]} vs ${correlationData.pairs[j]}: ${value.toFixed(3)}`}
                          >
                            {value.toFixed(2)}
                          </div>
                        );
                      })}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-dark-text-muted">
              <Grid3x3 className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Нет данных корреляции</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Analytics;

