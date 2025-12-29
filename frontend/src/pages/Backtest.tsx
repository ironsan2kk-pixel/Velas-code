/**
 * VELAS - Backtest Page
 * Страница для запуска и просмотра результатов бэктестов
 */

import React, { useState } from 'react';
import { Card, CardHeader, CardContent, CardFooter, Button, Input, Select, Spinner, Badge } from '@/components/ui';
import {
  useBacktestResults,
  useBacktestResult,
  useBacktestStatus,
  useRunBacktest,
} from '@/hooks/useApi';
import { PlayCircle, Clock, CheckCircle2, XCircle, TrendingUp, Activity, BarChart3 } from 'lucide-react';
import type { BacktestConfig, BacktestStatus as BStatus } from '@/types';

// 20 пар
const PAIRS = [
  'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
  'ADAUSDT', 'AVAXUSDT', 'DOGEUSDT', 'DOTUSDT', 'MATICUSDT',
  'LINKUSDT', 'UNIUSDT', 'ATOMUSDT', 'LTCUSDT', 'ETCUSDT',
  'NEARUSDT', 'APTUSDT', 'ARBUSDT', 'OPUSDT', 'INJUSDT',
];

const statusIcons = {
  pending: <Clock className="w-4 h-4 text-accent-yellow" />,
  running: <Activity className="w-4 h-4 text-accent-blue animate-pulse" />,
  completed: <CheckCircle2 className="w-4 h-4 text-accent-green" />,
  failed: <XCircle className="w-4 h-4 text-accent-red" />,
};

const statusLabels = {
  pending: 'Ожидание',
  running: 'Выполняется',
  completed: 'Завершён',
  failed: 'Ошибка',
};

const Backtest: React.FC = () => {
  const { data: results, isLoading: resultsLoading } = useBacktestResults();
  const runBacktest = useRunBacktest();
  
  const [selectedResultId, setSelectedResultId] = useState<string | null>(null);
  const [showNewBacktestForm, setShowNewBacktestForm] = useState(false);

  // Form state
  const [formData, setFormData] = useState<BacktestConfig>({
    symbol: 'BTCUSDT',
    timeframe: '1h',
    start_date: '',
    end_date: '',
    initial_balance: 10000,
    risk_per_trade: 2,
  });

  // Selected result detail
  const { data: selectedResult } = useBacktestResult(selectedResultId || '', {
    enabled: !!selectedResultId,
  });

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await runBacktest.mutateAsync(formData);
      setShowNewBacktestForm(false);
      setFormData({
        symbol: 'BTCUSDT',
        timeframe: '1h',
        start_date: '',
        end_date: '',
        initial_balance: 10000,
        risk_per_trade: 2,
      });
    } catch (error) {
      console.error('Error running backtest:', error);
    }
  };

  if (resultsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-text-primary">Бэктестинг</h1>
          <p className="text-dark-text-secondary mt-1">
            Тестирование стратегий на исторических данных
          </p>
        </div>
        <Button
          onClick={() => setShowNewBacktestForm(!showNewBacktestForm)}
          icon={<PlayCircle className="w-5 h-5" />}
        >
          Новый тест
        </Button>
      </div>

      {/* New Backtest Form */}
      {showNewBacktestForm && (
        <Card>
          <CardHeader title="Создание бэктеста" />
          <form onSubmit={handleSubmit}>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Select
                  label="Торговая пара"
                  value={formData.symbol}
                  onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                  options={PAIRS.map((p) => ({ value: p, label: p }))}
                />
                
                <Select
                  label="Таймфрейм"
                  value={formData.timeframe}
                  onChange={(e) => setFormData({ ...formData, timeframe: e.target.value as any })}
                  options={[
                    { value: '30m', label: '30 минут' },
                    { value: '1h', label: '1 час' },
                    { value: '2h', label: '2 часа' },
                  ]}
                />
                
                <Input
                  type="date"
                  label="Дата начала"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  required
                />
                
                <Input
                  type="date"
                  label="Дата окончания"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  required
                />
                
                <Input
                  type="number"
                  label="Начальный баланс ($)"
                  value={formData.initial_balance}
                  onChange={(e) => setFormData({ ...formData, initial_balance: Number(e.target.value) })}
                  min={1000}
                  step={1000}
                  required
                />
                
                <Input
                  type="number"
                  label="Риск на сделку (%)"
                  value={formData.risk_per_trade}
                  onChange={(e) => setFormData({ ...formData, risk_per_trade: Number(e.target.value) })}
                  min={0.5}
                  max={5}
                  step={0.5}
                  required
                />
              </div>
            </CardContent>
            <CardFooter>
              <div className="flex justify-end gap-3">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setShowNewBacktestForm(false)}
                >
                  Отмена
                </Button>
                <Button
                  type="submit"
                  loading={runBacktest.isPending}
                  icon={<PlayCircle className="w-4 h-4" />}
                >
                  Запустить тест
                </Button>
              </div>
            </CardFooter>
          </form>
        </Card>
      )}

      {/* Results List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader title="Список тестов" subtitle={`Всего: ${results?.length || 0}`} />
            <CardContent className="p-0">
              <div className="divide-y divide-dark-border max-h-[600px] overflow-y-auto">
                {results && results.length > 0 ? (
                  results.map((result) => (
                    <div
                      key={result.id}
                      onClick={() => setSelectedResultId(result.id)}
                      className={`p-4 cursor-pointer transition-colors ${
                        selectedResultId === result.id
                          ? 'bg-accent-blue/10 border-l-2 border-accent-blue'
                          : 'hover:bg-dark-bg-hover'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="font-medium text-dark-text-primary">
                            {result.symbol} • {result.timeframe}
                          </div>
                          <div className="text-xs text-dark-text-muted mt-0.5">
                            {new Date(result.created_at).toLocaleDateString('ru-RU')}
                          </div>
                        </div>
                        <Badge
                          variant={
                            result.status === 'completed' ? 'success' :
                            result.status === 'failed' ? 'danger' :
                            result.status === 'running' ? 'info' : 'warning'
                          }
                          size="sm"
                        >
                          {statusLabels[result.status]}
                        </Badge>
                      </div>
                      
                      {result.status === 'completed' && result.total_trades !== undefined && (
                        <div className="grid grid-cols-3 gap-2 text-xs">
                          <div>
                            <span className="text-dark-text-muted">Сделок:</span>{' '}
                            <span className="font-medium">{result.total_trades}</span>
                          </div>
                          <div>
                            <span className="text-dark-text-muted">WR:</span>{' '}
                            <span className="font-medium">{result.win_rate?.toFixed(1)}%</span>
                          </div>
                          <div>
                            <span className="text-dark-text-muted">P&L:</span>{' '}
                            <span className={`font-medium ${
                              (result.pnl_percent || 0) >= 0 ? 'text-profit' : 'text-loss'
                            }`}>
                              {(result.pnl_percent || 0) >= 0 ? '+' : ''}
                              {result.pnl_percent?.toFixed(2)}%
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="p-8 text-center text-dark-text-muted">
                    <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p>Нет результатов тестирования</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Detail */}
        <div className="lg:col-span-2">
          {selectedResult ? (
            <Card>
              <CardHeader
                title={`${selectedResult.config.symbol} • ${selectedResult.config.timeframe}`}
                subtitle={`${selectedResult.config.start_date} → ${selectedResult.config.end_date}`}
              />
              <CardContent>
                {selectedResult.status === 'running' ? (
                  <div className="text-center py-12">
                    <Spinner size="lg" className="mx-auto mb-4" />
                    <p className="text-dark-text-secondary">Выполняется бэктест...</p>
                  </div>
                ) : selectedResult.status === 'failed' ? (
                  <div className="text-center py-12 text-accent-red">
                    <XCircle className="w-12 h-12 mx-auto mb-4" />
                    <p className="font-medium">Ошибка выполнения</p>
                    {selectedResult.error && (
                      <p className="text-sm mt-2">{selectedResult.error}</p>
                    )}
                  </div>
                ) : selectedResult.metrics ? (
                  <div className="space-y-6">
                    {/* Metrics Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-4 bg-dark-bg-tertiary rounded-lg">
                        <div className="text-sm text-dark-text-muted mb-1">Сделок</div>
                        <div className="text-2xl font-bold text-dark-text-primary">
                          {selectedResult.metrics.total_trades}
                        </div>
                      </div>
                      
                      <div className="p-4 bg-dark-bg-tertiary rounded-lg">
                        <div className="text-sm text-dark-text-muted mb-1">Win Rate</div>
                        <div className={`text-2xl font-bold ${
                          selectedResult.metrics.win_rate >= 70 ? 'text-profit' : 'text-dark-text-primary'
                        }`}>
                          {selectedResult.metrics.win_rate.toFixed(1)}%
                        </div>
                      </div>
                      
                      <div className="p-4 bg-dark-bg-tertiary rounded-lg">
                        <div className="text-sm text-dark-text-muted mb-1">P&L</div>
                        <div className={`text-2xl font-bold ${
                          selectedResult.metrics.total_pnl_percent >= 0 ? 'text-profit' : 'text-loss'
                        }`}>
                          {selectedResult.metrics.total_pnl_percent >= 0 ? '+' : ''}
                          {selectedResult.metrics.total_pnl_percent.toFixed(2)}%
                        </div>
                      </div>
                      
                      <div className="p-4 bg-dark-bg-tertiary rounded-lg">
                        <div className="text-sm text-dark-text-muted mb-1">Sharpe</div>
                        <div className={`text-2xl font-bold ${
                          selectedResult.metrics.sharpe_ratio >= 1.5 ? 'text-profit' : 'text-dark-text-primary'
                        }`}>
                          {selectedResult.metrics.sharpe_ratio.toFixed(2)}
                        </div>
                      </div>
                    </div>

                    {/* Detailed Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-3">
                        <h4 className="font-medium text-dark-text-primary">Производительность</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-dark-text-muted">Profit Factor:</span>
                            <span className="font-medium">{selectedResult.metrics.profit_factor.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-dark-text-muted">Sortino Ratio:</span>
                            <span className="font-medium">{selectedResult.metrics.sortino_ratio.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-dark-text-muted">Expectancy:</span>
                            <span className="font-medium">${selectedResult.metrics.expectancy.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-dark-text-muted">Recovery Factor:</span>
                            <span className="font-medium">{selectedResult.metrics.recovery_factor.toFixed(2)}</span>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <h4 className="font-medium text-dark-text-primary">Риски</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-dark-text-muted">Max Drawdown:</span>
                            <span className="font-medium text-loss">
                              -{selectedResult.metrics.max_drawdown_percent.toFixed(2)}%
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-dark-text-muted">Средний выигрыш:</span>
                            <span className="font-medium text-profit">
                              ${selectedResult.metrics.avg_win.toFixed(2)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-dark-text-muted">Средний проигрыш:</span>
                            <span className="font-medium text-loss">
                              ${selectedResult.metrics.avg_loss.toFixed(2)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-dark-text-muted">Средняя длительность:</span>
                            <span className="font-medium">
                              {selectedResult.metrics.avg_duration_hours.toFixed(1)}ч
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 text-dark-text-muted">
                    <Activity className="w-12 h-12 mx-auto mb-4 opacity-30" />
                    <p>Результаты недоступны</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-24">
                <div className="text-center text-dark-text-muted">
                  <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-30" />
                  <p className="text-lg">Выберите результат теста</p>
                  <p className="text-sm mt-2">Нажмите на тест слева чтобы увидеть детали</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default Backtest;
