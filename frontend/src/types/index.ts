/**
 * VELAS Trading System - TypeScript Types
 * Все типы данных для frontend
 */

// ============================================================================
// ENUMS
// ============================================================================

export enum Side {
  LONG = 'LONG',
  SHORT = 'SHORT',
}

export enum Timeframe {
  M30 = '30m',
  H1 = '1h',
  H2 = '2h',
}

export enum VolatilityRegime {
  LOW = 'LOW',
  NORMAL = 'NORMAL',
  HIGH = 'HIGH',
}

export enum SignalStatus {
  PENDING = 'pending',
  ACTIVE = 'active',
  FILLED = 'filled',
  CANCELLED = 'cancelled',
  EXPIRED = 'expired',
}

export enum PositionStatus {
  OPEN = 'open',
  CLOSED = 'closed',
}

export enum BacktestStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum SystemComponent {
  LIVE_ENGINE = 'live_engine',
  DATA_ENGINE = 'data_engine',
  TELEGRAM_BOT = 'telegram_bot',
  DATABASE = 'database',
}

export enum ComponentStatus {
  ONLINE = 'online',
  OFFLINE = 'offline',
  ERROR = 'error',
}

export enum AlertType {
  INFO = 'info',
  SUCCESS = 'success',
  WARNING = 'warning',
  ERROR = 'error',
}

export enum AlertCategory {
  TRADING = 'trading',
  SYSTEM = 'system',
  PORTFOLIO = 'portfolio',
  PERFORMANCE = 'performance',
}

// ============================================================================
// API RESPONSES
// ============================================================================

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================================
// DASHBOARD
// ============================================================================

export interface DashboardSummary {
  status: 'live' | 'offline' | 'paused';
  total_pnl: number;
  total_pnl_percent: number;
  open_positions: number;
  total_trades: number;
  win_rate: number;
  portfolio_value: number;
  available_balance: number;
  portfolio_heat: number;
  today_signals: number;
  last_signal_time?: string;
}

export interface DashboardMetrics {
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_streak: number;
  loss_streak: number;
  best_pair: string;
  worst_pair: string;
  avg_win: number;
  avg_loss: number;
  expectancy: number;
}

export interface EquityPoint {
  timestamp: string;
  equity: number;
  drawdown: number;
  pnl: number;
}

// ============================================================================
// POSITIONS
// ============================================================================

export interface TpLevel {
  level: number;
  price: number;
  percent: number;
  quantity_percent: number;
  hit: boolean;
  hit_time?: string;
}

export interface Position {
  id: string;
  symbol: string;
  side: Side;
  timeframe: Timeframe;
  entry_price: number;
  quantity: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  stop_loss: number;
  tp_levels: TpLevel[];
  entry_time: string;
  duration_hours: number;
  volatility_regime: VolatilityRegime;
  preset_id: string;
  status: PositionStatus;
}

export interface PositionDetail extends Position {
  signals_history: Signal[];
  price_history: PricePoint[];
  trades: Trade[];
  risk_reward_ratio: number;
  max_profit_reached: number;
  max_drawdown_reached: number;
}

export interface PricePoint {
  timestamp: string;
  price: number;
  ma?: number;
}

// ============================================================================
// HISTORY
// ============================================================================

export interface Trade {
  id: string;
  symbol: string;
  side: Side;
  timeframe: Timeframe;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  pnl_percent: number;
  entry_time: string;
  exit_time: string;
  duration_hours: number;
  exit_reason: 'tp1' | 'tp2' | 'tp3' | 'tp4' | 'tp5' | 'tp6' | 'sl' | 'manual';
  tp_hits: number[];
  volatility_regime: VolatilityRegime;
  preset_id: string;
  fees: number;
  win: boolean;
}

export interface HistoryStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  total_pnl_percent: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
  best_trade: number;
  worst_trade: number;
  avg_duration_hours: number;
}

// ============================================================================
// SIGNALS
// ============================================================================

export interface Signal {
  id: string;
  symbol: string;
  side: Side;
  timeframe: Timeframe;
  entry_price: number;
  stop_loss: number;
  tp_levels: number[];
  tp_distribution: number[];
  confidence: number;
  created_at: string;
  expires_at: string;
  status: SignalStatus;
  filled_at?: string;
  cancelled_reason?: string;
  volatility_regime: VolatilityRegime;
  preset_id: string;
  velas_score: number;
  telegram_sent: boolean;
}

// ============================================================================
// PAIRS
// ============================================================================

export interface Pair {
  symbol: string;
  name: string;
  sector: string;
  current_price: number;
  price_change_24h: number;
  price_change_percent_24h: number;
  volume_24h: number;
  high_24h: number;
  low_24h: number;
  volatility_regime: VolatilityRegime;
  atr_ratio: number;
  active_position?: Side;
  signals_today: number;
  total_trades: number;
  win_rate: number;
  pnl_percent: number;
  last_signal_time?: string;
}

export interface PairDetail extends Pair {
  timeframes: PairTimeframeData[];
  recent_signals: Signal[];
  performance_stats: PairPerformanceStats;
  correlation_group: string;
}

export interface PairTimeframeData {
  timeframe: Timeframe;
  volatility_regime: VolatilityRegime;
  atr_ratio: number;
  signals_count: number;
  win_rate: number;
  pnl_percent: number;
  active_preset_id: string;
}

export interface PairPerformanceStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  total_pnl_percent: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
  best_trade: number;
  worst_trade: number;
  avg_duration_hours: number;
}

export interface OHLCV {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// ============================================================================
// ANALYTICS
// ============================================================================

export interface EquityCurveData {
  timestamp: string;
  equity: number;
  balance: number;
  drawdown: number;
}

export interface DrawdownData {
  timestamp: string;
  drawdown: number;
  equity: number;
  peak_equity: number;
}

export interface MonthlyStats {
  month: string; // "2024-12"
  trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  pnl: number;
  pnl_percent: number;
  sharpe_ratio: number;
  max_drawdown: number;
}

export interface PairAnalytics {
  symbol: string;
  trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  pnl: number;
  pnl_percent: number;
  profit_factor: number;
  avg_win: number;
  avg_loss: number;
  sharpe_ratio: number;
  max_drawdown: number;
}

export interface CorrelationData {
  pairs: string[];
  matrix: number[][];
}

// ============================================================================
// BACKTEST
// ============================================================================

export interface BacktestConfig {
  symbol: string;
  timeframe: Timeframe;
  start_date: string;
  end_date: string;
  initial_balance: number;
  risk_per_trade: number;
  preset_id?: string;
  volatility_regime?: VolatilityRegime;
  parameters?: BacktestParameters;
}

export interface BacktestParameters {
  i1: number;
  i2: number;
  i3: number;
  i4: number;
  i5: number;
  tp_levels: number[];
  tp_distribution: number[];
  sl_percent: number;
}

export interface BacktestResult {
  id: string;
  config: BacktestConfig;
  status: BacktestStatus;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
  metrics?: BacktestMetrics;
  trades?: Trade[];
  equity_curve?: EquityPoint[];
}

export interface BacktestMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  total_pnl_percent: number;
  profit_factor: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  max_drawdown_percent: number;
  avg_win: number;
  avg_loss: number;
  best_trade: number;
  worst_trade: number;
  avg_duration_hours: number;
  expectancy: number;
  recovery_factor: number;
}

export interface BacktestListItem {
  id: string;
  symbol: string;
  timeframe: Timeframe;
  start_date: string;
  end_date: string;
  status: BacktestStatus;
  created_at: string;
  total_trades?: number;
  win_rate?: number;
  pnl_percent?: number;
  sharpe_ratio?: number;
}

// ============================================================================
// SETTINGS
// ============================================================================

export interface SystemSettings {
  trading: TradingSettings;
  portfolio: PortfolioSettings;
  telegram: TelegramSettings;
  system: SystemSettings2;
}

export interface TradingSettings {
  enabled: boolean;
  max_open_positions: number;
  risk_per_trade: number;
  max_portfolio_heat: number;
  allow_multiple_per_pair: boolean;
  min_signal_confidence: number;
  signal_expiry_hours: number;
}

export interface PortfolioSettings {
  initial_balance: number;
  max_correlation_exposure: number;
  correlation_threshold: number;
  max_drawdown_limit: number;
  auto_pause_on_loss_streak: boolean;
  loss_streak_threshold: number;
}

export interface TelegramSettings {
  enabled: boolean;
  bot_token: string;
  chat_id: string;
  send_signals: boolean;
  send_position_updates: boolean;
  send_alerts: boolean;
}

export interface SystemSettings2 {
  log_level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  data_update_interval: number;
  websocket_reconnect_delay: number;
  backup_enabled: boolean;
  backup_interval_hours: number;
}

export interface Preset {
  id: string;
  name: string;
  symbol: string;
  timeframe: Timeframe;
  volatility_regime: VolatilityRegime;
  parameters: BacktestParameters;
  metrics: PresetMetrics;
  created_at: string;
  updated_at: string;
  active: boolean;
}

export interface PresetMetrics {
  sharpe_ratio: number;
  win_rate: number;
  profit_factor: number;
  max_drawdown: number;
  total_trades: number;
  robustness_score: number;
}

// ============================================================================
// ALERTS
// ============================================================================

export interface Alert {
  id: string;
  type: AlertType;
  category: AlertCategory;
  title: string;
  message: string;
  data?: any;
  created_at: string;
  read: boolean;
  acknowledged: boolean;
}

export interface AlertSettings {
  enabled: boolean;
  telegram_enabled: boolean;
  desktop_enabled: boolean;
  sound_enabled: boolean;
  trading_alerts: {
    new_signal: boolean;
    position_opened: boolean;
    tp_hit: boolean;
    sl_hit: boolean;
    position_closed: boolean;
  };
  portfolio_alerts: {
    max_positions_reached: boolean;
    high_correlation_warning: boolean;
    portfolio_heat_limit: boolean;
    drawdown_limit: boolean;
  };
  system_alerts: {
    component_offline: boolean;
    api_error: boolean;
    data_error: boolean;
    backtest_completed: boolean;
  };
  performance_alerts: {
    loss_streak: boolean;
    low_win_rate: boolean;
    high_drawdown: boolean;
  };
  loss_streak_threshold: number;
  win_rate_threshold: number;
  drawdown_threshold: number;
}

// ============================================================================
// SYSTEM
// ============================================================================

export interface SystemStatus {
  components: ComponentStatusMap;
  uptime_seconds: number;
  memory_usage_mb: number;
  cpu_usage_percent: number;
  disk_usage_percent: number;
  database_size_mb: number;
  last_update: string;
}

export interface ComponentStatusMap {
  [key: string]: ComponentStatusDetail;
}

export interface ComponentStatusDetail {
  status: ComponentStatus;
  uptime_seconds?: number;
  last_error?: string;
  last_error_time?: string;
  message?: string;
}

export interface LogEntry {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  component: string;
  message: string;
  data?: any;
}

// ============================================================================
// WEBSOCKET
// ============================================================================

export interface WebSocketMessage {
  type: 'subscribed' | 'signal_new' | 'position_opened' | 'position_updated' | 
        'position_closed' | 'tp_hit' | 'sl_hit' | 'system_status' | 'error';
  data?: any;
  timestamp?: string;
}

export interface WebSocketSubscription {
  type: 'subscribe' | 'unsubscribe';
  channels: ('signals' | 'positions' | 'system')[];
}

// ============================================================================
// UI TYPES
// ============================================================================

export type Theme = 'dark' | 'light';

export interface FilterOptions {
  [key: string]: any;
}

export interface SortOptions {
  field: string;
  direction: 'asc' | 'desc';
}

export interface ChartOptions {
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  animated?: boolean;
}
