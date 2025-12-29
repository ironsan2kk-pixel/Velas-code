/**
 * VELAS - System Page
 * Страница системного мониторинга и логов
 */

import React, { useState } from 'react';
import { Card, CardHeader, CardContent, Button, Spinner, StatusIndicator, Badge, Select } from '@/components/ui';
import { useSystemStatus, useSystemLogs, useDownloadLogs, useRestartComponent } from '@/hooks/useApi';
import {
  Server,
  Database,
  Activity,
  Download,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  XCircle,
  HardDrive,
  Cpu,
  MemoryStick,
} from 'lucide-react';
import type { SystemComponent, ComponentStatus, LogEntry } from '@/types';

type LogLevel = 'all' | 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';

const System: React.FC = () => {
  const [selectedComponent, setSelectedComponent] = useState<string | null>(null);
  const [logLevel, setLogLevel] = useState<LogLevel>('all');
  const [logLimit, setLogLimit] = useState(100);

  const { data: systemStatus, isLoading: statusLoading } = useSystemStatus();
  const { data: logs, isLoading: logsLoading } = useSystemLogs(
    logLimit,
    logLevel === 'all' ? undefined : logLevel
  );
  const downloadLogs = useDownloadLogs();
  const restartComponent = useRestartComponent();

  const handleDownloadLogs = async () => {
    try {
      const blob = await downloadLogs.mutateAsync();
      const url = window.URL.createObjectURL(blob as any);
      const a = document.createElement('a');
      a.href = url;
      a.download = `velas_logs_${new Date().toISOString().split('T')[0]}.log`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading logs:', error);
    }
  };

  const handleRestart = async (component: string) => {
    if (!window.confirm(`Перезапустить компонент "${component}"?`)) {
      return;
    }

    try {
      await restartComponent.mutateAsync(component);
      setSelectedComponent(null);
    } catch (error) {
      console.error('Error restarting component:', error);
    }
  };

  const getStatusColor = (status: ComponentStatus): 'online' | 'offline' | 'error' => {
    if (status === 'online') return 'online';
    if (status === 'offline') return 'offline';
    return 'error';
  };

  const logLevelColors: Record<string, string> = {
    DEBUG: 'text-dark-text-muted',
    INFO: 'text-accent-blue',
    WARNING: 'text-accent-yellow',
    ERROR: 'text-accent-red',
    CRITICAL: 'text-accent-red font-bold',
  };

  if (statusLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-dark-text-primary">Система</h1>
        <p className="text-dark-text-secondary mt-1">
          Мониторинг компонентов и системные логи
        </p>
      </div>

      {/* System Resources */}
      {systemStatus && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-accent-blue/10 text-accent-blue">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm text-dark-text-muted">Uptime</p>
                  <p className="text-xl font-bold text-dark-text-primary">
                    {Math.floor(systemStatus.uptime_seconds / 3600)}ч
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-accent-purple/10 text-accent-purple">
                  <Cpu className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm text-dark-text-muted">CPU</p>
                  <p className="text-xl font-bold text-dark-text-primary">
                    {systemStatus.cpu_usage_percent.toFixed(1)}%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-accent-green/10 text-accent-green">
                  <MemoryStick className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm text-dark-text-muted">RAM</p>
                  <p className="text-xl font-bold text-dark-text-primary">
                    {systemStatus.memory_usage_mb.toFixed(0)}MB
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-accent-yellow/10 text-accent-yellow">
                  <HardDrive className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm text-dark-text-muted">Диск</p>
                  <p className="text-xl font-bold text-dark-text-primary">
                    {systemStatus.disk_usage_percent.toFixed(1)}%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Components Status */}
      <Card>
        <CardHeader title="Статус компонентов" />
        <CardContent>
          {systemStatus && Object.keys(systemStatus.components).length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(systemStatus.components).map(([name, component]) => (
                <div
                  key={name}
                  className={`p-4 rounded-lg border transition-colors ${
                    selectedComponent === name
                      ? 'bg-accent-blue/5 border-accent-blue'
                      : 'bg-dark-bg-tertiary border-dark-border'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      {name === 'live_engine' && <Activity className="w-5 h-5 text-dark-text-secondary" />}
                      {name === 'data_engine' && <Server className="w-5 h-5 text-dark-text-secondary" />}
                      {name === 'telegram_bot' && <Bell className="w-5 h-5 text-dark-text-secondary" />}
                      {name === 'database' && <Database className="w-5 h-5 text-dark-text-secondary" />}
                      <div>
                        <p className="font-medium text-dark-text-primary">
                          {name.split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                        </p>
                        {component.uptime_seconds !== undefined && (
                          <p className="text-xs text-dark-text-muted mt-0.5">
                            Uptime: {Math.floor(component.uptime_seconds / 3600)}ч
                          </p>
                        )}
                      </div>
                    </div>
                    <StatusIndicator
                      status={getStatusColor(component.status)}
                      pulse={component.status === 'online'}
                    />
                  </div>

                  {component.message && (
                    <p className="text-sm text-dark-text-secondary mb-3">{component.message}</p>
                  )}

                  {component.last_error && (
                    <div className="p-3 bg-accent-red/10 border border-accent-red/20 rounded-lg mb-3">
                      <div className="flex items-start gap-2">
                        <XCircle className="w-4 h-4 text-accent-red shrink-0 mt-0.5" />
                        <div className="text-sm">
                          <p className="font-medium text-accent-red">Последняя ошибка:</p>
                          <p className="text-dark-text-secondary mt-1">{component.last_error}</p>
                          {component.last_error_time && (
                            <p className="text-xs text-dark-text-muted mt-1">
                              {new Date(component.last_error_time).toLocaleString('ru-RU')}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleRestart(name)}
                    loading={restartComponent.isPending}
                    icon={<RefreshCw className="w-4 h-4" />}
                    className="w-full"
                  >
                    Перезапустить
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-dark-text-muted">
              <Server className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Нет данных о компонентах</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Logs */}
      <Card>
        <CardHeader
          title="Системные логи"
          subtitle={`Последние ${logLimit} записей`}
          action={
            <div className="flex items-center gap-3">
              <Select
                value={logLevel}
                onChange={(e) => setLogLevel(e.target.value as LogLevel)}
                options={[
                  { value: 'all', label: 'Все уровни' },
                  { value: 'DEBUG', label: 'DEBUG' },
                  { value: 'INFO', label: 'INFO' },
                  { value: 'WARNING', label: 'WARNING' },
                  { value: 'ERROR', label: 'ERROR' },
                  { value: 'CRITICAL', label: 'CRITICAL' },
                ]}
                className="w-40"
              />
              <Select
                value={logLimit}
                onChange={(e) => setLogLimit(Number(e.target.value))}
                options={[
                  { value: 50, label: '50' },
                  { value: 100, label: '100' },
                  { value: 200, label: '200' },
                  { value: 500, label: '500' },
                ]}
                className="w-24"
              />
              <Button
                size="sm"
                variant="secondary"
                onClick={handleDownloadLogs}
                loading={downloadLogs.isPending}
                icon={<Download className="w-4 h-4" />}
              >
                Скачать
              </Button>
            </div>
          }
        />
        <CardContent className="p-0">
          {logsLoading ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : logs && logs.length > 0 ? (
            <div className="max-h-[600px] overflow-y-auto">
              <table className="w-full text-sm font-mono">
                <thead className="bg-dark-bg-secondary sticky top-0 z-10">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-dark-text-muted w-40">
                      Время
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-dark-text-muted w-24">
                      Уровень
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-dark-text-muted w-32">
                      Компонент
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-dark-text-muted">
                      Сообщение
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-border">
                  {logs.map((log, idx) => (
                    <tr key={idx} className="hover:bg-dark-bg-hover">
                      <td className="px-4 py-2 text-dark-text-muted">
                        {new Date(log.timestamp).toLocaleString('ru-RU', {
                          month: '2-digit',
                          day: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                        })}
                      </td>
                      <td className="px-4 py-2">
                        <span className={logLevelColors[log.level] || 'text-dark-text-primary'}>
                          {log.level}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-dark-text-secondary">{log.component}</td>
                      <td className="px-4 py-2 text-dark-text-primary break-words">
                        {log.message}
                        {log.data && (
                          <details className="mt-1">
                            <summary className="cursor-pointer text-accent-blue text-xs">
                              Детали
                            </summary>
                            <pre className="mt-1 p-2 bg-dark-bg-tertiary rounded text-xs overflow-x-auto">
                              {JSON.stringify(log.data, null, 2)}
                            </pre>
                          </details>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-dark-text-muted">
              <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Нет логов</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default System;
