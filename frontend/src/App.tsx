import React, { Suspense, lazy, useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Header, Sidebar, BottomNav } from '@/components/layout';
import { ToastContainer, PageSpinner } from '@/components/ui';
import { useThemeStore } from '@/stores';
import { useSettingsStore } from '@/stores';
import { cn } from '@/utils';

// Lazy load pages for code splitting
const DashboardPage = lazy(() => import('@/pages/Dashboard'));
const PositionsPage = lazy(() => import('@/pages/Positions'));
const HistoryPage = lazy(() => import('@/pages/History'));
const SignalsPage = lazy(() => import('@/pages/Signals'));
const PairsPage = lazy(() => import('@/pages/Pairs'));
const AnalyticsPage = lazy(() => import('@/pages/Analytics'));
const BacktestPage = lazy(() => import('@/pages/Backtest'));
const SettingsPage = lazy(() => import('@/pages/Settings'));
const AlertsPage = lazy(() => import('@/pages/Alerts'));
const SystemPage = lazy(() => import('@/pages/System'));

// React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

// Layout wrapper component
const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { sidebarCollapsed, setSidebarCollapsed } = useSettingsStore();
  const { isDark } = useThemeStore();

  // Apply theme class to document
  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    document.documentElement.classList.toggle('light', !isDark);
  }, [isDark]);

  return (
    <div className={cn(
      'min-h-screen',
      isDark ? 'bg-dark-bg-primary text-dark-text-primary' : 'bg-light-bg-primary text-light-text-primary'
    )}>
      <Header onMenuClick={() => setSidebarOpen(true)} />
      
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      
      <main
        className={cn(
          'pt-16 pb-20 lg:pb-6 transition-all duration-300',
          // Sidebar offset on desktop
          sidebarCollapsed ? 'lg:pl-16' : 'lg:pl-60'
        )}
      >
        <div className="p-4 lg:p-6 max-w-[1800px] mx-auto">
          {children}
        </div>
      </main>
      
      <BottomNav />
      <ToastContainer />
    </div>
  );
};

// Main App component
const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppLayout>
          <Suspense fallback={<PageSpinner />}>
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/positions" element={<PositionsPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/signals" element={<SignalsPage />} />
              <Route path="/pairs" element={<PairsPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/backtest" element={<BacktestPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/alerts" element={<AlertsPage />} />
              <Route path="/system" element={<SystemPage />} />
              {/* Fallback route */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </AppLayout>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
