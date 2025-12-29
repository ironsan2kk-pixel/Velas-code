import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { 
  History as HistoryIcon, 
  Download, 
  Filter, 
  Calendar,
  TrendingUp,
  TrendingDown,
  Target,
  Clock,
  DollarSign,
  Percent,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  X
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Spinner } from '../components/ui/Spinner';
import { apiClient } from '../api/client';

// Types
interface Trade {
  id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  timeframe: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  pnl_percent: number;
  tp_hit: number | null;
  sl_hit: boolean;
  duration_minutes: number;
  opened_at: string;
  closed_at: string;
  preset_id: string;
}

interface HistoryStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_pnl: number;
  profit_factor: number;
  avg_duration_minutes: number;
  best_trade: number;
  worst_trade: number;
  avg_win: number;
  avg_loss: number;
  max_consecutive_wins: number;
  max_consecutive_losses: number;
}

// Hooks
const useTradeHistory = (params: {
  page: number;
  limit: number;
  symbol?: string;
  side?: string;
  period?: string;
}) => {
  return useQuery({
    queryKey: ['history', params],
    queryFn: async () => {
      const response = await apiClient.get('/history', { params });
      return response.data;
    }
  });
};

const useHistoryStats = (period: string) => {
  return useQuery({
    queryKey: ['history-stats', period],
    queryFn: async () => {
      const response = await apiClient.get('/history/stats', { params: { period } });
      return response.data;
    }
  });
};

const useExportHistory = () => {
  return useMutation({
    mutationFn: async (format: 'csv' | 'xlsx') => {
      const response = await apiClient.get('/history/export', {
        params: { format },
        responseType: 'blob'
      });
      return { data: response.data, format };
    },
    onSuccess: ({ data, format }) => {
      const url = window.URL.createObjectURL(new Blob([data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `trade_history.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    }
  });
};

// Constants
const SYMBOLS = [
  'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
  'ADAUSDT', 'AVAXUSDT', 'DOGEUSDT', 'DOTUSDT', 'MATICUSDT',
  'LINKUSDT', 'UNIUSDT', 'ATOMUSDT', 'LTCUSDT', 'ETCUSDT',
  'NEARUSDT', 'APTUSDT', 'ARBUSDT', 'OPUSDT', 'INJUSDT'
];

const PERIODS = [
  { value: '7d', label: '7 дней' },
  { value: '30d', label: '30 дней' },
  { value: '90d', label: '90 дней' },
  { value: 'all', label: 'Все время' }
];

// Components
const StatCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string | number;
  subValue?: string;
  variant?: 'default' | 'success' | 'danger';
}> = ({ icon, label, value, subValue, variant = 'default' }) => {
  const variantClasses = {
    default: 'text-dark-text-primary',
    success: 'text-profit',
    danger: 'text-loss'
  };

  return (
    <div className="bg-dark-bg-tertiary rounded-lg p-4">
      <div className="flex items-center gap-2 text-dark-text-muted mb-1">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <div className={`text-xl font-bold ${variantClasses[variant]}`}>
        {value}
      </div>
      {subValue && (
        <div className="text-xs text-dark-text-muted mt-1">{subValue}</div>
      )}
    </div>
  );
};

const TradeRow: React.FC<{ trade: Trade }> = ({ trade }) => {
  const formatPrice = (price: number) => {
    if (price >= 1000) return price.toLocaleString('ru-RU', { maximumFractionDigits: 0 });
    if (price >= 1) return price.toFixed(2);
    return price.toFixed(4);
  };

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes}м`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)}ч ${minutes % 60}м`;
    return `${Math.floor(minutes / 1440)}д ${Math.floor((minutes % 1440) / 60)}ч`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <tr className="border-b border-dark-border hover:bg-dark-bg-tertiary/50 transition-colors">
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <span className="font-medium text-dark-text-primary">{trade.symbol.replace('USDT', '')}</span>
          <Badge variant={trade.side === 'LONG' ? 'success' : 'danger'} className="text-xs">
            {trade.side}
          </Badge>
        </div>
        <div className="text-xs text-dark-text-muted">{trade.timeframe}</div>
      </td>
      <td className="py-3 px-4 text-dark-text-secondary">
        <div>{formatPrice(trade.entry_price)}</div>
        <div className="text-xs text-dark-text-muted">Entry</div>
      </td>
      <td className="py-3 px-4 text-dark-text-secondary">
        <div>{formatPrice(trade.exit_price)}</div>
        <div className="text-xs text-dark-text-muted">Exit</div>
      </td>
      <td className="py-3 px-4">
        {trade.tp_hit ? (
          <Badge variant="success">TP{trade.tp_hit}</Badge>
        ) : trade.sl_hit ? (
          <Badge variant="danger">SL</Badge>
        ) : (
          <Badge variant="default">Manual</Badge>
        )}
      </td>
      <td className={`py-3 px-4 font-medium ${trade.pnl >= 0 ? 'text-profit' : 'text-loss'}`}>
        <div className="flex items-center gap-1">
          {trade.pnl >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          ${Math.abs(trade.pnl).toFixed(2)}
        </div>
        <div className="text-xs opacity-80">
          {trade.pnl >= 0 ? '+' : ''}{trade.pnl_percent.toFixed(2)}%
        </div>
      </td>
      <td className="py-3 px-4 text-dark-text-muted text-sm">
        {formatDuration(trade.duration_minutes)}
      </td>
      <td className="py-3 px-4 text-dark-text-muted text-sm">
        {formatDate(trade.closed_at)}
      </td>
    </tr>
  );
};

// Main Component
export const History: React.FC = () => {
  // State
  const [page, setPage] = useState(1);
  const [period, setPeriod] = useState('30d');
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [selectedSide, setSelectedSide] = useState<string>('');
  const [showFilters, setShowFilters] = useState(false);
  const limit = 20;

  // Queries
  const { data: historyData, isLoading: historyLoading } = useTradeHistory({
    page,
    limit,
    symbol: selectedSymbol || undefined,
    side: selectedSide || undefined,
    period
  });

  const { data: statsData, isLoading: statsLoading } = useHistoryStats(period);
  const exportMutation = useExportHistory();

  const trades: Trade[] = historyData?.data?.items || [];
  const totalPages = historyData?.data?.total_pages || 1;
  const stats: HistoryStats | null = statsData?.data || null;

  const clearFilters = () => {
    setSelectedSymbol('');
    setSelectedSide('');
    setPage(1);
  };

  const hasFilters = selectedSymbol || selectedSide;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <HistoryIcon className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-dark-text-primary">История сделок</h1>
            <p className="text-dark-text-muted">Все закрытые позиции</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Period selector */}
          <div className="flex bg-dark-bg-tertiary rounded-lg p-1">
            {PERIODS.map((p) => (
              <button
                key={p.value}
                onClick={() => { setPeriod(p.value); setPage(1); }}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  period === p.value
                    ? 'bg-accent-blue text-white'
                    : 'text-dark-text-secondary hover:text-dark-text-primary'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Filter toggle */}
          <Button
            variant={showFilters ? 'primary' : 'ghost'}
            onClick={() => setShowFilters(!showFilters)}
            className="relative"
          >
            <Filter className="w-4 h-4" />
            {hasFilters && (
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-accent-blue rounded-full" />
            )}
          </Button>

          {/* Export buttons */}
          <Button
            variant="ghost"
            onClick={() => exportMutation.mutate('csv')}
            disabled={exportMutation.isPending}
          >
            <Download className="w-4 h-4 mr-2" />
            CSV
          </Button>
          <Button
            variant="ghost"
            onClick={() => exportMutation.mutate('xlsx')}
            disabled={exportMutation.isPending}
          >
            <Download className="w-4 h-4 mr-2" />
            Excel
          </Button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-wrap items-center gap-4">
              {/* Symbol filter */}
              <div>
                <label className="block text-xs text-dark-text-muted mb-1">Пара</label>
                <select
                  value={selectedSymbol}
                  onChange={(e) => { setSelectedSymbol(e.target.value); setPage(1); }}
                  className="bg-dark-bg-tertiary text-dark-text-primary rounded-lg px-3 py-2 text-sm border border-dark-border focus:border-accent-blue outline-none"
                >
                  <option value="">Все пары</option>
                  {SYMBOLS.map((s) => (
                    <option key={s} value={s}>{s.replace('USDT', '/USDT')}</option>
                  ))}
                </select>
              </div>

              {/* Side filter */}
              <div>
                <label className="block text-xs text-dark-text-muted mb-1">Направление</label>
                <select
                  value={selectedSide}
                  onChange={(e) => { setSelectedSide(e.target.value); setPage(1); }}
                  className="bg-dark-bg-tertiary text-dark-text-primary rounded-lg px-3 py-2 text-sm border border-dark-border focus:border-accent-blue outline-none"
                >
                  <option value="">Все</option>
                  <option value="LONG">LONG</option>
                  <option value="SHORT">SHORT</option>
                </select>
              </div>

              {/* Clear filters */}
              {hasFilters && (
                <Button variant="ghost" onClick={clearFilters} className="mt-5">
                  <X className="w-4 h-4 mr-1" />
                  Сбросить
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats */}
      {statsLoading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          <StatCard
            icon={<Target className="w-4 h-4" />}
            label="Всего сделок"
            value={stats.total_trades}
            subValue={`${stats.winning_trades}W / ${stats.losing_trades}L`}
          />
          <StatCard
            icon={<Percent className="w-4 h-4" />}
            label="Win Rate"
            value={`${stats.win_rate.toFixed(1)}%`}
            variant={stats.win_rate >= 50 ? 'success' : 'danger'}
          />
          <StatCard
            icon={<DollarSign className="w-4 h-4" />}
            label="Общий P&L"
            value={`$${stats.total_pnl.toFixed(2)}`}
            variant={stats.total_pnl >= 0 ? 'success' : 'danger'}
          />
          <StatCard
            icon={<TrendingUp className="w-4 h-4" />}
            label="Profit Factor"
            value={stats.profit_factor.toFixed(2)}
            variant={stats.profit_factor >= 1.5 ? 'success' : stats.profit_factor >= 1 ? 'default' : 'danger'}
          />
          <StatCard
            icon={<Clock className="w-4 h-4" />}
            label="Ср. длительность"
            value={`${Math.round(stats.avg_duration_minutes / 60)}ч`}
          />
          <StatCard
            icon={<TrendingUp className="w-4 h-4" />}
            label="Лучшая сделка"
            value={`$${stats.best_trade.toFixed(2)}`}
            variant="success"
          />
          <StatCard
            icon={<TrendingDown className="w-4 h-4" />}
            label="Худшая сделка"
            value={`$${Math.abs(stats.worst_trade).toFixed(2)}`}
            variant="danger"
          />
        </div>
      )}

      {/* Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-dark-text-primary">
              Сделки
              {historyData?.data?.total && (
                <span className="text-dark-text-muted font-normal ml-2">
                  ({historyData.data.total})
                </span>
              )}
            </h2>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {historyLoading ? (
            <div className="flex justify-center py-12">
              <Spinner />
            </div>
          ) : trades.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-dark-text-muted">
              <HistoryIcon className="w-12 h-12 mb-3 opacity-50" />
              <p>Нет сделок за выбранный период</p>
              {hasFilters && (
                <Button variant="ghost" onClick={clearFilters} className="mt-2">
                  Сбросить фильтры
                </Button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-dark-border text-left">
                    <th className="py-3 px-4 text-dark-text-muted font-medium text-sm">Пара</th>
                    <th className="py-3 px-4 text-dark-text-muted font-medium text-sm">Вход</th>
                    <th className="py-3 px-4 text-dark-text-muted font-medium text-sm">Выход</th>
                    <th className="py-3 px-4 text-dark-text-muted font-medium text-sm">Результат</th>
                    <th className="py-3 px-4 text-dark-text-muted font-medium text-sm">P&L</th>
                    <th className="py-3 px-4 text-dark-text-muted font-medium text-sm">Время</th>
                    <th className="py-3 px-4 text-dark-text-muted font-medium text-sm">Закрыта</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.map((trade) => (
                    <TradeRow key={trade.id} trade={trade} />
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-dark-border">
              <div className="text-sm text-dark-text-muted">
                Страница {page} из {totalPages}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default History;
