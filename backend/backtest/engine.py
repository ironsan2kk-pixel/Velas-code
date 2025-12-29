"""
VELAS Backtest Engine - главный движок бэктестинга.

Функционал:
- Загрузка исторических данных
- Генерация сигналов
- Симуляция сделок
- Расчёт метрик
- Вывод результатов

Использование:
    engine = BacktestEngine(config)
    result = engine.run(df)
    print(result.metrics)
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
import pandas as pd
import numpy as np

from ..core.velas_indicator import VelasIndicator, VelasPreset, VELAS_PRESETS_60
from ..core.signals import SignalGenerator, Signal, SignalType, FilterConfig
from ..core.tpsl import TPSLManager, TPSLConfig, StopManagement
from .trade import Trade, TradeResult, TradeDirection, TradeStatus
from .metrics import BacktestMetrics, calculate_all_metrics, calculate_equity_curve


@dataclass
class BacktestConfig:
    """Конфигурация бэктеста."""
    
    # Символ и таймфрейм
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    
    # Пресет индикатора
    preset: VelasPreset = None
    preset_index: int = 0  # Если preset=None, используется этот индекс
    
    # TP/SL конфигурация
    tpsl_config: TPSLConfig = None
    
    # Фильтры сигналов
    filter_config: FilterConfig = None
    
    # Капитал
    initial_capital: float = 10000.0
    
    # Режимы
    cascade_stop: bool = True  # Каскадный стоп
    close_on_opposite_signal: bool = True  # Закрывать по противоположному сигналу
    
    # Дата range (опционально)
    start_date: datetime = None
    end_date: datetime = None
    
    def __post_init__(self):
        if self.preset is None:
            if 0 <= self.preset_index < 60:
                self.preset = VELAS_PRESETS_60[self.preset_index]
            else:
                self.preset = VELAS_PRESETS_60[0]
        
        if self.tpsl_config is None:
            self.tpsl_config = TPSLConfig()
        
        if self.filter_config is None:
            self.filter_config = FilterConfig()


@dataclass
class BacktestResult:
    """Результат бэктеста."""
    
    # Конфигурация
    config: BacktestConfig
    
    # Данные
    start_date: datetime = None
    end_date: datetime = None
    total_bars: int = 0
    
    # Сделки
    trades: List[Trade] = field(default_factory=list)
    
    # Метрики
    metrics: BacktestMetrics = None
    
    # Equity curve
    equity_curve: pd.DataFrame = None
    
    # Время выполнения
    execution_time_ms: float = 0.0
    
    @property
    def signals_generated(self) -> int:
        return len(self.trades)
    
    @property
    def closed_trades(self) -> List[Trade]:
        return [t for t in self.trades if t.result is not None]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.config.symbol,
            "timeframe": self.config.timeframe,
            "preset_index": self.config.preset.index,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "total_bars": self.total_bars,
            "signals_generated": self.signals_generated,
            "closed_trades": len(self.closed_trades),
            "metrics": self.metrics.to_dict() if self.metrics else None,
            "execution_time_ms": self.execution_time_ms,
        }
    
    def to_summary(self) -> str:
        """Краткий отчёт."""
        lines = [
            f"📊 Бэктест {self.config.symbol} {self.config.timeframe}",
            f"   Пресет: {self.config.preset.name}",
            f"   Период: {self.start_date} - {self.end_date}",
            f"   Баров: {self.total_bars}",
            f"   Сделок: {len(self.closed_trades)}",
            "",
        ]
        
        if self.metrics:
            lines.extend([
                f"   Win Rate: {self.metrics.win_rate:.1f}%",
                f"   Win Rate TP1: {self.metrics.win_rate_tp1:.1f}%",
                f"   Total PnL: {self.metrics.total_pnl_percent:+.2f}%",
                f"   Sharpe: {self.metrics.sharpe_ratio:.2f}",
                f"   Max DD: {self.metrics.max_drawdown_percent:.2f}%",
                f"   Profit Factor: {self.metrics.profit_factor:.2f}",
            ])
        
        return "\n".join(lines)


class BacktestEngine:
    """
    Движок бэктестинга.
    
    Пример использования:
        config = BacktestConfig(
            symbol="BTCUSDT",
            timeframe="1h",
            preset_index=5,
        )
        engine = BacktestEngine(config)
        result = engine.run(df)
        print(result.to_summary())
    """
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        
        # Инициализируем компоненты
        self.indicator = VelasIndicator(self.config.preset)
        self.signal_generator = SignalGenerator(
            preset=self.config.preset,
            filter_config=self.config.filter_config,
            symbol=self.config.symbol,
            timeframe=self.config.timeframe,
        )
        self.tpsl_manager = TPSLManager(self.config.tpsl_config)
    
    def run(self, df: pd.DataFrame) -> BacktestResult:
        """
        Запустить бэктест.
        
        Args:
            df: DataFrame с колонками [timestamp, open, high, low, close, volume]
            
        Returns:
            BacktestResult
        """
        import time
        start_time = time.time()
        
        # Подготовка данных
        df = self._prepare_data(df)
        
        result = BacktestResult(config=self.config)
        result.total_bars = len(df)
        
        if len(df) == 0:
            return result
        
        # Определяем период
        if "timestamp" in df.columns:
            result.start_date = pd.Timestamp(df["timestamp"].iloc[0]).to_pydatetime()
            result.end_date = pd.Timestamp(df["timestamp"].iloc[-1]).to_pydatetime()
        elif isinstance(df.index[0], pd.Timestamp):
            result.start_date = df.index[0].to_pydatetime()
            result.end_date = df.index[-1].to_pydatetime()
        
        # Рассчитываем индикатор
        calc_df = self.indicator.calculate(df)
        
        # Симулируем торговлю
        result.trades = self._simulate_trading(calc_df)
        
        # Рассчитываем метрики
        result.metrics = calculate_all_metrics(
            result.trades,
            self.config.initial_capital,
        )
        
        # Строим equity curve
        result.equity_curve = calculate_equity_curve(
            result.trades,
            self.config.initial_capital,
        )
        
        result.execution_time_ms = (time.time() - start_time) * 1000
        
        return result
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Подготовить данные для бэктеста."""
        df = df.copy()
        
        # Убеждаемся что есть нужные колонки
        required = ["open", "high", "low", "close", "volume"]
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Отсутствует колонка: {col}")
        
        # Фильтруем по датам если указаны
        if self.config.start_date or self.config.end_date:
            if "timestamp" in df.columns:
                ts_col = pd.to_datetime(df["timestamp"])
            elif isinstance(df.index, pd.DatetimeIndex):
                ts_col = df.index
            else:
                ts_col = None
            
            if ts_col is not None:
                if self.config.start_date:
                    mask = ts_col >= pd.Timestamp(self.config.start_date)
                    df = df[mask]
                if self.config.end_date:
                    mask = ts_col <= pd.Timestamp(self.config.end_date)
                    df = df[mask]
        
        return df.reset_index(drop=True)
    
    def _simulate_trading(self, df: pd.DataFrame) -> List[Trade]:
        """Симулировать торговлю на исторических данных."""
        trades = []
        current_trade: Optional[Trade] = None
        
        for idx in range(len(df)):
            row = df.iloc[idx]
            
            # Пропускаем если триггеры не рассчитаны
            if pd.isna(row.get("long_trigger")) or pd.isna(row.get("short_trigger")):
                continue
            
            # Получаем данные бара
            if "timestamp" in df.columns:
                ts = pd.Timestamp(row["timestamp"]).to_pydatetime()
            elif isinstance(df.index[idx], pd.Timestamp):
                ts = df.index[idx].to_pydatetime()
            else:
                ts = datetime.now()
            
            high = row["high"]
            low = row["low"]
            close = row["close"]
            
            # Если есть открытая сделка - проверяем TP/SL
            if current_trade is not None and current_trade.is_open:
                result = current_trade.check_bar(
                    timestamp=ts,
                    high=high,
                    low=low,
                    close=close,
                    cascade_stop=self.config.cascade_stop,
                )
                
                if result is not None:
                    # Сделка закрыта
                    current_trade = None
            
            # Проверяем условия для нового сигнала
            raw_long = high > row["long_trigger"]
            raw_short = low < row["short_trigger"]
            
            # Противоположный сигнал закрывает текущую сделку
            if current_trade is not None and current_trade.is_open:
                if self.config.close_on_opposite_signal:
                    if raw_long and not current_trade.is_long:
                        current_trade.close_by_signal(ts, close)
                        current_trade = None
                    elif raw_short and current_trade.is_long:
                        current_trade.close_by_signal(ts, close)
                        current_trade = None
            
            # Открываем новую сделку
            if current_trade is None or not current_trade.is_open:
                if raw_long:
                    current_trade = self._open_trade(
                        timestamp=ts,
                        direction=TradeDirection.LONG,
                        entry_price=close,
                        atr=row.get("atr", 0),
                    )
                    trades.append(current_trade)
                elif raw_short:
                    current_trade = self._open_trade(
                        timestamp=ts,
                        direction=TradeDirection.SHORT,
                        entry_price=close,
                        atr=row.get("atr", 0),
                    )
                    trades.append(current_trade)
        
        # Закрываем открытую сделку в конце
        if current_trade is not None and current_trade.is_open:
            last_row = df.iloc[-1]
            if "timestamp" in df.columns:
                last_ts = pd.Timestamp(last_row["timestamp"]).to_pydatetime()
            else:
                last_ts = datetime.now()
            current_trade.close_manual(last_ts, last_row["close"])
        
        return trades
    
    def _open_trade(
        self,
        timestamp: datetime,
        direction: TradeDirection,
        entry_price: float,
        atr: float = 0,
    ) -> Trade:
        """Открыть новую сделку."""
        # Создаём фиктивный сигнал для TPSL менеджера
        signal = Signal(
            timestamp=timestamp,
            symbol=self.config.symbol,
            timeframe=self.config.timeframe,
            signal_type=SignalType.LONG if direction == TradeDirection.LONG else SignalType.SHORT,
            entry_price=entry_price,
            preset_index=self.config.preset.index,
            atr=atr,
        )
        
        # Рассчитываем TP/SL
        levels = self.tpsl_manager.calculate_levels(signal, atr=atr)
        
        # Создаём сделку
        return Trade.from_signal(signal, levels)
    
    def run_multiple_presets(
        self,
        df: pd.DataFrame,
        presets: List[VelasPreset] = None,
        progress_callback: Callable[[int, int], None] = None,
    ) -> List[BacktestResult]:
        """
        Запустить бэктест для нескольких пресетов.
        
        Args:
            df: DataFrame с данными
            presets: Список пресетов (по умолчанию все 60)
            progress_callback: Функция для отслеживания прогресса (current, total)
            
        Returns:
            Список результатов
        """
        if presets is None:
            presets = VELAS_PRESETS_60
        
        results = []
        
        for i, preset in enumerate(presets):
            # Обновляем пресет
            self.config.preset = preset
            self.indicator = VelasIndicator(preset)
            self.signal_generator = SignalGenerator(
                preset=preset,
                filter_config=self.config.filter_config,
                symbol=self.config.symbol,
                timeframe=self.config.timeframe,
            )
            
            # Запускаем бэктест
            result = self.run(df)
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, len(presets))
        
        return results
    
    def find_best_preset(
        self,
        df: pd.DataFrame,
        presets: List[VelasPreset] = None,
        metric: str = "sharpe_ratio",
    ) -> BacktestResult:
        """
        Найти лучший пресет по метрике.
        
        Args:
            df: DataFrame с данными
            presets: Список пресетов
            metric: Метрика для сортировки (sharpe_ratio, win_rate, profit_factor, etc.)
            
        Returns:
            Лучший результат
        """
        results = self.run_multiple_presets(df, presets)
        
        if not results:
            return None
        
        # Сортируем по метрике
        def get_metric(r: BacktestResult) -> float:
            if r.metrics is None:
                return float("-inf")
            value = getattr(r.metrics, metric, None)
            if value is None:
                return float("-inf")
            # Для max_drawdown меньше = лучше
            if metric == "max_drawdown_percent":
                return -abs(value)
            return value
        
        results.sort(key=get_metric, reverse=True)
        
        return results[0]


def run_quick_backtest(
    df: pd.DataFrame,
    preset_index: int = 0,
    symbol: str = "BTCUSDT",
    timeframe: str = "1h",
) -> BacktestResult:
    """
    Быстрый запуск бэктеста с настройками по умолчанию.
    
    Args:
        df: DataFrame с OHLCV данными
        preset_index: Индекс пресета (0-59)
        symbol: Торговый символ
        timeframe: Таймфрейм
        
    Returns:
        BacktestResult
    """
    config = BacktestConfig(
        symbol=symbol,
        timeframe=timeframe,
        preset_index=preset_index,
    )
    
    engine = BacktestEngine(config)
    return engine.run(df)
