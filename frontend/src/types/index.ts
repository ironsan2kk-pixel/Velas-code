// ===== Trading Types =====

export type Side = 'LONG' | 'SHORT';
export type PositionStatus = 'open' | 'closed' | 'partial';
export type SignalStatus = 'pending' | 'active' | 'filled' | 'cancelled' | 'expired';
export type SystemStatus = 'online' | 'offline' | 'degraded' | 'maintenance';
export type VolatilityRegime = 'low' | 'normal' | 'high';
export type Timeframe = '30m' | '1h' | '2h';

// ===== Position Types =====

export interface Position {
  id: number;
  symbol: string;
  side: Side;
  timeframe: Timeframe;
  preset_id: string;
  entry_price: number;
  entry_time: string;
  quantity: number;
  current_sl: number;
  status: PositionStatus;
  tp1_hit: boolean;
  tp2_hit: boolean;
  tp3_hit: boolean;
  tp4_hit: boolean;
  tp5_hit: boolean;
  tp6_hit: boolean;
  close_price?: number;
  close_time?: string;
  close_reason?: string;
  realized_pnl?: number;
  unrealized_pnl?: number;
  unrealized_pnl_percent?: number;
  created_at: string;
}

export interface PositionSummary {
  total_positions: number;
  total_pnl: number;
  total_pnl_percent: number;
  winning_positions: number;
  losing_positions: number;
}

// ===== Signal Types =====

export interface Signal {
  id: number;
  symbol: string;
  side: Side;
  timeframe: Timeframe;
  entry_price: number;
  sl_price: number;
  tp1_price: number;
  tp2_price: number;
  tp3_price: number;
  tp4_price: number;
  tp5_price: number;
  tp6_price: number;
  status: SignalStatus;
  preset_id: string;
  volatility_regime: VolatilityRegime;
  telegram_sent: boolean;
  created_at: string;
}

// ===== Trade History Types =====

export interface TradeHistory {
  id: number;
  position_id: number;
  symbol: string;
  side: Side;
  timeframe: Timeframe;
  entry_price: number;
  exit_price: number;
  pnl_percent: number;
  pnl_usd: number;
  exit_reason: string;
  duration_minutes: number;
  created_at: string;
}

export interface HistoryStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_pnl: number;
  max_win: number;
  max_loss: number;
  profit_factor: number;
  avg_duration_minutes: number;
}

// ===== Pair Types =====

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
  active_position?: Position;
  last_signal?: Signal;
}

export interface PairDetail extends Pair {
  signals_count_24h: number;
  trades_count_24h: number;
  win_rate_30d: number;
  total_pnl_30d: number;
}

// ===== Analytics Types =====

export interface EquityPoint {
  timestamp: string;
  equity: number;
  drawdown: number;
}

export interface MonthlyStats {
  month: string;
  trades: number;
  win_rate: number;
  pnl: number;
  pnl_percent: number;
}

export interface PairStats {
  symbol: string;
  trades: number;
  win_rate: number;
  pnl: number;
  avg_pnl: number;
}

export interface CorrelationMatrix {
  symbols: string[];
  matrix: number[][];
}

// ===== Dashboard Types =====

export interface DashboardSummary {
  system_status: SystemStatus;
  total_balance: number;
  total_pnl: number;
  total_pnl_percent: number;
  win_rate: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  portfolio_heat: number;
  max_heat: number;
  open_positions_count: number;
  pending_signals_count: number;
}

export interface DashboardMetrics {
  sharpe_ratio: number;
  profit_factor: number;
  max_drawdown: number;
  avg_trade_duration_minutes: number;
  best_pair: string;
  worst_pair: string;
}

// ===== Backtest Types =====

export interface BacktestConfig {
  symbol: string;
  timeframe: Timeframe;
  start_date: string;
  end_date: string;
  initial_balance: number;
  risk_per_trade: number;
}

export interface BacktestResult {
  id: string;
  config: BacktestConfig;
  total_trades: number;
  win_rate: number;
  total_pnl: number;
  sharpe_ratio: number;
  profit_factor: number;
  max_drawdown: number;
  equity_curve: EquityPoint[];
  trades: TradeHistory[];
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  created_at: string;
}

// ===== Settings Types =====

export interface TradingSettings {
  mode: 'paper' | 'live';
  risk_per_trade: number;
  max_positions: number;
  max_per_sector: number;
  correlation_limit: number;
  initial_balance: number;
}

export interface TelegramSettings {
  enabled: boolean;
  bot_token_masked: string;
  chat_id: string;
  signal_new: boolean;
  tp_hit: boolean;
  sl_hit: boolean;
  system_errors: boolean;
}

export interface SystemSettings {
  log_level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  timezone: string;
  data_dir: string;
}

export interface AllSettings {
  trading: TradingSettings;
  telegram: TelegramSettings;
  system: SystemSettings;
}

// ===== System Types =====

export interface ComponentStatus {
  name: string;
  status: SystemStatus;
  last_heartbeat: string;
  error?: string;
}

export interface SystemStatusResponse {
  overall_status: SystemStatus;
  components: ComponentStatus[];
  uptime_seconds: number;
  version: string;
  last_update: string;
}

export interface LogEntry {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  component: string;
  message: string;
}

// ===== Preset Types =====

export interface Preset {
  id: string;
  symbol: string;
  timeframe: Timeframe;
  volatility_regime: VolatilityRegime;
  i1: number;
  i2: number;
  i3: number;
  i4: number;
  i5: number;
  tp1: number;
  tp2: number;
  tp3: number;
  tp4: number;
  tp5: number;
  tp6: number;
  sl: number;
  tp_distribution: number[];
  metrics: {
    win_rate: number;
    sharpe_ratio: number;
    profit_factor: number;
    max_drawdown: number;
  };
}

// ===== WebSocket Types =====

export interface WSMessage {
  type: string;
  data: unknown;
  timestamp: string;
}

export interface WSSignalNew {
  type: 'signal_new';
  data: Signal;
}

export interface WSPositionOpened {
  type: 'position_opened';
  data: Position;
}

export interface WSPositionUpdated {
  type: 'position_updated';
  data: Position;
}

export interface WSPositionClosed {
  type: 'position_closed';
  data: Position;
}

export interface WSTPHit {
  type: 'tp_hit';
  data: {
    position_id: number;
    tp_level: number;
    price: number;
  };
}

export interface WSSLHit {
  type: 'sl_hit';
  data: {
    position_id: number;
    price: number;
    pnl: number;
  };
}

export interface WSSystemStatus {
  type: 'system_status';
  data: SystemStatusResponse;
}

export type WSEvent =
  | WSSignalNew
  | WSPositionOpened
  | WSPositionUpdated
  | WSPositionClosed
  | WSTPHit
  | WSSLHit
  | WSSystemStatus;

// ===== API Response Types =====

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ===== Chart Types =====

export interface OHLCV {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartMarker {
  time: number;
  position: 'aboveBar' | 'belowBar';
  color: string;
  shape: 'circle' | 'square' | 'arrowUp' | 'arrowDown';
  text: string;
}
