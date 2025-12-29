import React, { useState } from 'react';
import { Card, CardHeader, CardContent, Badge, Button, Spinner, StatusIndicator } from '@/components/ui';
import { PositionProgress } from '@/components/charts';
import { usePositions, useClosePosition } from '@/hooks/useApi';
import { 
  TrendingUp, 
  TrendingDown,
  Clock,
  BarChart3,
  X,
  ChevronDown,
  ChevronUp,
  Filter,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';

type SortField = 'pnl' | 'symbol' | 'duration' | 'entry_time';
type SortOrder = 'asc' | 'desc';

interface Position {
  id: number;
  symbol: string;
  side: 'LONG' | 'SHORT';
  timeframe: string;
  entry_price: number;
  current_price: number;
  current_sl: number;
  original_sl: number;
  quantity: number;
  status: string;
  tp_levels: Array<{
    level: number;
    price: number;
    percent: number;
    hit: boolean;
    hit_time?: string;
  }>;
  position_left_percent: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  realized_pnl: number;
  duration_minutes: number;
  entry_time: string;
}

const formatDuration = (minutes: number): string => {
  if (minutes < 60) return `${minutes}м`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours < 24) return `${hours}ч ${mins}м`;
  const days = Math.floor(hours / 24);
  return `${days}д ${hours % 24}ч`;
};

const formatPrice = (price: number): string => {
  if (price >= 1000) return price.toLocaleString('ru-RU', { maximumFractionDigits: 0 });
  if (price >= 1) return price.toLocaleString('ru-RU', { maximumFractionDigits: 2 });
  return price.toLocaleString('ru-RU', { maximumFractionDigits: 4 });
};

// Position Card Component
interface PositionCardProps {
  position: Position;
  onClose: (id: number) => void;
  isClosing: boolean;
}

const PositionCard: React.FC<PositionCardProps> = ({ position, onClose, isClosing }) => {
  const [expanded, setExpanded] = useState(false);
  
  const isProfit = position.unrealized_pnl >= 0;
  const isLong = position.side === 'LONG';
  const tpHitCount = position.tp_levels.filter(tp => tp.hit).length;
  const isBreakeven = position.current_sl === position.entry_price;
  
  return (
    <Card className={`transition-all ${expanded ? 'ring-1 ring-accent-blue' : ''}`}>
      <CardContent className="p-0">
        {/* Main Row */}
        <div 
          className="flex items-center justify-between p-4 cursor-pointer hover:bg-dark-bg-hover transition-colors"
          onClick={() => setExpanded(!expanded)}
        >
          {/* Left: Symbol & Side */}
          <div className="flex items-center gap-4">
            <div className={`w-1.5 h-12 rounded-full ${isLong ? 'bg-accent-green' : 'bg-accent-red'}`} />
            <div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold">{position.symbol}</span>
                <Badge variant={isLong ? 'success' : 'danger'}>
                  {position.side}
                </Badge>
                <span className="text-xs text-dark-text-muted bg-dark-bg-tertiary px-2 py-0.5 rounded">
                  {position.timeframe}
                </span>
              </div>
              <div className="flex items-center gap-3 mt-1 text-sm text-dark-text-muted">
                <span>Entry: {formatPrice(position.entry_price)}</span>
                <span>•</span>
                <span>Current: {formatPrice(position.current_price)}</span>
              </div>
            </div>
          </div>

          {/* Center: TP Progress */}
          <div className="hidden md:flex items-center gap-1">
            {position.tp_levels.map((tp) => (
              <div
                key={tp.level}
                className={`w-6 h-6 rounded text-xs flex items-center justify-center font-medium transition-all ${
                  tp.hit
                    ? 'bg-accent-green text-white'
                    : 'bg-dark-bg-tertiary text-dark-text-muted'
                }`}
                title={`TP${tp.level}: ${formatPrice(tp.price)} (${tp.percent}%)`}
              >
                {tp.level}
              </div>
            ))}
          </div>

          {/* Right: P&L */}
          <div className="flex items-center gap-6">
            <div className="text-right">
              <div className={`text-xl font-bold ${isProfit ? 'text-profit' : 'text-loss'}`}>
                {isProfit ? '+' : ''}{position.unrealized_pnl_percent.toFixed(2)}%
              </div>
              <div className="text-sm text-dark-text-muted">
                {isProfit ? '+' : ''}${position.unrealized_pnl.toFixed(2)}
              </div>
            </div>
            <div className="text-dark-text-muted">
              {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </div>
          </div>
        </div>

        {/* Expanded Content */}
        {expanded && (
          <div className="border-t border-dark-border p-4 space-y-4 bg-dark-bg-secondary/50">
            {/* Progress Bar */}
            <PositionProgress
              side={position.side}
              entryPrice={position.entry_price}
              currentPrice={position.current_price}
              slPrice={position.current_sl}
              tpLevels={position.tp_levels}
            />

            {/* Details Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-dark-text-muted mb-1">Stop Loss</p>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-loss">{formatPrice(position.current_sl)}</span>
                  {isBreakeven && (
                    <Badge variant="warning" size="sm">BE</Badge>
                  )}
                </div>
              </div>
              <div>
                <p className="text-xs text-dark-text-muted mb-1">Позиция</p>
                <span className="font-medium">{position.position_left_percent}%</span>
              </div>
              <div>
                <p className="text-xs text-dark-text-muted mb-1">Длительность</p>
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4 text-dark-text-muted" />
                  <span className="font-medium">{formatDuration(position.duration_minutes)}</span>
                </div>
              </div>
              <div>
                <p className="text-xs text-dark-text-muted mb-1">Реализованный P&L</p>
                <span className={`font-medium ${position.realized_pnl >= 0 ? 'text-profit' : 'text-loss'}`}>
                  {position.realized_pnl >= 0 ? '+' : ''}${position.realized_pnl.toFixed(2)}
                </span>
              </div>
            </div>

            {/* TP Details */}
            <div className="grid grid-cols-6 gap-2">
              {position.tp_levels.map((tp) => (
                <div 
                  key={tp.level}
                  className={`p-2 rounded-lg text-center ${
                    tp.hit 
                      ? 'bg-accent-green/20 border border-accent-green/30' 
                      : 'bg-dark-bg-tertiary'
                  }`}
                >
                  <div className="text-xs text-dark-text-muted">TP{tp.level}</div>
                  <div className="font-medium text-sm">{formatPrice(tp.price)}</div>
                  <div className={`text-xs ${tp.hit ? 'text-profit' : 'text-dark-text-muted'}`}>
                    +{tp.percent}%
                  </div>
                </div>
              ))}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-2 border-t border-dark-border">
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm">
                  <BarChart3 className="w-4 h-4 mr-1" />
                  График
                </Button>
                <Button variant="ghost" size="sm">
                  Изменить SL
                </Button>
              </div>
              <Button 
                variant="danger" 
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onClose(position.id);
                }}
                disabled={isClosing}
              >
                {isClosing ? <Spinner size="sm" /> : <X className="w-4 h-4 mr-1" />}
                Закрыть
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const Positions: React.FC = () => {
  const [sortField, setSortField] = useState<SortField>('pnl');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [showFilters, setShowFilters] = useState(false);

  const { data: positionsResp, isLoading, refetch, isRefetching } = usePositions('open');
  const positions = positionsResp?.data || [];
  const closePosition = useClosePosition();

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const handleClose = async (id: number) => {
    if (confirm('Вы уверены, что хотите закрыть эту позицию?')) {
      await closePosition.mutateAsync(id);
    }
  };

  const sortedPositions = React.useMemo(() => {
    if (!positions) return [];
    
    return [...positions].sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'pnl':
          comparison = a.unrealized_pnl_percent - b.unrealized_pnl_percent;
          break;
        case 'symbol':
          comparison = a.symbol.localeCompare(b.symbol);
          break;
        case 'duration':
          comparison = a.duration_minutes - b.duration_minutes;
          break;
        case 'entry_time':
          comparison = new Date(a.entry_time).getTime() - new Date(b.entry_time).getTime();
          break;
      }
      return sortOrder === 'desc' ? -comparison : comparison;
    });
  }, [positions, sortField, sortOrder]);

  // Summary calculations
  const summary = React.useMemo(() => {
    if (!positions?.length) return null;
    
    const totalPnl = positions.reduce((sum: number, p: Position) => sum + p.unrealized_pnl + p.realized_pnl, 0);
    const totalInvestment = positions.reduce((sum: number, p: Position) => sum + p.entry_price * p.quantity, 0);
    const winning = positions.filter((p: Position) => p.unrealized_pnl > 0).length;
    const totalRisk = positions.reduce((sum: number, p: Position) => {
      const riskPercent = Math.abs((p.current_sl - p.entry_price) / p.entry_price * 100);
      return sum + riskPercent * (p.position_left_percent / 100);
    }, 0);

    return {
      count: positions.length,
      totalPnl,
      totalPnlPercent: totalInvestment ? (totalPnl / totalInvestment * 100) : 0,
      winning,
      losing: positions.length - winning,
      totalRisk: totalRisk / positions.length,
    };
  }, [positions]);

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
            Позиции
          </h1>
          <p className="text-dark-text-secondary mt-1">
            Управление открытыми позициями
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="w-4 h-4 mr-1" />
            Фильтры
          </Button>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${isRefetching ? 'animate-spin' : ''}`} />
            Обновить
          </Button>
        </div>
      </div>

      {/* Summary */}
      {summary && (
        <Card>
          <CardContent className="p-4">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div>
                <p className="text-xs text-dark-text-muted mb-1">Всего позиций</p>
                <p className="text-xl font-bold">{summary.count}</p>
              </div>
              <div>
                <p className="text-xs text-dark-text-muted mb-1">Общий P&L</p>
                <p className={`text-xl font-bold ${summary.totalPnl >= 0 ? 'text-profit' : 'text-loss'}`}>
                  {summary.totalPnl >= 0 ? '+' : ''}${summary.totalPnl.toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-xs text-dark-text-muted mb-1">P&L %</p>
                <p className={`text-xl font-bold ${summary.totalPnlPercent >= 0 ? 'text-profit' : 'text-loss'}`}>
                  {summary.totalPnlPercent >= 0 ? '+' : ''}{summary.totalPnlPercent.toFixed(2)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-dark-text-muted mb-1">В прибыли / В убытке</p>
                <p className="text-xl font-bold">
                  <span className="text-profit">{summary.winning}</span>
                  {' / '}
                  <span className="text-loss">{summary.losing}</span>
                </p>
              </div>
              <div>
                <p className="text-xs text-dark-text-muted mb-1">Средний риск</p>
                <p className={`text-xl font-bold ${summary.totalRisk > 3 ? 'text-accent-yellow' : ''}`}>
                  {summary.totalRisk.toFixed(1)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sort Controls */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-dark-text-muted">Сортировка:</span>
        {[
          { field: 'pnl' as SortField, label: 'P&L' },
          { field: 'symbol' as SortField, label: 'Символ' },
          { field: 'duration' as SortField, label: 'Время' },
        ].map(({ field, label }) => (
          <button
            key={field}
            onClick={() => handleSort(field)}
            className={`px-3 py-1 rounded-md transition-colors flex items-center gap-1 ${
              sortField === field
                ? 'bg-accent-blue text-white'
                : 'bg-dark-bg-tertiary text-dark-text-secondary hover:bg-dark-bg-hover'
            }`}
          >
            {label}
            {sortField === field && (
              sortOrder === 'desc' ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />
            )}
          </button>
        ))}
      </div>

      {/* Positions List */}
      <div className="space-y-4">
        {sortedPositions.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-dark-text-muted opacity-50" />
              <h3 className="text-lg font-medium text-dark-text-primary mb-2">
                Нет открытых позиций
              </h3>
              <p className="text-dark-text-muted">
                Система ожидает сигналов для открытия новых позиций
              </p>
            </CardContent>
          </Card>
        ) : (
          sortedPositions.map((position: Position) => (
            <PositionCard
              key={position.id}
              position={position}
              onClose={handleClose}
              isClosing={closePosition.isPending}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default Positions;

