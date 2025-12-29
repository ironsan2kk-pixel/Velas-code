import React from 'react';
import { Link } from 'react-router-dom';
import { cn } from '@/utils';
import { useThemeStore, useSettingsStore } from '@/stores';
import { useSystemStatus } from '@/hooks';
import { StatusIndicator } from '@/components/ui';
import {
  Menu,
  Sun,
  Moon,
  Bell,
  Settings,
  Activity,
} from 'lucide-react';

interface HeaderProps {
  onMenuClick: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const { theme, toggleTheme } = useThemeStore();
  const { data: systemStatus } = useSystemStatus();

  const getStatusType = () => {
    switch (systemStatus?.overall_status) {
      case 'online':
        return 'online';
      case 'offline':
        return 'offline';
      case 'degraded':
      case 'maintenance':
        return 'warning';
      default:
        return 'offline';
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-40 h-16 bg-dark-bg-secondary border-b border-dark-border">
      <div className="h-full px-4 flex items-center justify-between">
        {/* Left section */}
        <div className="flex items-center gap-4">
          {/* Mobile menu button */}
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-md hover:bg-dark-bg-tertiary transition-colors"
            aria-label="Меню"
          >
            <Menu className="w-5 h-5 text-dark-text-secondary" />
          </button>

          {/* Logo */}
          <Link to="/" className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent-blue flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-lg font-bold text-dark-text-primary leading-tight">
                VELAS
              </h1>
              <p className="text-xs text-dark-text-muted -mt-0.5">
                Trading System
              </p>
            </div>
          </Link>
        </div>

        {/* Center section - System Status */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-md bg-dark-bg-tertiary">
          <StatusIndicator
            status={getStatusType()}
            size="sm"
          />
          <span className="text-sm text-dark-text-secondary">
            {systemStatus?.overall_status === 'online'
              ? 'Система работает'
              : systemStatus?.overall_status === 'offline'
              ? 'Система отключена'
              : systemStatus?.overall_status === 'degraded'
              ? 'Деградация'
              : 'Загрузка...'}
          </span>
        </div>

        {/* Right section */}
        <div className="flex items-center gap-2">
          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-md hover:bg-dark-bg-tertiary transition-colors"
            aria-label={theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
          >
            {theme === 'dark' ? (
              <Sun className="w-5 h-5 text-dark-text-secondary" />
            ) : (
              <Moon className="w-5 h-5 text-dark-text-secondary" />
            )}
          </button>

          {/* Notifications */}
          <button
            className="p-2 rounded-md hover:bg-dark-bg-tertiary transition-colors relative"
            aria-label="Уведомления"
          >
            <Bell className="w-5 h-5 text-dark-text-secondary" />
            {/* Notification badge */}
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-accent-red rounded-full" />
          </button>

          {/* Settings (desktop only) */}
          <Link
            to="/settings"
            className="hidden sm:flex p-2 rounded-md hover:bg-dark-bg-tertiary transition-colors"
            aria-label="Настройки"
          >
            <Settings className="w-5 h-5 text-dark-text-secondary" />
          </Link>

          {/* Mobile status indicator */}
          <div className="md:hidden">
            <StatusIndicator status={getStatusType()} size="md" />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
