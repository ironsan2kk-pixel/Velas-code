import React from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui';
import { t } from '@/i18n';
import { Signal } from 'lucide-react';

const Signals: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('nav.signals')}</h1>
        <p className="text-dark-text-secondary mt-1">
          Лог всех сигналов системы
        </p>
      </div>

      <Card>
        <CardHeader 
          title="Сигналы" 
          subtitle="Все сгенерированные сигналы"
        />
        <CardContent>
          <div className="flex flex-col items-center justify-center py-16 text-dark-text-muted">
            <Signal className="w-12 h-12 mb-4 opacity-50" />
            <p>Сигналов пока нет</p>
            <p className="text-sm mt-2">Страница будет реализована в VELAS-09</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Signals;
