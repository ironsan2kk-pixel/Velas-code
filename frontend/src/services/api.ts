import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  ApiResponse,
  PaginatedResponse,
  DashboardSummary,
  DashboardMetrics,
  Position,
  Trade,
  HistoryStats,
  Signal,
  Pair,
  PairDetail,
  EquityPoint,
  MonthlyStats,
  PairAnalytics,
  CorrelationData,
  BacktestConfig,
  BacktestResult,
  SystemSettings,
  TradingSettings,
  SystemStatus,
  LogEntry,
  Preset,
  OHLCV,
} from '@/types';

// Combined settings type
export interface AllSettings {
  system: SystemSettings;
  trading: TradingSettings;
}

// Position summary type
export interface PositionSummary {
  total_positions: number;
  open_positions: number;
  total_pnl: number;
  total_pnl_percent: number;
}

// ===== API Client Configuration =====

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Redirect to login or refresh token
      console.error('Unauthorized request');
    } else if (error.response?.status === 500) {
      console.error('Server error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Helper to extract data from ApiResponse
function extractData<T>(response: { data: ApiResponse<T> }): T {
  if (!response.data.data) {
    throw new Error('API response missing data');
  }
  return response.data.data;
}

// ===== API Functions =====

// --- Health & Info ---

export async function getHealth(): Promise<{ status: string; timestamp: string }> {
  const response = await api.get('/health');
  return response.data;
}

export async function getVersion(): Promise<{ version: string; build: string }> {
  const response = await api.get('/version');
  return response.data;
}

// --- Dashboard ---

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await api.get<ApiResponse<DashboardSummary>>('/dashboard/summary');
  return extractData(response);
}

export async function getDashboardMetrics(): Promise<DashboardMetrics> {
  const response = await api.get<ApiResponse<DashboardMetrics>>('/dashboard/metrics');
  return extractData(response);
}

export async function getDashboardChart(period: '1d' | '1w' | '1m' | '3m' = '1w'): Promise<EquityPoint[]> {
  const response = await api.get<ApiResponse<EquityPoint[]>>('/dashboard/chart', {
    params: { period },
  });
  return extractData(response);
}

// --- Positions ---

export async function getPositions(status?: 'open' | 'closed'): Promise<Position[]> {
  const response = await api.get<ApiResponse<Position[]>>('/positions', {
    params: { status },
  });
  return extractData(response);
}

export async function getPosition(id: number): Promise<Position> {
  const response = await api.get<ApiResponse<Position>>(`/positions/${id}`);
  return extractData(response);
}

export async function closePosition(id: number): Promise<Position> {
  const response = await api.post<ApiResponse<Position>>(`/positions/${id}/close`);
  return extractData(response);
}

export async function getPositionsSummary(): Promise<PositionSummary> {
  const response = await api.get<ApiResponse<PositionSummary>>('/positions/summary');
  return extractData(response);
}

// --- History ---

export async function getHistory(
  page: number = 1,
  pageSize: number = 20,
  symbol?: string,
  side?: 'LONG' | 'SHORT'
): Promise<PaginatedResponse<Trade>> {
  const response = await api.get<PaginatedResponse<Trade>>('/history', {
    params: { page, page_size: pageSize, symbol, side },
  });
  return response.data;
}

export async function getHistoryStats(period?: '7d' | '30d' | '90d' | 'all'): Promise<HistoryStats> {
  const response = await api.get<ApiResponse<HistoryStats>>('/history/stats', {
    params: { period },
  });
  return extractData(response);
}

export async function exportHistory(format: 'csv' | 'xlsx' = 'csv'): Promise<Blob> {
  const response = await api.get('/history/export', {
    params: { format },
    responseType: 'blob',
  });
  return response.data;
}

// --- Signals ---

export async function getSignals(
  page: number = 1,
  pageSize: number = 20,
  status?: string
): Promise<PaginatedResponse<Signal>> {
  const response = await api.get<PaginatedResponse<Signal>>('/signals', {
    params: { page, page_size: pageSize, status },
  });
  return response.data;
}

export async function getPendingSignals(): Promise<Signal[]> {
  const response = await api.get<ApiResponse<Signal[]>>('/signals/pending');
  return extractData(response);
}

export async function getSignal(id: number): Promise<Signal> {
  const response = await api.get<ApiResponse<Signal>>(`/signals/${id}`);
  return extractData(response);
}

// --- Pairs ---

export async function getPairs(): Promise<Pair[]> {
  const response = await api.get<ApiResponse<Pair[]>>('/pairs');
  return extractData(response);
}

export async function getPair(symbol: string): Promise<PairDetail> {
  const response = await api.get<ApiResponse<PairDetail>>(`/pairs/${symbol}`);
  return extractData(response);
}

export async function getPairChart(
  symbol: string,
  timeframe: '30m' | '1h' | '2h' | '4h' | '1d' = '1h',
  limit: number = 100
): Promise<OHLCV[]> {
  const response = await api.get<ApiResponse<OHLCV[]>>(`/pairs/${symbol}/chart`, {
    params: { timeframe, limit },
  });
  return extractData(response);
}

export async function getPairSignals(symbol: string, limit: number = 10): Promise<Signal[]> {
  const response = await api.get<ApiResponse<Signal[]>>(`/pairs/${symbol}/signals`, {
    params: { limit },
  });
  return extractData(response);
}

// --- Analytics ---

export async function getEquityCurve(period: '1w' | '1m' | '3m' | '6m' | '1y' = '1m'): Promise<EquityPoint[]> {
  const response = await api.get<ApiResponse<EquityPoint[]>>('/analytics/equity', {
    params: { period },
  });
  return extractData(response);
}

export async function getDrawdownChart(period: '1w' | '1m' | '3m' | '6m' | '1y' = '1m'): Promise<EquityPoint[]> {
  const response = await api.get<ApiResponse<EquityPoint[]>>('/analytics/drawdown', {
    params: { period },
  });
  return extractData(response);
}

export async function getMonthlyStats(): Promise<MonthlyStats[]> {
  const response = await api.get<ApiResponse<MonthlyStats[]>>('/analytics/monthly');
  return extractData(response);
}

export async function getPairAnalytics(): Promise<PairAnalytics[]> {
  const response = await api.get<ApiResponse<PairAnalytics[]>>('/analytics/pairs');
  return extractData(response);
}

export async function getCorrelationMatrix(): Promise<CorrelationData> {
  const response = await api.get<ApiResponse<CorrelationData>>('/analytics/correlation');
  return extractData(response);
}

// --- Backtest ---

export async function runBacktest(config: BacktestConfig): Promise<{ id: string }> {
  const response = await api.post<ApiResponse<{ id: string }>>('/backtest/run', config);
  return extractData(response);
}

export async function getBacktestStatus(id: string): Promise<BacktestResult> {
  const response = await api.get<ApiResponse<BacktestResult>>(`/backtest/status/${id}`);
  return extractData(response);
}

export async function getBacktestResults(): Promise<BacktestResult[]> {
  const response = await api.get<ApiResponse<BacktestResult[]>>('/backtest/results');
  return extractData(response);
}

export async function getBacktestResult(id: string): Promise<BacktestResult> {
  const response = await api.get<ApiResponse<BacktestResult>>(`/backtest/results/${id}`);
  return extractData(response);
}

// --- Settings ---

export async function getSettings(): Promise<AllSettings> {
  const response = await api.get<ApiResponse<AllSettings>>('/settings');
  return extractData(response);
}

export async function updateSettings(settings: Partial<AllSettings>): Promise<AllSettings> {
  const response = await api.put<ApiResponse<AllSettings>>('/settings', settings);
  return extractData(response);
}

export async function getPresets(): Promise<Preset[]> {
  const response = await api.get<ApiResponse<Preset[]>>('/settings/presets');
  return extractData(response);
}

export async function getPreset(id: string): Promise<Preset> {
  const response = await api.get<ApiResponse<Preset>>(`/settings/presets/${id}`);
  return extractData(response);
}

export async function updatePreset(id: string, preset: Partial<Preset>): Promise<Preset> {
  const response = await api.put<ApiResponse<Preset>>(`/settings/presets/${id}`, preset);
  return extractData(response);
}

// --- System ---

export async function getSystemStatus(): Promise<SystemStatus> {
  const response = await api.get<ApiResponse<SystemStatus>>('/system/status');
  return extractData(response);
}

export async function getSystemLogs(
  level?: string,
  component?: string,
  limit: number = 100
): Promise<LogEntry[]> {
  const response = await api.get<ApiResponse<LogEntry[]>>('/system/logs', {
    params: { level, component, limit },
  });
  return extractData(response);
}

export async function downloadLogs(): Promise<Blob> {
  const response = await api.get('/system/logs/download', {
    responseType: 'blob',
  });
  return response.data;
}

export async function pauseTrading(): Promise<{ success: boolean }> {
  const response = await api.post<ApiResponse<{ success: boolean }>>('/system/pause');
  return extractData(response);
}

export async function resumeTrading(): Promise<{ success: boolean }> {
  const response = await api.post<ApiResponse<{ success: boolean }>>('/system/resume');
  return extractData(response);
}

export async function restartComponent(component: string): Promise<{ success: boolean }> {
  const response = await api.post<ApiResponse<{ success: boolean }>>('/system/restart', { component });
  return extractData(response);
}

export default api;
