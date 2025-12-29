import React from 'react';
import { Card, CardHeader, CardContent, Button } from '@/components/ui';
import { t } from '@/i18n';
import { Settings as SettingsIcon, Save } from 'lucide-react';
import { useThemeStore } from '@/stores';

const Settings: React.FC = () => {
  const { isDark, toggleTheme } = useThemeStore();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('nav.settings')}</h1>
        <p className="text-dark-text-secondary mt-1">
          Настройки торговой системы
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* UI Settings */}
        <Card>
          <CardHeader title="Интерфейс" />
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Тёмная тема</p>
                <p className="text-sm text-dark-text-muted">Переключить цветовую схему</p>
              </div>
              <button
                onClick={toggleTheme}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  isDark ? 'bg-accent-blue' : 'bg-dark-border'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    isDark ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Компактный режим</p>
                <p className="text-sm text-dark-text-muted">Уменьшить отступы</p>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-dark-border">
                <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-1" />
              </button>
            </div>
          </CardContent>
        </Card>

        {/* Trading Settings */}
        <Card>
          <CardHeader title="Торговля" />
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm text-dark-text-secondary">Макс. позиций</label>
              <input type="number" className="input mt-1 w-full" defaultValue={5} disabled />
            </div>
            <div>
              <label className="text-sm text-dark-text-secondary">Риск на сделку (%)</label>
              <input type="number" className="input mt-1 w-full" defaultValue={2} disabled />
            </div>
            <p className="text-xs text-dark-text-muted">
              Торговые настройки будут в VELAS-09
            </p>
          </CardContent>
        </Card>

        {/* Telegram Settings */}
        <Card>
          <CardHeader title="Telegram" />
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm text-dark-text-secondary">Bot Token</label>
              <input type="password" className="input mt-1 w-full" placeholder="••••••••" disabled />
            </div>
            <div>
              <label className="text-sm text-dark-text-secondary">Channel ID</label>
              <input type="text" className="input mt-1 w-full" placeholder="-1001234567890" disabled />
            </div>
            <p className="text-xs text-dark-text-muted">
              Telegram интеграция будет в VELAS-09
            </p>
          </CardContent>
        </Card>

        {/* Presets */}
        <Card>
          <CardHeader title="Пресеты" />
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 text-dark-text-muted">
              <SettingsIcon className="w-8 h-8 mb-3 opacity-50" />
              <p className="text-sm">Управление пресетами</p>
              <p className="text-xs mt-1">Будет в VELAS-09</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button disabled>
          <Save className="w-4 h-4 mr-2" />
          Сохранить настройки
        </Button>
      </div>
    </div>
  );
};

export default Settings;
