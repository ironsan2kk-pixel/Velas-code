import React from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui';
import { t } from '@/i18n';
import { Coins } from 'lucide-react';

const Pairs: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('nav.pairs')}</h1>
        <p className="text-dark-text-secondary mt-1">
          Информация по торговым парам
        </p>
      </div>

      <Card>
        <CardHeader 
          title="Торговые пары" 
          subtitle="20 активных пар"
        />
        <CardContent>
          <div className="flex flex-col items-center justify-center py-16 text-dark-text-muted">
            <Coins className="w-12 h-12 mb-4 opacity-50" />
            <p>Загрузка пар...</p>
            <p className="text-sm mt-2">Страница будет реализована в VELAS-09</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Pairs;
