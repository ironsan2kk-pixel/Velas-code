import React from 'react';
import { Card, CardHeader, CardContent, Button } from '@/components/ui';
import { t } from '@/i18n';
import { Bell, Plus } from 'lucide-react';

const Alerts: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t('nav.alerts')}</h1>
          <p className="text-dark-text-secondary mt-1">
            Настройка уведомлений и алертов
          </p>
        </div>
        <Button disabled>
          <Plus className="w-4 h-4 mr-2" />
          Новый алерт
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Alerts */}
        <Card>
          <CardHeader 
            title="Активные алерты" 
            subtitle="0 настроено"
          />
          <CardContent>
            <div className="flex flex-col items-center justify-center py-12 text-dark-text-muted">
              <Bell className="w-10 h-10 mb-3 opacity-50" />
              <p>Алертов не настроено</p>
              <p className="text-sm mt-2">Страница будет реализована в VELAS-09</p>
            </div>
          </CardContent>
        </Card>

        {/* Alert Types */}
        <Card>
          <CardHeader title="Типы уведомлений" />
          <CardContent className="space-y-3">
            {[
              { name: 'Новый сигнал', desc: 'При генерации сигнала', enabled: true },
              { name: 'Открытие позиции', desc: 'При входе в сделку', enabled: true },
              { name: 'Take Profit', desc: 'При срабатывании TP', enabled: false },
              { name: 'Stop Loss', desc: 'При срабатывании SL', enabled: true },
              { name: 'Системные ошибки', desc: 'При ошибках системы', enabled: true },
            ].map((alert) => (
              <div key={alert.name} className="flex items-center justify-between py-2">
                <div>
                  <p className="font-medium">{alert.name}</p>
                  <p className="text-xs text-dark-text-muted">{alert.desc}</p>
                </div>
                <div className={`w-3 h-3 rounded-full ${alert.enabled ? 'bg-accent-green' : 'bg-dark-border'}`} />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* History */}
      <Card>
        <CardHeader 
          title="История уведомлений" 
          subtitle="Последние 24 часа"
        />
        <CardContent>
          <div className="text-center py-8 text-dark-text-muted">
            История уведомлений будет в VELAS-09
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Alerts;
