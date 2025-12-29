/**
 * VELAS - Settings Page
 * Страница настроек системы
 */

import React, { useState } from 'react';
import { Card, CardHeader, CardContent, CardFooter, Button, Input, Select, Spinner, Badge } from '@/components/ui';
import { useSettings, useUpdateSettings, usePresets, useUpdatePreset } from '@/hooks/useApi';
import { Save, RefreshCw, AlertCircle, CheckCircle2, Settings2, Shield, Bell, Cpu } from 'lucide-react';
import type { SystemSettings, Preset } from '@/types';

type SettingsTab = 'trading' | 'portfolio' | 'telegram' | 'system' | 'presets';

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<SettingsTab>('trading');
  const [hasChanges, setHasChanges] = useState(false);
  
  const { data: settingsResp, isLoading } = useSettings();
  const settings = settingsResp?.data;
  const updateSettings = useUpdateSettings();
  const { data: presetsResp, isLoading: presetsLoading } = usePresets();
  const presets = presetsResp?.data || [];
  const updatePreset = useUpdatePreset();

  const [formData, setFormData] = useState<SystemSettings | null>(null);

  // Initialize form data when settings load
  React.useEffect(() => {
    if (settings && !formData) {
      setFormData(settings);
    }
  }, [settings, formData]);

  // Handle input change
  const handleChange = (section: keyof SystemSettings, field: string, value: any) => {
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

  // Save settings
  const handleSave = async () => {
    if (!formData) return;
    
    try {
      await updateSettings.mutateAsync(formData);
      setHasChanges(false);
    } catch (error) {
      console.error('Error saving settings:', error);
    }
  };

  // Reset to original
  const handleReset = () => {
    if (settings) {
      setFormData(settings);
      setHasChanges(false);
    }
  };

  // Toggle preset active status
  const handleTogglePreset = async (preset: Preset) => {
    try {
      await updatePreset.mutateAsync({
        id: preset.id,
        data: { active: !preset.active },
      });
    } catch (error) {
      console.error('Error toggling preset:', error);
    }
  };

  if (isLoading || !formData) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  const tabs: { id: SettingsTab; label: string; icon: React.ReactNode }[] = [
    { id: 'trading', label: 'Торговля', icon: <Settings2 className="w-4 h-4" /> },
    { id: 'portfolio', label: 'Портфель', icon: <Shield className="w-4 h-4" /> },
    { id: 'telegram', label: 'Telegram', icon: <Bell className="w-4 h-4" /> },
    { id: 'system', label: 'Система', icon: <Cpu className="w-4 h-4" /> },
    { id: 'presets', label: 'Пресеты', icon: <RefreshCw className="w-4 h-4" /> },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-text-primary">Настройки</h1>
          <p className="text-dark-text-secondary mt-1">
            Конфигурация торговой системы VELAS
          </p>
        </div>
        {hasChanges && (
          <div className="flex items-center gap-3">
            <Button variant="secondary" onClick={handleReset}>
              Отменить
            </Button>
            <Button
              onClick={handleSave}
              loading={updateSettings.isPending}
              icon={<Save className="w-4 h-4" />}
            >
              Сохранить
            </Button>
          </div>
        )}
      </div>

      {/* Tabs */}
      <Card>
        <div className="flex border-b border-dark-border overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-4 font-medium border-b-2 transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-accent-blue text-accent-blue'
                  : 'border-transparent text-dark-text-secondary hover:text-dark-text-primary'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        <CardContent className="p-6">
          {/* Trading Settings */}
          {activeTab === 'trading' && (
            <div className="space-y-6">
              <div className="flex items-start gap-3 p-4 bg-accent-blue/10 border border-accent-blue/20 rounded-lg">
                <AlertCircle className="w-5 h-5 text-accent-blue shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-dark-text-primary">Настройки торговли</p>
                  <p className="text-dark-text-secondary mt-1">
                    Базовые параметры для управления позициями и рисками
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="trading-enabled"
                      checked={formData.trading.enabled}
                      onChange={(e) => handleChange('trading', 'enabled', e.target.checked)}
                      className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                    />
                    <label htmlFor="trading-enabled" className="text-sm font-medium text-dark-text-primary">
                      Торговля включена
                    </label>
                  </div>

                  <Input
                    type="number"
                    label="Максимум открытых позиций"
                    value={formData.trading.max_open_positions}
                    onChange={(e) => handleChange('trading', 'max_open_positions', Number(e.target.value))}
                    min={1}
                    max={10}
                  />

                  <Input
                    type="number"
                    label="Риск на сделку (%)"
                    value={formData.trading.risk_per_trade}
                    onChange={(e) => handleChange('trading', 'risk_per_trade', Number(e.target.value))}
                    min={0.5}
                    max={5}
                    step={0.5}
                  />

                  <Input
                    type="number"
                    label="Макс. нагрузка портфеля (%)"
                    value={formData.trading.max_portfolio_heat}
                    onChange={(e) => handleChange('trading', 'max_portfolio_heat', Number(e.target.value))}
                    min={5}
                    max={50}
                  />
                </div>

                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="multiple-per-pair"
                      checked={formData.trading.allow_multiple_per_pair}
                      onChange={(e) => handleChange('trading', 'allow_multiple_per_pair', e.target.checked)}
                      className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                    />
                    <label htmlFor="multiple-per-pair" className="text-sm font-medium text-dark-text-primary">
                      Несколько позиций по одной паре
                    </label>
                  </div>

                  <Input
                    type="number"
                    label="Минимальная уверенность сигнала (%)"
                    value={formData.trading.min_signal_confidence}
                    onChange={(e) => handleChange('trading', 'min_signal_confidence', Number(e.target.value))}
                    min={50}
                    max={95}
                  />

                  <Input
                    type="number"
                    label="Срок действия сигнала (часы)"
                    value={formData.trading.signal_expiry_hours}
                    onChange={(e) => handleChange('trading', 'signal_expiry_hours', Number(e.target.value))}
                    min={1}
                    max={24}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Portfolio Settings */}
          {activeTab === 'portfolio' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <Input
                    type="number"
                    label="Начальный баланс ($)"
                    value={formData.portfolio.initial_balance}
                    onChange={(e) => handleChange('portfolio', 'initial_balance', Number(e.target.value))}
                    min={1000}
                    step={1000}
                  />

                  <Input
                    type="number"
                    label="Макс. корреляция портфеля"
                    value={formData.portfolio.max_correlation_exposure}
                    onChange={(e) => handleChange('portfolio', 'max_correlation_exposure', Number(e.target.value))}
                    min={1}
                    max={5}
                  />

                  <Input
                    type="number"
                    label="Порог корреляции"
                    value={formData.portfolio.correlation_threshold}
                    onChange={(e) => handleChange('portfolio', 'correlation_threshold', Number(e.target.value))}
                    min={0.5}
                    max={0.95}
                    step={0.05}
                  />
                </div>

                <div className="space-y-4">
                  <Input
                    type="number"
                    label="Лимит макс. просадки (%)"
                    value={formData.portfolio.max_drawdown_limit}
                    onChange={(e) => handleChange('portfolio', 'max_drawdown_limit', Number(e.target.value))}
                    min={5}
                    max={30}
                  />

                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="auto-pause"
                      checked={formData.portfolio.auto_pause_on_loss_streak}
                      onChange={(e) => handleChange('portfolio', 'auto_pause_on_loss_streak', e.target.checked)}
                      className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                    />
                    <label htmlFor="auto-pause" className="text-sm font-medium text-dark-text-primary">
                      Автопауза при серии убытков
                    </label>
                  </div>

                  <Input
                    type="number"
                    label="Порог серии убытков"
                    value={formData.portfolio.loss_streak_threshold}
                    onChange={(e) => handleChange('portfolio', 'loss_streak_threshold', Number(e.target.value))}
                    min={2}
                    max={10}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Telegram Settings */}
          {activeTab === 'telegram' && (
            <div className="space-y-6">
              <div className="flex items-start gap-3 p-4 bg-accent-yellow/10 border border-accent-yellow/20 rounded-lg">
                <AlertCircle className="w-5 h-5 text-accent-yellow shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-dark-text-primary">Конфиденциальная информация</p>
                  <p className="text-dark-text-secondary mt-1">
                    Token и Chat ID хранятся в config.yaml и не отображаются в интерфейсе
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="telegram-enabled"
                    checked={formData.telegram.enabled}
                    onChange={(e) => handleChange('telegram', 'enabled', e.target.checked)}
                    className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                  />
                  <label htmlFor="telegram-enabled" className="text-sm font-medium text-dark-text-primary">
                    Telegram уведомления включены
                  </label>
                </div>

                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="send-signals"
                    checked={formData.telegram.send_signals}
                    onChange={(e) => handleChange('telegram', 'send_signals', e.target.checked)}
                    className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                  />
                  <label htmlFor="send-signals" className="text-sm font-medium text-dark-text-primary">
                    Отправлять сигналы (Cornix формат)
                  </label>
                </div>

                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="send-position-updates"
                    checked={formData.telegram.send_position_updates}
                    onChange={(e) => handleChange('telegram', 'send_position_updates', e.target.checked)}
                    className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                  />
                  <label htmlFor="send-position-updates" className="text-sm font-medium text-dark-text-primary">
                    Обновления позиций (TP/SL)
                  </label>
                </div>

                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="send-alerts"
                    checked={formData.telegram.send_alerts}
                    onChange={(e) => handleChange('telegram', 'send_alerts', e.target.checked)}
                    className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                  />
                  <label htmlFor="send-alerts" className="text-sm font-medium text-dark-text-primary">
                    Системные уведомления
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* System Settings */}
          {activeTab === 'system' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <Select
                    label="Уровень логирования"
                    value={formData.system.log_level}
                    onChange={(e) => handleChange('system', 'log_level', e.target.value)}
                    options={[
                      { value: 'DEBUG', label: 'DEBUG' },
                      { value: 'INFO', label: 'INFO' },
                      { value: 'WARNING', label: 'WARNING' },
                      { value: 'ERROR', label: 'ERROR' },
                    ]}
                  />

                  <Input
                    type="number"
                    label="Интервал обновления данных (сек)"
                    value={formData.system.data_update_interval}
                    onChange={(e) => handleChange('system', 'data_update_interval', Number(e.target.value))}
                    min={1}
                    max={60}
                  />

                  <Input
                    type="number"
                    label="Задержка переподключения WebSocket (сек)"
                    value={formData.system.websocket_reconnect_delay}
                    onChange={(e) => handleChange('system', 'websocket_reconnect_delay', Number(e.target.value))}
                    min={1}
                    max={30}
                  />
                </div>

                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="backup-enabled"
                      checked={formData.system.backup_enabled}
                      onChange={(e) => handleChange('system', 'backup_enabled', e.target.checked)}
                      className="w-4 h-4 rounded border-dark-border bg-dark-bg-tertiary"
                    />
                    <label htmlFor="backup-enabled" className="text-sm font-medium text-dark-text-primary">
                      Автоматический бэкап
                    </label>
                  </div>

                  <Input
                    type="number"
                    label="Интервал бэкапа (часы)"
                    value={formData.system.backup_interval_hours}
                    onChange={(e) => handleChange('system', 'backup_interval_hours', Number(e.target.value))}
                    min={1}
                    max={24}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Presets */}
          {activeTab === 'presets' && (
            <div className="space-y-4">
              {presetsLoading ? (
                <div className="flex justify-center py-8">
                  <Spinner />
                </div>
              ) : presets && presets.length > 0 ? (
                <div className="space-y-3">
                  {presets.map((preset) => (
                    <div
                      key={preset.id}
                      className="flex items-center justify-between p-4 bg-dark-bg-tertiary rounded-lg"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <span className="font-medium text-dark-text-primary">{preset.name}</span>
                          <Badge variant="secondary" size="sm">
                            {preset.symbol} • {preset.timeframe}
                          </Badge>
                          <Badge
                            variant={
                              preset.volatility_regime === 'LOW' ? 'info' :
                              preset.volatility_regime === 'HIGH' ? 'danger' : 'warning'
                            }
                            size="sm"
                          >
                            {preset.volatility_regime}
                          </Badge>
                        </div>
                        <div className="text-sm text-dark-text-muted mt-2">
                          <span>Sharpe: {preset.metrics.sharpe_ratio.toFixed(2)}</span>
                          <span className="mx-2">•</span>
                          <span>WR: {preset.metrics.win_rate.toFixed(1)}%</span>
                          <span className="mx-2">•</span>
                          <span>PF: {preset.metrics.profit_factor.toFixed(2)}</span>
                          <span className="mx-2">•</span>
                          <span>Robustness: {preset.metrics.robustness_score.toFixed(2)}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {preset.active ? (
                          <Badge variant="success" size="sm">
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Активен
                          </Badge>
                        ) : (
                          <Badge variant="secondary" size="sm">
                            Неактивен
                          </Badge>
                        )}
                        <Button
                          size="sm"
                          variant={preset.active ? 'secondary' : 'primary'}
                          onClick={() => handleTogglePreset(preset)}
                          loading={updatePreset.isPending}
                        >
                          {preset.active ? 'Отключить' : 'Активировать'}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-dark-text-muted">
                  <RefreshCw className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>Нет доступных пресетов</p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Settings;

