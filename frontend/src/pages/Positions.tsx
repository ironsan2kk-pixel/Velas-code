import React from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui';
import { t } from '@/i18n';
import { Wallet } from 'lucide-react';

const Positions: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t('nav.positions')}</h1>
        <p className="text-dark-text-secondary mt-1">
          Управление открытыми позициями
        </p>
      </div>

      <Card>
        <CardHeader 
          title="Открытые позиции" 
          subtitle="0 активных"
        />
        <CardContent>
          <div className="flex flex-col items-center justify-center py-16 text-dark-text-muted">
            <Wallet className="w-12 h-12 mb-4 opacity-50" />
            <p>Нет открытых позиций</p>
            <p className="text-sm mt-2">Страница будет реализована в VELAS-09</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Positions;
