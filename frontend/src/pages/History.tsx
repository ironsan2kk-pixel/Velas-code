import React from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui';
import { t } from '@/i18n';
import { History as HistoryIcon } from 'lucide-react';

const History: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('nav.history')}</h1>
        <p className="text-dark-text-secondary mt-1">
          История закрытых сделок
        </p>
      </div>

      <Card>
        <CardHeader 
          title="История сделок" 
          subtitle="Все закрытые позиции"
        />
        <CardContent>
          <div className="flex flex-col items-center justify-center py-16 text-dark-text-muted">
            <HistoryIcon className="w-12 h-12 mb-4 opacity-50" />
            <p>История пуста</p>
            <p className="text-sm mt-2">Страница будет реализована в VELAS-09</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default History;
