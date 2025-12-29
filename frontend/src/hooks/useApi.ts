import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '@/services/api';
import type {
  Position,
  Signal,
  TradeHistory,
  Pair,
  PairDetail,
  BacktestConfig,
  AllSettings,
} from '@/types';

// ===== Query Keys =====

export const queryKeys = {
  // Dashboard
  dashboardSummary: ['dashboard', 'summary'] as const,
  dashboardMetrics: ['dashboard', 'metrics'] as const,
  dashboardChart: (period: string) => ['dashboard', 'chart', period] as const,
  
  // Positions
  positions: (status?: string) => ['positions', { status }] as const,
  position: (id: number) => ['positions', id] as const,
  positionsSummary: ['positions', 'summary'] as const,
  
  // History
  history: (page: number, pageSize: number, symbol?: string, side?: string) =>
    ['history', { page, pageSize, symbol, side }] as const,
  historyStats: (period?: string) => ['history', 'stats', period] as const,
  
  // Signals
  signals: (page: number, pageSize: number, status?: string) =>
    ['signals', { page, pageSize, status }] as const,
  pendingSignals: ['signals', 'pending'] as const,
  signal: (id: number) => ['signals', id] as const,
  
  // Pairs
  pairs: ['pairs'] as const,
  pair: (symbol: string) => ['pairs', symbol] as const,
  pairChart: (symbol: string, timeframe: string) => ['pairs', symbol, 'chart', timeframe] as const,
  pairSignals: (symbol: string) => ['pairs', symbol, 'signals'] as const,
  
  // Analytics
  equityCurve: (period: string) => ['analytics', 'equity', period] as const,
  drawdown: (period: string) => ['analytics', 'drawdown', period] as const,
  monthlyStats: ['analytics', 'monthly'] as const,
  pairAnalytics: ['analytics', 'pairs'] as const,
  correlationMatrix: ['analytics', 'correlation'] as const,
  
  // Backtest
  backtestResults: ['backtest', 'results'] as const,
  backtestResult: (id: string) => ['backtest', 'results', id] as const,
  backtestStatus: (id: string) => ['backtest', 'status', id] as const,
  
  // Settings
  settings: ['settings'] as const,
  presets: ['settings', 'presets'] as const,
  preset: (id: string) => ['settings', 'presets', id] as const,
  
  // System
  systemStatus: ['system', 'status'] as const,
  systemLogs: (level?: string, component?: string) =>
    ['system', 'logs', { level, component }] as const,
};

// ===== Dashboard Hooks =====

export function useDashboardSummary() {
  return useQuery({
    queryKey: queryKeys.dashboardSummary,
    queryFn: api.getDashboardSummary,
    refetchInterval: 5000, // Refresh every 5 seconds
  });
}

export function useDashboardMetrics() {
  return useQuery({
    queryKey: queryKeys.dashboardMetrics,
    queryFn: api.getDashboardMetrics,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

export function useDashboardChart(period: '1d' | '1w' | '1m' | '3m' = '1w') {
  return useQuery({
    queryKey: queryKeys.dashboardChart(period),
    queryFn: () => api.getDashboardChart(period),
  });
}

// ===== Position Hooks =====

export function usePositions(status?: 'open' | 'closed') {
  return useQuery({
    queryKey: queryKeys.positions(status),
    queryFn: () => api.getPositions(status),
    refetchInterval: 5000,
  });
}

export function usePosition(id: number) {
  return useQuery({
    queryKey: queryKeys.position(id),
    queryFn: () => api.getPosition(id),
    enabled: id > 0,
  });
}

export function useClosePosition() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => api.closePosition(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

// ===== History Hooks =====

export function useHistory(
  page: number = 1,
  pageSize: number = 20,
  symbol?: string,
  side?: 'LONG' | 'SHORT'
) {
  return useQuery({
    queryKey: queryKeys.history(page, pageSize, symbol, side),
    queryFn: () => api.getHistory(page, pageSize, symbol, side),
  });
}

export function useHistoryStats(period?: '7d' | '30d' | '90d' | 'all') {
  return useQuery({
    queryKey: queryKeys.historyStats(period),
    queryFn: () => api.getHistoryStats(period),
  });
}

// ===== Signal Hooks =====

export function useSignals(page: number = 1, pageSize: number = 20, status?: string) {
  return useQuery({
    queryKey: queryKeys.signals(page, pageSize, status),
    queryFn: () => api.getSignals(page, pageSize, status),
  });
}

export function usePendingSignals() {
  return useQuery({
    queryKey: queryKeys.pendingSignals,
    queryFn: api.getPendingSignals,
    refetchInterval: 5000,
  });
}

// ===== Pair Hooks =====

export function usePairs() {
  return useQuery({
    queryKey: queryKeys.pairs,
    queryFn: api.getPairs,
    refetchInterval: 10000,
  });
}

export function usePair(symbol: string) {
  return useQuery({
    queryKey: queryKeys.pair(symbol),
    queryFn: () => api.getPair(symbol),
    enabled: !!symbol,
    refetchInterval: 5000,
  });
}

export function usePairChart(
  symbol: string,
  timeframe: '30m' | '1h' | '2h' | '4h' | '1d' = '1h'
) {
  return useQuery({
    queryKey: queryKeys.pairChart(symbol, timeframe),
    queryFn: () => api.getPairChart(symbol, timeframe),
    enabled: !!symbol,
    refetchInterval: 30000,
  });
}

// ===== Analytics Hooks =====

export function useEquityCurve(period: '1w' | '1m' | '3m' | '6m' | '1y' = '1m') {
  return useQuery({
    queryKey: queryKeys.equityCurve(period),
    queryFn: () => api.getEquityCurve(period),
  });
}

export function useMonthlyStats() {
  return useQuery({
    queryKey: queryKeys.monthlyStats,
    queryFn: api.getMonthlyStats,
  });
}

export function usePairAnalytics() {
  return useQuery({
    queryKey: queryKeys.pairAnalytics,
    queryFn: api.getPairAnalytics,
  });
}

export function useCorrelationMatrix() {
  return useQuery({
    queryKey: queryKeys.correlationMatrix,
    queryFn: api.getCorrelationMatrix,
  });
}

// ===== Backtest Hooks =====

export function useRunBacktest() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (config: BacktestConfig) => api.runBacktest(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.backtestResults });
    },
  });
}

export function useBacktestResults() {
  return useQuery({
    queryKey: queryKeys.backtestResults,
    queryFn: api.getBacktestResults,
  });
}

export function useBacktestStatus(id: string) {
  return useQuery({
    queryKey: queryKeys.backtestStatus(id),
    queryFn: () => api.getBacktestStatus(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.status === 'running' ? 2000 : false;
    },
  });
}

// ===== Settings Hooks =====

export function useSettings() {
  return useQuery({
    queryKey: queryKeys.settings,
    queryFn: api.getSettings,
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (settings: Partial<AllSettings>) => api.updateSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settings });
    },
  });
}

export function usePresets() {
  return useQuery({
    queryKey: queryKeys.presets,
    queryFn: api.getPresets,
  });
}

// ===== System Hooks =====

export function useSystemStatus() {
  return useQuery({
    queryKey: queryKeys.systemStatus,
    queryFn: api.getSystemStatus,
    refetchInterval: 10000,
  });
}

export function useSystemLogs(level?: string, component?: string, limit: number = 100) {
  return useQuery({
    queryKey: queryKeys.systemLogs(level, component),
    queryFn: () => api.getSystemLogs(level, component, limit),
    refetchInterval: 5000,
  });
}

export function usePauseTrading() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.pauseTrading,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.systemStatus });
    },
  });
}

export function useResumeTrading() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.resumeTrading,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.systemStatus });
    },
  });
}
