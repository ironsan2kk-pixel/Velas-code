import React from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui';
import { t } from '@/i18n';
import { BarChart3 } from 'lucide-react';

const Analytics: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('nav.analytics')}</h1>
        <p className="text-dark-text-secondary mt-1">
          Детальная аналитика торговли
        </p>
      </div>

      {/* Metrics Grid Placeholder */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {['Profit Factor', 'Sharpe Ratio', 'Max DD', 'Win Rate'].map((metric) => (
          <Card key={metric} className="card-hover">
            <CardContent className="p-4">
              <p className="text-sm text-dark-text-muted">{metric}</p>
              <p className="text-2xl font-bold mt-1">--</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader 
          title="Аналитика" 
          subtitle="Графики и статистика"
        />
        <CardContent>
          <div className="flex flex-col items-center justify-center py-16 text-dark-text-muted">
            <BarChart3 className="w-12 h-12 mb-4 opacity-50" />
            <p>Загрузка аналитики...</p>
            <p className="text-sm mt-2">Страница будет реализована в VELAS-09</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Analytics;
