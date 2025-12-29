import React from 'react';
import { Card, CardHeader, CardContent, Button, StatusIndicator } from '@/components/ui';
import { t } from '@/i18n';
import { Server, RefreshCw, Pause, Play, Download } from 'lucide-react';

const System: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t('nav.system')}</h1>
          <p className="text-dark-text-secondary mt-1">
            Мониторинг системы и компонентов
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" disabled>
            <Pause className="w-4 h-4 mr-2" />
            Пауза
          </Button>
          <Button variant="secondary" disabled>
            <RefreshCw className="w-4 h-4 mr-2" />
            Перезапуск
          </Button>
        </div>
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { name: 'Data Engine', status: 'online' as const },
          { name: 'Strategy Engine', status: 'online' as const },
          { name: 'Portfolio Manager', status: 'online' as const },
          { name: 'Telegram Bot', status: 'offline' as const },
        ].map((component) => (
          <Card key={component.name} className="card-hover">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <span className="font-medium">{component.name}</span>
                <StatusIndicator status={component.status} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Component Details */}
        <Card>
          <CardHeader title="Компоненты" />
          <CardContent className="space-y-4">
            {[
              { name: 'Binance REST API', latency: '45ms', status: 'ok' },
              { name: 'Binance WebSocket', latency: '12ms', status: 'ok' },
              { name: 'Database', latency: '3ms', status: 'ok' },
              { name: 'Telegram API', latency: '--', status: 'error' },
            ].map((item) => (
              <div key={item.name} className="flex items-center justify-between py-2 border-b border-dark-border last:border-0">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${item.status === 'ok' ? 'bg-accent-green' : 'bg-accent-red'}`} />
                  <span>{item.name}</span>
                </div>
                <span className="text-sm text-dark-text-muted">{item.latency}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* System Info */}
        <Card>
          <CardHeader title="Информация" />
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-dark-text-secondary">Версия</span>
              <span className="font-mono">1.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-text-secondary">Uptime</span>
              <span className="font-mono">3d 14h 22m</span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-text-secondary">CPU</span>
              <span className="font-mono">12%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-text-secondary">Memory</span>
              <span className="font-mono">256 MB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-text-secondary">База данных</span>
              <span className="font-mono">42 MB</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Logs */}
      <Card>
        <CardHeader 
          title="Логи системы" 
          subtitle="Последние события"
          action={
            <Button variant="ghost" size="sm" disabled>
              <Download className="w-4 h-4 mr-2" />
              Скачать
            </Button>
          }
        />
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-dark-text-muted">
            <Server className="w-10 h-10 mb-3 opacity-50" />
            <p>Логи будут отображаться здесь</p>
            <p className="text-sm mt-2">Страница будет реализована в VELAS-09</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default System;
