import React from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui';
import { t } from '@/i18n';
import { Activity, TrendingUp, Wallet, Signal } from 'lucide-react';

const Dashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-dark-text-primary dark:text-dark-text-primary">
          {t('nav.dashboard')}
        </h1>
        <p className="text-dark-text-secondary mt-1">
          Обзор торговой системы VELAS
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="card-hover">
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-accent-green/10">
                <TrendingUp className="w-6 h-6 text-accent-green" />
              </div>
              <div>
                <p className="text-sm text-dark-text-muted">Баланс</p>
                <p className="text-xl font-bold text-profit">+$12,450.00</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-accent-blue/10">
                <Wallet className="w-6 h-6 text-accent-blue" />
              </div>
              <div>
                <p className="text-sm text-dark-text-muted">Открытых позиций</p>
                <p className="text-xl font-bold">3 / 5</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-accent-purple/10">
                <Signal className="w-6 h-6 text-accent-purple" />
              </div>
              <div>
                <p className="text-sm text-dark-text-muted">Сигналов сегодня</p>
                <p className="text-xl font-bold">7</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-accent-yellow/10">
                <Activity className="w-6 h-6 text-accent-yellow" />
              </div>
              <div>
                <p className="text-sm text-dark-text-muted">Win Rate</p>
                <p className="text-xl font-bold">72.4%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Equity Chart Placeholder */}
        <Card className="lg:col-span-2">
          <CardHeader 
            title="Equity Curve" 
            subtitle="Динамика баланса"
          />
          <CardContent>
            <div className="h-64 flex items-center justify-center text-dark-text-muted">
              График будет добавлен в VELAS-09
            </div>
          </CardContent>
        </Card>

        {/* Quick Stats */}
        <Card>
          <CardHeader title="Статистика" />
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-dark-text-secondary">Profit Factor</span>
              <span className="font-medium">2.34</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-dark-text-secondary">Sharpe Ratio</span>
              <span className="font-medium">1.87</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-dark-text-secondary">Max Drawdown</span>
              <span className="font-medium text-loss">-8.4%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-dark-text-secondary">Всего сделок</span>
              <span className="font-medium">156</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Positions & Signals */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Positions */}
        <Card>
          <CardHeader 
            title="Открытые позиции" 
            subtitle="3 активных"
          />
          <CardContent>
            <div className="text-center py-8 text-dark-text-muted">
              Список позиций будет добавлен в VELAS-09
            </div>
          </CardContent>
        </Card>

        {/* Recent Signals */}
        <Card>
          <CardHeader 
            title="Последние сигналы" 
            subtitle="За сегодня"
          />
          <CardContent>
            <div className="text-center py-8 text-dark-text-muted">
              Лента сигналов будет добавлена в VELAS-09
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
