import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardContent, Badge, Spinner, StatusIndicator } from '@/components/ui';
import { EquityCurve, MiniChart } from '@/components/charts';
import { 
  useDashboardSummary, 
  useDashboardMetrics, 
  useDashboardChart,
  usePositions,
  useSignals,
} from '@/hooks/useApi';
import { 
  Activity, 
  TrendingUp, 
  TrendingDown,
  Wallet, 
  Signal,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Zap,
  Target,
  BarChart3,
  Clock,
} from 'lucide-react';

type ChartPeriod = '1d' | '1w' | '1m' | '3m';

const periodLabels: Record<ChartPeriod, string> = {
  '1d': '1Д',
  '1w': '1Н',
  '1m': '1М',
  '3m': '3М',
};

// Stat card component
interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  subValue?: string;
  trend?: 'up' | 'down' | 'neutral';
  color?: 'green' | 'red' | 'blue' | 'yellow' | 'purple';
}

const StatCard: React.FC<StatCardProps> = ({ 
  icon, 
  label, 
  value, 
  subValue,
  trend,
  color = 'blue' 
}) => {
  const colorClasses = {
    green: 'bg-accent-green/10 text-accent-green',
    red: 'bg-accent-red/10 text-accent-red',
    blue: 'bg-accent-blue/10 text-accent-blue',
    yellow: 'bg-accent-yellow/10 text-accent-yellow',
    purple: 'bg-accent-purple/10 text-accent-purple',
  };

  return (
    <Card className="card-hover">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-lg ${colorClasses[color]}`}>
              {icon}
            </div>
            <div>
              <p className="text-sm text-dark-text-muted">{label}</p>
              <div className="flex items-baseline gap-2">
                <p className={`text-xl font-bold ${
                  trend === 'up' ? 'text-profit' : 
                  trend === 'down' ? 'text-loss' : 
                  'text-dark-text-primary'
                }`}>
                  {value}
                </p>
                {subValue && (
                  <span className="text-sm text-dark-text-muted">{subValue}</span>
                )}
              </div>
            </div>
          </div>
          {trend && (
            <div className={`p-1 rounded ${trend === 'up' ? 'text-profit' : 'text-loss'}`}>
              {trend === 'up' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Position mini card
interface PositionMiniProps {
  position: any;
}

const PositionMini: React.FC<PositionMiniProps> = ({ position }) => {
  const isProfit = position.unrealized_pnl >= 0;
  const tpHit = position.tp_levels?.filter((tp: any) => tp.hit).length || 0;
  
  return (
    <div className="flex items-center justify-between py-3 border-b border-dark-border last:border-0">
      <div className="flex items-center gap-3">
        <div className={`w-2 h-2 rounded-full ${position.side === 'LONG' ? 'bg-accent-green' : 'bg-accent-red'}`} />
        <div>
          <div className="flex items-center gap-2">
            <span className="font-medium">{position.symbol}</span>
            <Badge variant={position.side === 'LONG' ? 'success' : 'danger'} size="sm">
              {position.side}
            </Badge>
          </div>
          <div className="text-xs text-dark-text-muted">
            Entry: {position.entry_price.toLocaleString()}
          </div>
        </div>
      </div>
      <div className="text-right">
        <div className={`font-medium ${isProfit ? 'text-profit' : 'text-loss'}`}>
          {isProfit ? '+' : ''}{position.unrealized_pnl_percent?.toFixed(2)}%
        </div>
        <div className="text-xs text-dark-text-muted">
          TP: {tpHit}/6
        </div>
      </div>
    </div>
  );
};

// Signal mini card
interface SignalMiniProps {
  signal: any;
}

const SignalMini: React.FC<SignalMiniProps> = ({ signal }) => {
  const time = new Date(signal.created_at).toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  });

  const statusIcons = {
    active: <Zap className="w-4 h-4 text-accent-yellow" />,
    filled: <CheckCircle2 className="w-4 h-4 text-accent-green" />,
    cancelled: <XCircle className="w-4 h-4 text-dark-text-muted" />,
    pending: <Clock className="w-4 h-4 text-accent-blue" />,
  };

  return (
    <div className="flex items-center justify-between py-2.5 border-b border-dark-border last:border-0">
      <div className="flex items-center gap-3">
        {statusIcons[signal.status as keyof typeof statusIcons] || statusIcons.pending}
        <div>
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm">{signal.symbol}</span>
            <span className={`text-xs ${signal.side === 'LONG' ? 'text-profit' : 'text-loss'}`}>
              {signal.side}
            </span>
          </div>
          <div className="text-xs text-dark-text-muted">
            {signal.timeframe} • {signal.confidence?.toFixed(0)}%
          </div>
        </div>
      </div>
      <div className="text-xs text-dark-text-muted">
        {time}
      </div>
    </div>
  );
};

const Dashboard: React.FC = () => {
  const [chartPeriod, setChartPeriod] = useState<ChartPeriod>('1w');
  
  const { data: summaryResp, isLoading: summaryLoading } = useDashboardSummary();
  const { data: metricsResp, isLoading: metricsLoading } = useDashboardMetrics();
  const { data: chartResp, isLoading: chartLoading } = useDashboardChart(chartPeriod);
  const { data: positionsResp, isLoading: positionsLoading } = usePositions('open');
  const { data: signalsResp, isLoading: signalsLoading } = useSignals(1, 10);

  const summary = summaryResp?.data;
  const metrics = metricsResp?.data;
  const chartData = chartResp?.data || [];
  const signals = signalsResp?.data?.data || [];
  const openPositions = positionsResp?.data || [];

  if (summaryLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-text-primary">
            Панель управления
          </h1>
          <p className="text-dark-text-secondary mt-1">
            Обзор торговой системы VELAS
          </p>
        </div>
        <div className="flex items-center gap-3">
          <StatusIndicator 
            status={summary?.status === 'live' ? 'online' : 'offline'} 
            label={summary?.status === 'live' ? 'LIVE' : 'OFFLINE'}
            pulse
          />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          icon={<TrendingUp className="w-5 h-5" />}
          label="Общий P&L"
          value={`$${summary?.total_pnl?.toLocaleString() || 0}`}
          subValue={`${summary?.total_pnl_percent?.toFixed(1)}%`}
          trend={summary?.total_pnl >= 0 ? 'up' : 'down'}
          color="green"
        />
        <StatCard
          icon={<Target className="w-5 h-5" />}
          label="Win Rate"
          value={`${summary?.win_rate?.toFixed(1)}%`}
          color="blue"
        />
        <StatCard
          icon={<Wallet className="w-5 h-5" />}
          label="Позиции"
          value={`${summary?.active_positions || 0}`}
          subValue={`/ ${summary?.max_positions || 5}`}
          color="purple"
        />
        <StatCard
          icon={<Signal className="w-5 h-5" />}
          label="Сигналы сегодня"
          value={summary?.today_signals || 0}
          color="yellow"
        />
        <StatCard
          icon={<Activity className="w-5 h-5" />}
          label="Portfolio Heat"
          value={`${summary?.portfolio_heat?.toFixed(1)}%`}
          subValue={`/ ${summary?.max_heat}%`}
          color={summary?.portfolio_heat > 10 ? 'red' : 'green'}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Equity Chart */}
        <Card className="lg:col-span-2">
          <CardHeader 
            title="Кривая доходности" 
            subtitle={`Период: ${periodLabels[chartPeriod]}`}
            action={
              <div className="flex gap-1">
                {(Object.keys(periodLabels) as ChartPeriod[]).map((period) => (
                  <button
                    key={period}
                    onClick={() => setChartPeriod(period)}
                    className={`px-3 py-1 text-xs rounded-md transition-colors ${
                      chartPeriod === period
                        ? 'bg-accent-blue text-white'
                        : 'bg-dark-bg-tertiary text-dark-text-secondary hover:bg-dark-bg-hover'
                    }`}
                  >
                    {periodLabels[period]}
                  </button>
                ))}
              </div>
            }
          />
          <CardContent>
            {chartLoading ? (
              <div className="h-64 flex items-center justify-center">
                <Spinner />
              </div>
            ) : (
              <EquityCurve 
                data={chartData || []} 
                height={280}
                showGrid
                animated
              />
            )}
          </CardContent>
        </Card>

        {/* Quick Stats */}
        <Card>
          <CardHeader title="Ключевые метрики" />
          <CardContent className="space-y-4">
            {metricsLoading ? (
              <Spinner />
            ) : (
              <>
                <div className="flex justify-between items-center py-2 border-b border-dark-border">
                  <span className="text-dark-text-secondary">Profit Factor</span>
                  <span className="font-medium text-profit">{metrics?.profit_factor?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-dark-border">
                  <span className="text-dark-text-secondary">Sharpe Ratio</span>
                  <span className="font-medium">{metrics?.sharpe_ratio?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-dark-border">
                  <span className="text-dark-text-secondary">Max Drawdown</span>
                  <span className="font-medium text-loss">-{metrics?.max_drawdown?.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-dark-border">
                  <span className="text-dark-text-secondary">Всего сделок</span>
                  <span className="font-medium">{summary?.total_trades}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-dark-border">
                  <span className="text-dark-text-secondary">Win Streak</span>
                  <span className="font-medium text-profit">{metrics?.win_streak}</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-dark-text-secondary">Лучшая пара</span>
                  <span className="font-medium">{metrics?.best_pair}</span>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Positions & Signals */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Positions */}
        <Card>
          <CardHeader 
            title="Открытые позиции" 
            subtitle={`${openPositions.length} активных`}
            action={
              <Link 
                to="/positions" 
                className="text-sm text-accent-blue hover:underline flex items-center gap-1"
              >
                Все <ChevronRight className="w-4 h-4" />
              </Link>
            }
          />
          <CardContent>
            {positionsLoading ? (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            ) : openPositions.length === 0 ? (
              <div className="text-center py-8 text-dark-text-muted">
                <Wallet className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>Нет открытых позиций</p>
              </div>
            ) : (
              <div>
                {openPositions.slice(0, 5).map((position: any) => (
                  <PositionMini key={position.id} position={position} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Signals */}
        <Card>
          <CardHeader 
            title="Последние сигналы" 
            subtitle="За сегодня"
            action={
              <Link 
                to="/signals" 
                className="text-sm text-accent-blue hover:underline flex items-center gap-1"
              >
                Все <ChevronRight className="w-4 h-4" />
              </Link>
            }
          />
          <CardContent>
            {signalsLoading ? (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            ) : signals.length === 0 ? (
              <div className="text-center py-8 text-dark-text-muted">
                <Signal className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>Нет сигналов</p>
              </div>
            ) : (
              <div>
                {signals.slice(0, 7).map((signal: any) => (
                  <SignalMini key={signal.id} signal={signal} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Performance by Pair & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance by Pair */}
        <Card>
          <CardHeader title="Доходность по парам" subtitle="Топ 5" />
          <CardContent>
            <div className="space-y-3">
              {[
                { symbol: 'BTC', pnl: 8.2, color: 'green' },
                { symbol: 'ETH', pnl: 5.1, color: 'green' },
                { symbol: 'SOL', pnl: 3.2, color: 'green' },
                { symbol: 'BNB', pnl: 2.0, color: 'green' },
                { symbol: 'XRP', pnl: -0.5, color: 'red' },
              ].map((pair) => (
                <div key={pair.symbol} className="flex items-center gap-3">
                  <span className="w-10 font-medium">{pair.symbol}</span>
                  <div className="flex-1 h-6 bg-dark-bg-tertiary rounded overflow-hidden">
                    <div 
                      className={`h-full ${pair.pnl >= 0 ? 'bg-accent-green/60' : 'bg-accent-red/60'}`}
                      style={{ width: `${Math.min(Math.abs(pair.pnl) * 10, 100)}%` }}
                    />
                  </div>
                  <span className={`w-16 text-right font-medium ${pair.pnl >= 0 ? 'text-profit' : 'text-loss'}`}>
                    {pair.pnl >= 0 ? '+' : ''}{pair.pnl}%
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Alerts */}
        <Card>
          <CardHeader 
            title="Уведомления" 
            action={
              <Link 
                to="/alerts" 
                className="text-sm text-accent-blue hover:underline flex items-center gap-1"
              >
                Все <ChevronRight className="w-4 h-4" />
              </Link>
            }
          />
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-accent-yellow/10 border border-accent-yellow/20">
                <AlertTriangle className="w-5 h-5 text-accent-yellow shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-dark-text-primary">3 убыточных сделки подряд</p>
                  <p className="text-sm text-dark-text-muted">SOLUSDT — рассмотрите паузу</p>
                </div>
              </div>
              <div className="flex items-start gap-3 p-3 rounded-lg bg-accent-blue/10 border border-accent-blue/20">
                <BarChart3 className="w-5 h-5 text-accent-blue shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-dark-text-primary">Алгоритм обновлён</p>
                  <p className="text-sm text-dark-text-muted">Новые параметры для BTCUSDT</p>
                </div>
              </div>
              <div className="flex items-start gap-3 p-3 rounded-lg bg-accent-green/10 border border-accent-green/20">
                <CheckCircle2 className="w-5 h-5 text-accent-green shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-dark-text-primary">Система работает стабильно</p>
                  <p className="text-sm text-dark-text-muted">Uptime: 99.9%</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;

