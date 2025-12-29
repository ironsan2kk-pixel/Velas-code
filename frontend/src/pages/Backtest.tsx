import React from 'react';
import { Card, CardHeader, CardContent, Button } from '@/components/ui';
import { t } from '@/i18n';
import { TestTube, Play } from 'lucide-react';

const Backtest: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('nav.backtest')}</h1>
        <p className="text-dark-text-secondary mt-1">
          Тестирование стратегий на исторических данных
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Config Panel */}
        <Card>
          <CardHeader title="Настройки теста" />
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm text-dark-text-secondary">Пара</label>
              <select className="input mt-1 w-full">
                <option>BTCUSDT</option>
                <option>ETHUSDT</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-dark-text-secondary">Таймфрейм</label>
              <select className="input mt-1 w-full">
                <option>30m</option>
                <option>1h</option>
                <option>2h</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-dark-text-secondary">Период</label>
              <input type="text" className="input mt-1 w-full" placeholder="2024-01-01 - 2024-12-01" disabled />
            </div>
            <Button className="w-full" disabled>
              <Play className="w-4 h-4 mr-2" />
              Запустить тест
            </Button>
            <p className="text-xs text-dark-text-muted text-center">
              Функционал будет в VELAS-09
            </p>
          </CardContent>
        </Card>

        {/* Results Panel */}
        <Card className="lg:col-span-2">
          <CardHeader 
            title="Результаты" 
            subtitle="Последний бэктест"
          />
          <CardContent>
            <div className="flex flex-col items-center justify-center py-16 text-dark-text-muted">
              <TestTube className="w-12 h-12 mb-4 opacity-50" />
              <p>Запустите бэктест для просмотра результатов</p>
              <p className="text-sm mt-2">Страница будет реализована в VELAS-09</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Backtest;
