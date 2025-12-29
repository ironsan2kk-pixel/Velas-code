/**
 * VELAS - Header Component
 */

import React, { useState } from 'react';
import { StatusIndicator, Badge } from '@/components/ui';
import { useDashboardSummary } from '@/hooks/useApi';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useThemeStore } from '@/stores';
import { Sun, Moon, Bell, Wifi, WifiOff, ChevronDown, Menu } from 'lucide-react';

interface HeaderProps {
  onMenuClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const { data: summary, isLoading, isError } = useDashboardSummary();
  const { isConnected } = useWebSocket();
  const { isDark, toggleTheme } = useThemeStore();

  const notifications = [
    { id: '1', type: 'success' as const, title: 'System Ready', message: 'VELAS initialized', time: 'now' },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-dark-bg-secondary border-b border-dark-border z-30 lg:left-60">
      <div className="h-full flex items-center justify-between px-4 lg:px-6">
        {/* Left */}
        <div className="flex items-center gap-4">
          <button onClick={onMenuClick} className="lg:hidden p-2 rounded-lg hover:bg-dark-bg-hover text-dark-text-secondary">
            <Menu className="w-5 h-5" />
          </button>

          <StatusIndicator
            status={isError ? 'offline' : isLoading ? 'degraded' : 'online'}
            label={isError ? 'ERROR' : isLoading ? 'LOADING' : 'ONLINE'}
            pulse={!isError && !isLoading}
          />

          <div className="hidden sm:flex items-center gap-2 text-dark-text-muted">
            {isConnected ? <Wifi className="w-4 h-4 text-accent-green" /> : <WifiOff className="w-4 h-4" />}
            <span className="text-sm">WS {isConnected ? 'On' : 'Off'}</span>
          </div>

          {summary && (
            <div className="hidden md:flex items-center gap-4 text-sm">
              <span className="text-dark-text-muted">Positions: <span className="text-dark-text-primary font-medium">{summary.open_positions || 0}</span></span>
              <span className="text-dark-text-muted">P&L: <span className={`font-medium ${(summary.total_pnl_percent || 0) >= 0 ? 'text-profit' : 'text-loss'}`}>{(summary.total_pnl_percent || 0) >= 0 ? '+' : ''}{(summary.total_pnl_percent || 0).toFixed(2)}%</span></span>
            </div>
          )}
        </div>

        {/* Right */}
        <div className="flex items-center gap-2">
          <button onClick={toggleTheme} className="p-2 rounded-lg hover:bg-dark-bg-hover text-dark-text-secondary" title={isDark ? 'Light' : 'Dark'}>
            {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>

          <div className="relative">
            <button onClick={() => setShowNotifications(!showNotifications)} className="relative p-2 rounded-lg hover:bg-dark-bg-hover text-dark-text-secondary">
              <Bell className="w-5 h-5" />
              {notifications.length > 0 && <span className="absolute top-1 right-1 w-2 h-2 bg-accent-red rounded-full" />}
            </button>

            {showNotifications && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowNotifications(false)} />
                <div className="absolute top-12 right-0 w-80 bg-dark-bg-card border border-dark-border rounded-lg shadow-lg z-50">
                  <div className="p-4 border-b border-dark-border flex justify-between">
                    <h3 className="font-medium text-dark-text-primary">Notifications</h3>
                    <Badge variant="secondary" size="sm">{notifications.length}</Badge>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    {notifications.map((n) => (
                      <div key={n.id} className="p-4 border-b border-dark-border hover:bg-dark-bg-hover">
                        <p className="font-medium text-dark-text-primary text-sm">{n.title}</p>
                        <p className="text-sm text-dark-text-secondary mt-1">{n.message}</p>
                        <p className="text-xs text-dark-text-muted mt-1">{n.time}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>

          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-dark-bg-hover cursor-pointer">
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
