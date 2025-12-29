/**
 * VELAS - Sidebar Component
 * Боковое меню навигации
 */

import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '@/utils/cn';
import {
  LayoutDashboard,
  Wallet,
  History,
  Signal,
  Activity,
  BarChart3,
  PlayCircle,
  Settings,
  Bell,
  Server,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const menuItems = [
  { path: '/', label: 'Панель управления', icon: LayoutDashboard },
  { path: '/positions', label: 'Позиции', icon: Wallet },
  { path: '/history', label: 'История', icon: History },
  { path: '/signals', label: 'Сигналы', icon: Signal },
  { path: '/pairs', label: 'Пары', icon: Activity },
  { path: '/analytics', label: 'Аналитика', icon: BarChart3 },
  { path: '/backtest', label: 'Бэктест', icon: PlayCircle },
  { path: '/settings', label: 'Настройки', icon: Settings },
  { path: '/alerts', label: 'Уведомления', icon: Bell },
  { path: '/system', label: 'Система', icon: Server },
];

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const location = useLocation();

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-screen bg-dark-bg-secondary border-r border-dark-border transition-all duration-300 z-30',
        collapsed ? 'w-20' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-dark-border">
        {!collapsed && (
          <div>
            <h1 className="text-xl font-bold text-dark-text-primary">VELAS</h1>
            <p className="text-xs text-dark-text-muted">Trading System</p>
          </div>
        )}
        <button
          onClick={onToggle}
          className={cn(
            'p-2 rounded-lg hover:bg-dark-bg-hover text-dark-text-secondary transition-colors',
            collapsed && 'mx-auto'
          )}
        >
          {collapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <ChevronLeft className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="p-3">
        <div className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                  'hover:bg-dark-bg-hover',
                  isActive && 'bg-accent-blue/10 text-accent-blue',
                  !isActive && 'text-dark-text-secondary',
                  collapsed && 'justify-center'
                )}
                title={collapsed ? item.label : undefined}
              >
                <Icon className="w-5 h-5 shrink-0" />
                {!collapsed && (
                  <span className="font-medium">{item.label}</span>
                )}
              </NavLink>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-dark-border">
          <div className="text-xs text-dark-text-muted">
            <p>Версия 1.0.0</p>
            <p className="mt-1">© 2024 VELAS</p>
          </div>
        </div>
      )}
    </aside>
  );
};
