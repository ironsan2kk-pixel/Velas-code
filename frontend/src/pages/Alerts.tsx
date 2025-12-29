/**
 * VELAS - Alerts Page
 * Страница управления уведомлениями и алертами
 */

import React, { useState } from 'react';
import { Card, CardHeader, CardContent, Button, Spinner, Badge, Input } from '@/components/ui';
import { useAlertSettings, useUpdateAlertSettings, useAlertHistory } from '@/hooks/useApi';
import { useWebSocket } from '@/hooks/useWebSocket';
import {
  Bell,
  BellOff,
  Save,
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Info,
  XCircle,
  Volume2,
  VolumeX,
} from 'lucide-react';
import type { Alert, AlertType, AlertCategory } from '@/types';

type FilterTab = 'all' | 'unread' | 'trading' | 'portfolio' | 'system' | 'performance';

const Alerts: React.FC = () => {
  const [activeFilter, setActiveFilter] = useState<FilterTab>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [hasChanges, setHasChanges] = useState(false);

  const { data: alertSettings, isLoading: settingsLoading } = useAlertSettings();
  const updateAlertSettings = useUpdateAlertSettings();
  const { data: alertHistory, isLoading: historyLoading } = useAlertHistory(page, 20);

  // WebSocket for real-time alerts
  useWebSocket({
    channels: ['system'],
    onMessage: (message) => {
      if (message.type === 'system_status' || message.type === 'error') {
        // Можно добавить тост-уведомление
        console.log('New alert:', message);
      }
    },
  });

  const [formData, setFormData] = useState(alertSettings);

  React.useEffect(() => {
    if (alertSettings && !formData) {
      setFormData(alertSettings);
    }
  }, [alertSettings, formData]);

  const handleChange = (section: string, field: string, value: any) => {
    if (!formData) return;
    
    setFormData({
      ...formData,
      [section]: {
        ...formData[section],
        [field]: value,
      },
    });
    setHasChanges(true);
  };

  const handleSave = async () => {
    if (!formData) return;
    
    try {
      await updateAlertSettings.mutateAsync(formData);
      setHasChanges(false);
    } catch (error) {
      console.error('Error saving alert settings:', error);
    }
  };

  const handleReset = () => {
    if (alertSettings) {
      setFormData(alertSettings);
      setHasChanges(false);
    }
  };

  // Filter alerts
  const filteredAlerts = alertHistory?.data.filter((alert) => {
    const matchesSearch = alert.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         alert.message.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (activeFilter === 'all') return matchesSearch;
    if (activeFilter === 'unread') return matchesSearch && !alert.read;
    return matchesSearch && alert.category === activeFilter;
  }) || [];

  const alertTypeIcons: Record<AlertType, React.ReactNode> = {
    info: <Info className="w-5 h-5 text-accent-blue" />,
    success: <CheckCircle2 className="w-5 h-5 text-accent-green" />,
    warning: <AlertTriangle className="w-5 h-5 text-accent-yellow" />,
    error: <XCircle className="w-5 h-5 text-accent-red" />,
  };

  const alertTypeBg: Record<AlertType, string> = {
    info: 'bg-accent-blue/10 border-accent-blue/20',
    success: 'bg-accent-green/10 border-accent-green/20',
    warning: 'bg-accent-yellow/10 border-accent-yellow/20',
    error: 'bg-accent-red/10 border-accent-red/20',
  };

  if (settingsLoading || !formData) {
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
          <h1 className="text-2xl font-bold text-dark-text-primary">Уведомления</h1>
          <p className="text-dark-text-secondary mt-1">
            Настройка алертов и просмотр истории
          </p>
        </div>
        {hasChanges && (
          <div className="flex items-center gap-3">
            <Button variant="secondary" onClick={handleReset}>
              Отменить
            </Button>
            <Button
              onClick={handleSave}
              loading={updateAlertSettings.isPending}
              icon={<Save className="w-4 h-4" />}
            >
              Сохранить
            </Button>
          </div>
        )}
      </div>

      {/* Settings */}
      <Card>
        <CardHeader title="Настройки уведомлений" />
        <CardContent>
          <div className="space-y-6">
            {/* Global Settings */}
            <div>
              <h3 className="font-medium text-dark-text-primary mb-4">Общие настройки</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="enabled"
                    checked={formData.enabled}
                    onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                    className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                  />
                  <label htmlFor="enabled" className="flex items-center gap-2 text-sm font-medium text-dark-text-primary">
                    <Bell className="w-4 h-4" />
                    Уведомления
                  </label>
                </div>

                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="telegram"
                    checked={formData.telegram_enabled}
                    onChange={(e) => setFormData({ ...formData, telegram_enabled: e.target.checked })}
                    className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                  />
                  <label htmlFor="telegram" className="text-sm font-medium text-dark-text-primary">
                    Telegram
                  </label>
                </div>

                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="desktop"
                    checked={formData.desktop_enabled}
                    onChange={(e) => setFormData({ ...formData, desktop_enabled: e.target.checked })}
                    className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                  />
                  <label htmlFor="desktop" className="text-sm font-medium text-dark-text-primary">
                    Desktop
                  </label>
                </div>

                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="sound"
                    checked={formData.sound_enabled}
                    onChange={(e) => setFormData({ ...formData, sound_enabled: e.target.checked })}
                    className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                  />
                  <label htmlFor="sound" className="flex items-center gap-2 text-sm font-medium text-dark-text-primary">
                    {formData.sound_enabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                    Звук
                  </label>
                </div>
              </div>
            </div>

            {/* Trading Alerts */}
            <div>
              <h3 className="font-medium text-dark-text-primary mb-4">Торговые события</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(formData.trading_alerts).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id={`trading-${key}`}
                      checked={value}
                      onChange={(e) => handleChange('trading_alerts', key, e.target.checked)}
                      className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                    />
                    <label htmlFor={`trading-${key}`} className="text-sm text-dark-text-primary">
                      {key === 'new_signal' && 'Новый сигнал'}
                      {key === 'position_opened' && 'Позиция открыта'}
                      {key === 'tp_hit' && 'Take Profit достигнут'}
                      {key === 'sl_hit' && 'Stop Loss сработал'}
                      {key === 'position_closed' && 'Позиция закрыта'}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            {/* Portfolio Alerts */}
            <div>
              <h3 className="font-medium text-dark-text-primary mb-4">Портфельные риски</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(formData.portfolio_alerts).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id={`portfolio-${key}`}
                      checked={value}
                      onChange={(e) => handleChange('portfolio_alerts', key, e.target.checked)}
                      className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                    />
                    <label htmlFor={`portfolio-${key}`} className="text-sm text-dark-text-primary">
                      {key === 'max_positions_reached' && 'Достигнут лимит позиций'}
                      {key === 'high_correlation_warning' && 'Высокая корреляция'}
                      {key === 'portfolio_heat_limit' && 'Лимит нагрузки портфеля'}
                      {key === 'drawdown_limit' && 'Лимит просадки'}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            {/* System Alerts */}
            <div>
              <h3 className="font-medium text-dark-text-primary mb-4">Системные события</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(formData.system_alerts).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id={`system-${key}`}
                      checked={value}
                      onChange={(e) => handleChange('system_alerts', key, e.target.checked)}
                      className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                    />
                    <label htmlFor={`system-${key}`} className="text-sm text-dark-text-primary">
                      {key === 'component_offline' && 'Компонент offline'}
                      {key === 'api_error' && 'Ошибка API'}
                      {key === 'data_error' && 'Ошибка данных'}
                      {key === 'backtest_completed' && 'Бэктест завершён'}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            {/* Performance Alerts */}
            <div>
              <h3 className="font-medium text-dark-text-primary mb-4">Производительность</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="loss-streak"
                      checked={formData.performance_alerts.loss_streak}
                      onChange={(e) => handleChange('performance_alerts', 'loss_streak', e.target.checked)}
                      className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                    />
                    <label htmlFor="loss-streak" className="text-sm text-dark-text-primary">
                      Серия убытков
                    </label>
                  </div>
                  <Input
                    type="number"
                    label="Порог (сделок)"
                    value={formData.loss_streak_threshold}
                    onChange={(e) => setFormData({ ...formData, loss_streak_threshold: Number(e.target.value) })}
                    min={2}
                    max={10}
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="low-wr"
                      checked={formData.performance_alerts.low_win_rate}
                      onChange={(e) => handleChange('performance_alerts', 'low_win_rate', e.target.checked)}
                      className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                    />
                    <label htmlFor="low-wr" className="text-sm text-dark-text-primary">
                      Низкий WinRate
                    </label>
                  </div>
                  <Input
                    type="number"
                    label="Порог (%)"
                    value={formData.win_rate_threshold}
                    onChange={(e) => setFormData({ ...formData, win_rate_threshold: Number(e.target.value) })}
                    min={30}
                    max={70}
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="high-dd"
                      checked={formData.performance_alerts.high_drawdown}
                      onChange={(e) => handleChange('performance_alerts', 'high_drawdown', e.target.checked)}
                      className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                    />
                    <label htmlFor="high-dd" className="text-sm text-dark-text-primary">
                      Высокая просадка
                    </label>
                  </div>
                  <Input
                    type="number"
                    label="Порог (%)"
                    value={formData.drawdown_threshold}
                    onChange={(e) => setFormData({ ...formData, drawdown_threshold: Number(e.target.value) })}
                    min={5}
                    max={30}
                  />
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* History */}
      <Card>
        <CardHeader title="История уведомлений" subtitle={`Всего: ${alertHistory?.total || 0}`} />
        <CardContent>
          {/* Filters */}
          <div className="flex items-center gap-4 mb-6">
            <Input
              placeholder="Поиск..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              icon={<Search className="w-4 h-4" />}
              className="flex-1"
            />
            <div className="flex gap-2">
              {[
                { id: 'all', label: 'Все' },
                { id: 'unread', label: 'Непрочитанные' },
                { id: 'trading', label: 'Торговля' },
                { id: 'portfolio', label: 'Портфель' },
                { id: 'system', label: 'Система' },
                { id: 'performance', label: 'Производительность' },
              ].map((filter) => (
                <button
                  key={filter.id}
                  onClick={() => setActiveFilter(filter.id as FilterTab)}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                    activeFilter === filter.id
                      ? 'bg-accent-blue text-white'
                      : 'bg-dark-bg-tertiary text-dark-text-secondary hover:bg-dark-bg-hover'
                  }`}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>

          {/* Alert List */}
          {historyLoading ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : filteredAlerts.length > 0 ? (
            <div className="space-y-3">
              {filteredAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`flex items-start gap-3 p-4 rounded-lg border ${alertTypeBg[alert.type]} ${
                    !alert.read ? 'border-l-4' : ''
                  }`}
                >
                  {alertTypeIcons[alert.type]}
                  <div className="flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-medium text-dark-text-primary">{alert.title}</p>
                        <p className="text-sm text-dark-text-secondary mt-1">{alert.message}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <Badge variant="secondary" size="sm">
                          {alert.category}
                        </Badge>
                        <p className="text-xs text-dark-text-muted mt-1">
                          {new Date(alert.created_at).toLocaleString('ru-RU')}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-dark-text-muted">
              {formData.enabled ? (
                <>
                  <Bell className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>Нет уведомлений</p>
                </>
              ) : (
                <>
                  <BellOff className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>Уведомления отключены</p>
                </>
              )}
            </div>
          )}

          {/* Pagination */}
          {alertHistory && alertHistory.total_pages > 1 && (
            <div className="flex justify-center gap-2 mt-6">
              <Button
                size="sm"
                variant="secondary"
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
              >
                Назад
              </Button>
              <span className="px-4 py-2 text-sm text-dark-text-muted">
                Страница {page} из {alertHistory.total_pages}
              </span>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => setPage(page + 1)}
                disabled={page === alertHistory.total_pages}
              >
                Далее
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Alerts;
