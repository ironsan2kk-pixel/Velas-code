/**
 * VELAS - Header Component
 * Шапка приложения с уведомлениями и статусом
 */

import React, { useState } from 'react';
import { StatusIndicator, Badge } from '@/components/ui';
import { useDashboardSummary } from '@/hooks/useApi';
import { useWebSocket } from '@/hooks/useWebSocket';
import {
  Sun,
  Moon,
  Bell,
  Wifi,
  WifiOff,
  ChevronDown,
} from 'lucide-react';

interface HeaderProps {
  theme: 'dark' | 'light';
  onThemeToggle: () => void;
}

export const Header: React.FC<HeaderProps> = ({ theme, onThemeToggle }) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const { data: summary } = useDashboardSummary();
  const { isConnected, connectionStatus } = useWebSocket();

  const [notifications] = useState([
    {
      id: '1',
      type: 'success' as const,
      title: 'Новая позиция открыта',
      message: 'BTCUSDT LONG @ $96,500',
      time: '2 мин назад',
    },
    {
      id: '2',
      type: 'warning' as const,
      title: 'TP2 достигнут',
      message: 'ETHUSDT SHORT (+3.5%)',
      time: '15 мин назад',
    },
    {
      id: '3',
      type: 'info' as const,
      title: 'Новый сигнал',
      message: 'SOLUSDT LONG — confidence 85%',
      time: '1 час назад',
    },
  ]);

  const unreadCount = notifications.length;

  return (
    <header className="fixed top-0 right-0 left-64 h-16 bg-dark-bg-secondary border-b border-dark-border z-20 transition-all duration-300">
      <div className="h-full flex items-center justify-between px-6">
        {/* Left: Status */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <StatusIndicator
              status={summary?.status === 'live' ? 'online' : 'offline'}
              label={summary?.status === 'live' ? 'LIVE' : 'OFFLINE'}
              pulse={summary?.status === 'live'}
            />
          </div>

          <div className="flex items-center gap-3">
            {isConnected ? (
              <div className="flex items-center gap-2 text-accent-green">
                <Wifi className="w-4 h-4" />
                <span className="text-sm font-medium">WebSocket</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-accent-red">
                <WifiOff className="w-4 h-4" />
                <span className="text-sm font-medium">Отключен</span>
              </div>
            )}
          </div>

          {summary && (
            <div className="flex items-center gap-4 text-sm">
              <div>
                <span className="text-dark-text-muted">Позиции:</span>{' '}
                <span className="font-medium text-dark-text-primary">
                  {summary.open_positions}
                </span>
              </div>
              <div>
                <span className="text-dark-text-muted">P&L:</span>{' '}
                <span
                  className={`font-medium ${
                    summary.total_pnl_percent >= 0 ? 'text-profit' : 'text-loss'
                  }`}
                >
                  {summary.total_pnl_percent >= 0 ? '+' : ''}
                  {summary.total_pnl_percent.toFixed(2)}%
                </span>
              </div>
              <div>
                <span className="text-dark-text-muted">Heat:</span>{' '}
                <span
                  className={`font-medium ${
                    summary.portfolio_heat > 70
                      ? 'text-accent-red'
                      : summary.portfolio_heat > 50
                      ? 'text-accent-yellow'
                      : 'text-accent-green'
                  }`}
                >
                  {summary.portfolio_heat.toFixed(0)}%
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-3">
          {/* Theme Toggle */}
          <button
            onClick={onThemeToggle}
            className="p-2 rounded-lg hover:bg-dark-bg-hover text-dark-text-secondary transition-colors"
            title={theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
          >
            {theme === 'dark' ? (
              <Sun className="w-5 h-5" />
            ) : (
              <Moon className="w-5 h-5" />
            )}
          </button>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 rounded-lg hover:bg-dark-bg-hover text-dark-text-secondary transition-colors"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-2 h-2 bg-accent-red rounded-full" />
              )}
            </button>

            {/* Notifications Dropdown */}
            {showNotifications && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setShowNotifications(false)}
                />
                <div className="absolute top-12 right-0 w-96 bg-dark-bg-card border border-dark-border rounded-lg shadow-lg z-50">
                  <div className="p-4 border-b border-dark-border">
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium text-dark-text-primary">Уведомления</h3>
                      <Badge variant="secondary" size="sm">
                        {unreadCount}
                      </Badge>
                    </div>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    {notifications.map((notif) => (
                      <div
                        key={notif.id}
                        className="p-4 border-b border-dark-border hover:bg-dark-bg-hover cursor-pointer transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          <div
                            className={`w-2 h-2 rounded-full mt-2 shrink-0 ${
                              notif.type === 'success'
                                ? 'bg-accent-green'
                                : notif.type === 'warning'
                                ? 'bg-accent-yellow'
                                : 'bg-accent-blue'
                            }`}
                          />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-dark-text-primary text-sm">
                              {notif.title}
                            </p>
                            <p className="text-sm text-dark-text-secondary mt-1">
                              {notif.message}
                            </p>
                            <p className="text-xs text-dark-text-muted mt-1">{notif.time}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="p-3 border-t border-dark-border text-center">
                    <button className="text-sm text-accent-blue hover:underline">
                      Посмотреть все
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* User Menu (placeholder) */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-dark-bg-hover cursor-pointer transition-colors">
            <div className="w-8 h-8 rounded-full bg-accent-blue/20 flex items-center justify-center">
              <span className="text-sm font-medium text-accent-blue">VL</span>
            </div>
            <ChevronDown className="w-4 h-4 text-dark-text-secondary" />
          </div>
        </div>
      </div>
    </header>
  );
};
