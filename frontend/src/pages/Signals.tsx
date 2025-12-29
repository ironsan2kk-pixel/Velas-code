import React, { useState } from 'react';
import { Card, CardHeader, CardContent, Badge, Button, Spinner } from '@/components/ui';
import { useSignals } from '@/hooks/useApi';
import { 
  Zap,
  CheckCircle2,
  XCircle,
  Clock,
  Filter,
  ChevronLeft,
  ChevronRight,
  Send,
  MessageCircle,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
} from 'lucide-react';

type SignalStatus = 'all' | 'active' | 'filled' | 'cancelled' | 'pending';

interface Signal {
  id: number;
  symbol: string;
  side: 'LONG' | 'SHORT';
  timeframe: string;
  entry_price: number;
  current_price: number;
  sl_price: number;
  tp1_price: number;
  tp2_price: number;
  tp3_price: number;
  tp4_price: number;
  tp5_price: number;
  tp6_price: number;
  status: string;
  preset_id: string;
  volatility_regime: string;
  confidence: number;
  filters_passed: string[];
  filters_failed: string[];
  telegram_sent: boolean;
  cornix_sent: boolean;
  created_at: string;
  executed_at?: string;
}

const statusConfig = {
  active: { 
    icon: Zap, 
    label: 'Активный', 
    color: 'text-accent-yellow',
    bg: 'bg-accent-yellow/10 border-accent-yellow/30'
  },
  filled: { 
    icon: CheckCircle2, 
    label: 'Исполнен', 
    color: 'text-accent-green',
    bg: 'bg-accent-green/10 border-accent-green/30'
  },
  cancelled: { 
    icon: XCircle, 
    label: 'Отменён', 
    color: 'text-dark-text-muted',
    bg: 'bg-dark-bg-tertiary border-dark-border'
  },
  pending: { 
    icon: Clock, 
    label: 'Ожидает', 
    color: 'text-accent-blue',
    bg: 'bg-accent-blue/10 border-accent-blue/30'
  },
  expired: { 
    icon: XCircle, 
    label: 'Истёк', 
    color: 'text-dark-text-muted',
    bg: 'bg-dark-bg-tertiary border-dark-border'
  },
};

const formatPrice = (price: number): string => {
  if (price >= 1000) return price.toLocaleString('ru-RU', { maximumFractionDigits: 0 });
  if (price >= 1) return price.toLocaleString('ru-RU', { maximumFractionDigits: 2 });
  return price.toLocaleString('ru-RU', { maximumFractionDigits: 4 });
};

const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp);
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// Signal Card Component
interface SignalCardProps {
  signal: Signal;
}

const SignalCard: React.FC<SignalCardProps> = ({ signal }) => {
  const [expanded, setExpanded] = useState(false);
  
  const status = statusConfig[signal.status as keyof typeof statusConfig] || statusConfig.pending;
  const StatusIcon = status.icon;
  const isLong = signal.side === 'LONG';
  
  // Calculate current P&L from entry
  const pnlPercent = isLong 
    ? ((signal.current_price - signal.entry_price) / signal.entry_price) * 100
    : ((signal.entry_price - signal.current_price) / signal.entry_price) * 100;
  
  const tpPrices = [
    signal.tp1_price,
    signal.tp2_price,
    signal.tp3_price,
    signal.tp4_price,
    signal.tp5_price,
    signal.tp6_price,
  ];

  return (
    <Card className={`border ${status.bg}`}>
      <CardContent className="p-0">
        {/* Header */}
        <div 
          className="flex items-center justify-between p-4 cursor-pointer hover:bg-dark-bg-hover/50 transition-colors"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex items-center gap-4">
            <div className={`p-2 rounded-lg ${status.bg}`}>
              <StatusIcon className={`w-5 h-5 ${status.color}`} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold">{signal.symbol}</span>
                <Badge variant={isLong ? 'success' : 'danger'}>
                  {signal.side}
                </Badge>
                <span className="text-xs text-dark-text-muted bg-dark-bg-tertiary px-2 py-0.5 rounded">
                  {signal.timeframe}
                </span>
              </div>
              <div className="flex items-center gap-3 mt-1 text-sm text-dark-text-muted">
                <span>Entry: {formatPrice(signal.entry_price)}</span>
                <span>•</span>
                <span>Conf: {signal.confidence.toFixed(0)}%</span>
                <span>•</span>
                <span>{formatTime(signal.created_at)}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Delivery Status */}
            <div className="hidden md:flex items-center gap-2">
              <div className={`flex items-center gap-1 text-xs ${signal.telegram_sent ? 'text-accent-green' : 'text-dark-text-muted'}`}>
                <Send className="w-3 h-3" />
                TG
              </div>
              <div className={`flex items-center gap-1 text-xs ${signal.cornix_sent ? 'text-accent-green' : 'text-dark-text-muted'}`}>
                <MessageCircle className="w-3 h-3" />
                Cornix
              </div>
            </div>

            {/* Current P&L */}
            {signal.status === 'active' || signal.status === 'filled' ? (
              <div className="text-right">
                <div className={`text-lg font-bold flex items-center gap-1 ${pnlPercent >= 0 ? 'text-profit' : 'text-loss'}`}>
                  {pnlPercent >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                  {pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%
                </div>
              </div>
            ) : (
              <Badge variant="default">{status.label}</Badge>
            )}
          </div>
        </div>

        {/* Expanded Content */}
        {expanded && (
          <div className="border-t border-dark-border p-4 space-y-4 bg-dark-bg-secondary/30">
            {/* TP/SL Levels */}
            <div className="grid grid-cols-7 gap-2">
              <div className="p-2 rounded-lg bg-loss/20 border border-loss/30 text-center">
                <div className="text-xs text-dark-text-muted">SL</div>
                <div className="font-medium text-loss text-sm">{formatPrice(signal.sl_price)}</div>
                <div className="text-xs text-loss">-8.5%</div>
              </div>
              {tpPrices.map((price, index) => (
                <div 
                  key={index}
                  className="p-2 rounded-lg bg-dark-bg-tertiary text-center"
                >
                  <div className="text-xs text-dark-text-muted">TP{index + 1}</div>
                  <div className="font-medium text-sm">{formatPrice(price)}</div>
                  <div className="text-xs text-profit">+{[1, 2, 3, 4, 7.5, 14][index]}%</div>
                </div>
              ))}
            </div>

            {/* Filters */}
            <div className="flex flex-wrap gap-4">
              <div>
                <p className="text-xs text-dark-text-muted mb-2">Фильтры пройдены</p>
                <div className="flex flex-wrap gap-1">
                  {signal.filters_passed.map((filter) => (
                    <Badge key={filter} variant="success" size="sm">
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                      {filter}
                    </Badge>
                  ))}
                </div>
              </div>
              {signal.filters_failed.length > 0 && (
                <div>
                  <p className="text-xs text-dark-text-muted mb-2">Фильтры не пройдены</p>
                  <div className="flex flex-wrap gap-1">
                    {signal.filters_failed.map((filter) => (
                      <Badge key={filter} variant="danger" size="sm">
                        <XCircle className="w-3 h-3 mr-1" />
                        {filter}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Meta Info */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2 border-t border-dark-border">
              <div>
                <p className="text-xs text-dark-text-muted">Пресет</p>
                <p className="font-medium text-sm">{signal.preset_id}</p>
              </div>
              <div>
                <p className="text-xs text-dark-text-muted">Волатильность</p>
                <Badge variant="default" size="sm">
                  {signal.volatility_regime.toUpperCase()}
                </Badge>
              </div>
              <div>
                <p className="text-xs text-dark-text-muted">Создан</p>
                <p className="font-medium text-sm">{formatTime(signal.created_at)}</p>
              </div>
              {signal.executed_at && (
                <div>
                  <p className="text-xs text-dark-text-muted">Исполнен</p>
                  <p className="font-medium text-sm">{formatTime(signal.executed_at)}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const Signals: React.FC = () => {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<SignalStatus>('all');
  const pageSize = 10;

  const { data: signalsData, isLoading } = useSignals(
    page, 
    pageSize, 
    statusFilter === 'all' ? undefined : statusFilter
  );

  const signals = signalsData?.data || [];
  const totalPages = signalsData?.total_pages || 1;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-dark-text-primary">
            Сигналы
          </h1>
          <p className="text-dark-text-secondary mt-1">
            Лог торговых сигналов системы
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm text-dark-text-muted">Статус:</span>
        {[
          { value: 'all', label: 'Все' },
          { value: 'active', label: 'Активные' },
          { value: 'filled', label: 'Исполненные' },
          { value: 'pending', label: 'Ожидающие' },
          { value: 'cancelled', label: 'Отменённые' },
        ].map(({ value, label }) => (
          <button
            key={value}
            onClick={() => {
              setStatusFilter(value as SignalStatus);
              setPage(1);
            }}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              statusFilter === value
                ? 'bg-accent-blue text-white'
                : 'bg-dark-bg-tertiary text-dark-text-secondary hover:bg-dark-bg-hover'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Signals List */}
      <div className="space-y-3">
        {signals.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-dark-text-muted opacity-50" />
              <h3 className="text-lg font-medium text-dark-text-primary mb-2">
                Нет сигналов
              </h3>
              <p className="text-dark-text-muted">
                {statusFilter === 'all' 
                  ? 'Система ещё не сгенерировала сигналов'
                  : `Нет сигналов со статусом "${statusFilter}"`
                }
              </p>
            </CardContent>
          </Card>
        ) : (
          signals.map((signal: Signal) => (
            <SignalCard key={signal.id} signal={signal} />
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="text-sm text-dark-text-muted px-4">
            Страница {page} из {totalPages}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
};

export default Signals;

