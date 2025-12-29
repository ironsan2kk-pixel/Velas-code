/**
 * VELAS - Main Layout
 * Основная разметка приложения с роутингом
 */

import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { cn } from '@/utils/cn';

// Pages
import Dashboard from '@/pages/Dashboard';
import Positions from '@/pages/Positions';
import History from '@/pages/History';
import Signals from '@/pages/Signals';
import Pairs from '@/pages/Pairs';
import Analytics from '@/pages/Analytics';
import Backtest from '@/pages/Backtest';
import Settings from '@/pages/Settings';
import Alerts from '@/pages/Alerts';
import System from '@/pages/System';

export const MainLayout: React.FC = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    // В реальном приложении здесь будет переключение Tailwind dark mode
    // document.documentElement.classList.toggle('dark', newTheme === 'dark');
  };

  return (
    <div className="min-h-screen bg-dark-bg-primary">
      <Sidebar collapsed={sidebarCollapsed} onToggle={toggleSidebar} />
      
      <div
        className={cn(
          'transition-all duration-300',
          sidebarCollapsed ? 'ml-20' : 'ml-64'
        )}
      >
        <Header theme={theme} onThemeToggle={toggleTheme} />
        
        <main className="mt-16 p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/positions" element={<Positions />} />
            <Route path="/history" element={<History />} />
            <Route path="/signals" element={<Signals />} />
            <Route path="/pairs" element={<Pairs />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/backtest" element={<Backtest />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/system" element={<System />} />
            
            {/* 404 */}
            <Route
              path="*"
              element={
                <div className="flex items-center justify-center h-96">
                  <div className="text-center">
                    <h1 className="text-6xl font-bold text-dark-text-primary mb-4">404</h1>
                    <p className="text-xl text-dark-text-secondary">Страница не найдена</p>
                  </div>
                </div>
              }
            />
          </Routes>
        </main>
      </div>
    </div>
  );
};
