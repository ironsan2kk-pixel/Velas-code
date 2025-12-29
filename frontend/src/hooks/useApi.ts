/**
 * VELAS Trading System - API Hooks
 * React Query hooks для всех API endpoints
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { get, post, put, buildQueryString } from '@/api/client';
import type {
  ApiResponse,
  PaginatedResponse,
  DashboardSummary,
  DashboardMetrics,
  EquityPoint,
  Position,
  PositionDetail,
  Trade,
  HistoryStats,
  Signal,
  Pair,
  PairDetail,
  OHLCV,
  EquityCurveData,
  DrawdownData,
  MonthlyStats,
  PairAnalytics,
  CorrelationData,
  BacktestConfig,
  BacktestResult,
  BacktestListItem,
  SystemSettings,
  Preset,
  AlertSettings,
  Alert,
  SystemStatus,
  LogEntry,
} from '@/types';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const queryKeys = {
  // Dashboard
  dashboardSummary: ['dashboard', 'summary'] as const,
  dashboardMetrics: ['dashboard', 'metrics'] as const,
  dashboardChart: (period: string) => ['dashboard', 'chart', period] as const,
  
  // Positions
  positions: (status?: string) => ['positions', status] as const,
  position: (id: string) => ['position', id] as const,
  
  // History
  history: (page: number, pageSize: number, filters?: any) => ['history', page, pageSize, filters] as const,
  historyStats: ['history', 'stats'] as const,
  
  // Signals
  signals: (page: number, pageSize: number, filters?: any) => ['signals', page, pageSize, filters] as const,
  signalsPending: ['signals', 'pending'] as const,
  signal: (id: string) => ['signal', id] as const,
  
  // Pairs
  pairs: ['pairs'] as const,
  pair: (symbol: string) => ['pair', symbol] as const,
  pairChart: (symbol: string, timeframe: string, period: string) => ['pair', symbol, 'chart', timeframe, period] as const,
  pairSignals: (symbol: string) => ['pair', symbol, 'signals'] as const,
  
  // Analytics
  analyticsEquity: (period?: string) => ['analytics', 'equity', period] as const,
  analyticsDrawdown: (period?: string) => ['analytics', 'drawdown', period] as const,
  analyticsMonthly: ['analytics', 'monthly'] as const,
  analyticsPairs: ['analytics', 'pairs'] as const,
  analyticsCorrelation: ['analytics', 'correlation'] as const,
  
  // Backtest
  backtestResults: ['backtest', 'results'] as const,
  backtestResult: (id: string) => ['backtest', 'result', id] as const,
  backtestStatus: (id: string) => ['backtest', 'status', id] as const,
  
  // Settings
  settings: ['settings'] as const,
  presets: ['settings', 'presets'] as const,
  preset: (id: string) => ['settings', 'preset', id] as const,
  
  // Alerts
  alertSettings: ['alerts', 'settings'] as const,
  alertHistory: (page: number, pageSize: number) => ['alerts', 'history', page, pageSize] as const,
  
  // System
  systemStatus: ['system', 'status'] as const,
  systemLogs: (limit?: number, level?: string) => ['system', 'logs', limit, level] as const,
};

// ============================================================================
// DASHBOARD
// ============================================================================

export const useDashboardSummary = (options?: UseQueryOptions<DashboardSummary>) => {
  return useQuery<DashboardSummary>({
    queryKey: queryKeys.dashboardSummary,
    queryFn: () => get('/dashboard/summary'),
    refetchInterval: 5000, // обновляем каждые 5 секунд
    ...options,
  });
};

export const useDashboardMetrics = (options?: UseQueryOptions<DashboardMetrics>) => {
  return useQuery<DashboardMetrics>({
    queryKey: queryKeys.dashboardMetrics,
    queryFn: () => get('/dashboard/metrics'),
    refetchInterval: 10000,
    ...options,
  });
};

export const useDashboardChart = (period: string = '1w', options?: UseQueryOptions<EquityPoint[]>) => {
  return useQuery<EquityPoint[]>({
    queryKey: queryKeys.dashboardChart(period),
    queryFn: () => get(`/dashboard/chart${buildQueryString({ period })}`),
    refetchInterval: 30000,
    ...options,
  });
};

// ============================================================================
// POSITIONS
// ============================================================================

export const usePositions = (status?: 'open' | 'closed', options?: UseQueryOptions<Position[]>) => {
  return useQuery<Position[]>({
    queryKey: queryKeys.positions(status),
    queryFn: () => get(`/positions${buildQueryString({ status })}`),
    refetchInterval: 3000,
    ...options,
  });
};

export const usePosition = (id: string, options?: UseQueryOptions<PositionDetail>) => {
  return useQuery<PositionDetail>({
    queryKey: queryKeys.position(id),
    queryFn: () => get(`/positions/${id}`),
    enabled: !!id,
    refetchInterval: 5000,
    ...options,
  });
};

export const useClosePosition = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => post(`/positions/${id}/close`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.positions() });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboardSummary });
    },
  });
};

// ============================================================================
// HISTORY
// ============================================================================

export const useHistory = (
  page: number = 1,
  pageSize: number = 20,
  filters?: any,
  options?: UseQueryOptions<PaginatedResponse<Trade>>
) => {
  return useQuery<PaginatedResponse<Trade>>({
    queryKey: queryKeys.history(page, pageSize, filters),
    queryFn: () => get(`/history${buildQueryString({ page, page_size: pageSize, ...filters })}`),
    ...options,
  });
};

export const useHistoryStats = (options?: UseQueryOptions<HistoryStats>) => {
  return useQuery<HistoryStats>({
    queryKey: queryKeys.historyStats,
    queryFn: () => get('/history/stats'),
    ...options,
  });
};

export const useExportHistory = () => {
  return useMutation({
    mutationFn: (filters?: any) => get(`/history/export${buildQueryString(filters || {})}`, { responseType: 'blob' }),
  });
};

// ============================================================================
// SIGNALS
// ============================================================================

export const useSignals = (
  page: number = 1,
  pageSize: number = 20,
  filters?: any,
  options?: UseQueryOptions<PaginatedResponse<Signal>>
) => {
  return useQuery<PaginatedResponse<Signal>>({
    queryKey: queryKeys.signals(page, pageSize, filters),
    queryFn: () => get(`/signals${buildQueryString({ page, page_size: pageSize, ...filters })}`),
    refetchInterval: 5000,
    ...options,
  });
};

export const usePendingSignals = (options?: UseQueryOptions<Signal[]>) => {
  return useQuery<Signal[]>({
    queryKey: queryKeys.signalsPending,
    queryFn: () => get('/signals/pending'),
    refetchInterval: 3000,
    ...options,
  });
};

export const useSignal = (id: string, options?: UseQueryOptions<Signal>) => {
  return useQuery<Signal>({
    queryKey: queryKeys.signal(id),
    queryFn: () => get(`/signals/${id}`),
    enabled: !!id,
    ...options,
  });
};

// ============================================================================
// PAIRS
// ============================================================================

export const usePairs = (options?: UseQueryOptions<Pair[]>) => {
  return useQuery<Pair[]>({
    queryKey: queryKeys.pairs,
    queryFn: () => get('/pairs'),
    refetchInterval: 10000,
    ...options,
  });
};

export const usePair = (symbol: string, options?: UseQueryOptions<PairDetail>) => {
  return useQuery<PairDetail>({
    queryKey: queryKeys.pair(symbol),
    queryFn: () => get(`/pairs/${symbol}`),
    enabled: !!symbol,
    refetchInterval: 5000,
    ...options,
  });
};

export const usePairChart = (
  symbol: string,
  timeframe: string = '1h',
  period: string = '1w',
  options?: UseQueryOptions<OHLCV[]>
) => {
  return useQuery<OHLCV[]>({
    queryKey: queryKeys.pairChart(symbol, timeframe, period),
    queryFn: () => get(`/pairs/${symbol}/chart${buildQueryString({ timeframe, period })}`),
    enabled: !!symbol,
    refetchInterval: 10000,
    ...options,
  });
};

export const usePairSignals = (symbol: string, options?: UseQueryOptions<Signal[]>) => {
  return useQuery<Signal[]>({
    queryKey: queryKeys.pairSignals(symbol),
    queryFn: () => get(`/pairs/${symbol}/signals`),
    enabled: !!symbol,
    refetchInterval: 5000,
    ...options,
  });
};

// ============================================================================
// ANALYTICS
// ============================================================================

export const useAnalyticsEquity = (period?: string, options?: UseQueryOptions<EquityCurveData[]>) => {
  return useQuery<EquityCurveData[]>({
    queryKey: queryKeys.analyticsEquity(period),
    queryFn: () => get(`/analytics/equity${buildQueryString({ period: period || 'all' })}`),
    ...options,
  });
};

export const useAnalyticsDrawdown = (period?: string, options?: UseQueryOptions<DrawdownData[]>) => {
  return useQuery<DrawdownData[]>({
    queryKey: queryKeys.analyticsDrawdown(period),
    queryFn: () => get(`/analytics/drawdown${buildQueryString({ period: period || 'all' })}`),
    ...options,
  });
};

export const useAnalyticsMonthly = (options?: UseQueryOptions<MonthlyStats[]>) => {
  return useQuery<MonthlyStats[]>({
    queryKey: queryKeys.analyticsMonthly,
    queryFn: () => get('/analytics/monthly'),
    ...options,
  });
};

export const useAnalyticsPairs = (options?: UseQueryOptions<PairAnalytics[]>) => {
  return useQuery<PairAnalytics[]>({
    queryKey: queryKeys.analyticsPairs,
    queryFn: () => get('/analytics/pairs'),
    ...options,
  });
};

export const useAnalyticsCorrelation = (options?: UseQueryOptions<CorrelationData>) => {
  return useQuery<CorrelationData>({
    queryKey: queryKeys.analyticsCorrelation,
    queryFn: () => get('/analytics/correlation'),
    ...options,
  });
};

// ============================================================================
// BACKTEST
// ============================================================================

export const useBacktestResults = (options?: UseQueryOptions<BacktestListItem[]>) => {
  return useQuery<BacktestListItem[]>({
    queryKey: queryKeys.backtestResults,
    queryFn: () => get('/backtest/results'),
    ...options,
  });
};

export const useBacktestResult = (id: string, options?: UseQueryOptions<BacktestResult>) => {
  return useQuery<BacktestResult>({
    queryKey: queryKeys.backtestResult(id),
    queryFn: () => get(`/backtest/results/${id}`),
    enabled: !!id,
    ...options,
  });
};

export const useBacktestStatus = (id: string, options?: UseQueryOptions<BacktestResult>) => {
  return useQuery<BacktestResult>({
    queryKey: queryKeys.backtestStatus(id),
    queryFn: () => get(`/backtest/status/${id}`),
    enabled: !!id,
    refetchInterval: (data) => {
      // Останавливаем polling если тест завершён
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return 2000; // каждые 2 секунды
    },
    ...options,
  });
};

export const useRunBacktest = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (config: BacktestConfig) => post('/backtest/run', config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.backtestResults });
    },
  });
};

// ============================================================================
// SETTINGS
// ============================================================================

export const useSettings = (options?: UseQueryOptions<SystemSettings>) => {
  return useQuery<SystemSettings>({
    queryKey: queryKeys.settings,
    queryFn: () => get('/settings'),
    ...options,
  });
};

export const useUpdateSettings = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (settings: Partial<SystemSettings>) => put('/settings', settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settings });
    },
  });
};

export const usePresets = (options?: UseQueryOptions<Preset[]>) => {
  return useQuery<Preset[]>({
    queryKey: queryKeys.presets,
    queryFn: () => get('/settings/presets'),
    ...options,
  });
};

export const useUpdatePreset = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Preset> }) => put(`/settings/presets/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.presets });
    },
  });
};

// ============================================================================
// ALERTS
// ============================================================================

export const useAlertSettings = (options?: UseQueryOptions<AlertSettings>) => {
  return useQuery<AlertSettings>({
    queryKey: queryKeys.alertSettings,
    queryFn: () => get('/alerts/settings'),
    ...options,
  });
};

export const useUpdateAlertSettings = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (settings: Partial<AlertSettings>) => put('/alerts/settings', settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alertSettings });
    },
  });
};

export const useAlertHistory = (
  page: number = 1,
  pageSize: number = 20,
  options?: UseQueryOptions<PaginatedResponse<Alert>>
) => {
  return useQuery<PaginatedResponse<Alert>>({
    queryKey: queryKeys.alertHistory(page, pageSize),
    queryFn: () => get(`/alerts/history${buildQueryString({ page, page_size: pageSize })}`),
    refetchInterval: 10000,
    ...options,
  });
};

// ============================================================================
// SYSTEM
// ============================================================================

export const useSystemStatus = (options?: UseQueryOptions<SystemStatus>) => {
  return useQuery<SystemStatus>({
    queryKey: queryKeys.systemStatus,
    queryFn: () => get('/system/status'),
    refetchInterval: 5000,
    ...options,
  });
};

export const useSystemLogs = (
  limit: number = 100,
  level?: string,
  options?: UseQueryOptions<LogEntry[]>
) => {
  return useQuery<LogEntry[]>({
    queryKey: queryKeys.systemLogs(limit, level),
    queryFn: () => get(`/system/logs${buildQueryString({ limit, level })}`),
    refetchInterval: 10000,
    ...options,
  });
};

export const useDownloadLogs = () => {
  return useMutation({
    mutationFn: () => get('/system/logs/download', { responseType: 'blob' }),
  });
};

export const useRestartComponent = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (component: string) => post(`/system/restart`, { component }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.systemStatus });
    },
  });
};
