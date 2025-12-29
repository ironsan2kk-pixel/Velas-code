"""
VELAS Signal Generator - генерация торговых сигналов.

Типы сигналов:
- LONG: высокая вероятность роста
- SHORT: высокая вероятность падения
- PREPARE_LONG: предупреждение о возможном LONG
- PREPARE_SHORT: предупреждение о возможном SHORT

Фильтры (опциональные):
- Volume: volume > SMA(volume, 20) * multiplier
- RSI: RSI > level (LONG) / RSI < level (SHORT)
- ADX: ADX > level (сила тренда)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

from .velas_indicator import VelasIndicator, VelasPreset


class SignalType(Enum):
    """Тип торгового сигнала."""
    LONG = "long"
    SHORT = "short"
    PREPARE_LONG = "prepare_long"
    PREPARE_SHORT = "prepare_short"


class SignalStrength(Enum):
    """Сила сигнала."""
    WEAK = "weak"
    NORMAL = "normal"
    STRONG = "strong"


@dataclass
class FilterConfig:
    """Конфигурация фильтров сигналов."""
    
    # Volume filter
    use_volume_filter: bool = False
    volume_multiplier: float = 1.2
    volume_period: int = 20
    
    # RSI filter
    use_rsi_filter: bool = False
    rsi_period: int = 14
    rsi_long_level: int = 50  # LONG если RSI > level
    rsi_short_level: int = 50  # SHORT если RSI < level
    
    # ADX filter
    use_adx_filter: bool = False
    adx_period: int = 14
    adx_level: int = 25  # Сигнал только если ADX > level
    
    # Session filter
    use_session_filter: bool = False
    session_start: str = "09:00"
    session_end: str = "17:00"
    
    # Adaptive filters (на основе ATR)
    use_adaptive_filters: bool = False
    adaptive_vol_coeff: float = 0.5
    adaptive_rsi_coeff: float = 10.0
    adaptive_adx_coeff: float = 10.0


@dataclass
class Signal:
    """Торговый сигнал."""
    
    timestamp: datetime
    symbol: str
    timeframe: str
    signal_type: SignalType
    entry_price: float
    
    # Уровни TP/SL (рассчитываются позже TPSLManager)
    tp_levels: List[float] = field(default_factory=list)
    sl_level: float = 0.0
    
    # Мета-информация
    preset_index: int = 0
    strength: SignalStrength = SignalStrength.NORMAL
    filters_passed: Dict[str, bool] = field(default_factory=dict)
    
    # Дополнительные данные индикатора
    high_channel: float = 0.0
    low_channel: float = 0.0
    mid_channel: float = 0.0
    trigger_price: float = 0.0  # long_trigger или short_trigger
    atr: float = 0.0
    
    @property
    def is_long(self) -> bool:
        return self.signal_type in (SignalType.LONG, SignalType.PREPARE_LONG)
    
    @property
    def is_short(self) -> bool:
        return self.signal_type in (SignalType.SHORT, SignalType.PREPARE_SHORT)
    
    @property
    def is_confirmed(self) -> bool:
        return self.signal_type in (SignalType.LONG, SignalType.SHORT)
    
    @property
    def signal_id(self) -> str:
        """Уникальный ID сигнала."""
        direction = "Long" if self.is_long else "Short"
        ts = self.timestamp.strftime("%d_%m_%Y_%H_%M")
        return f"#{direction}_{self.symbol}_{ts}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "signal_type": self.signal_type.value,
            "entry_price": self.entry_price,
            "tp_levels": self.tp_levels,
            "sl_level": self.sl_level,
            "preset_index": self.preset_index,
            "strength": self.strength.value,
            "filters_passed": self.filters_passed,
            "signal_id": self.signal_id,
        }


class SignalGenerator:
    """
    Генератор торговых сигналов на основе индикатора Velas.
    
    Использование:
        generator = SignalGenerator(preset, filter_config)
        signals = generator.generate(df)
    """
    
    PREPARE_OFFSET_PERCENT = 0.3  # Смещение для prepare сигналов
    
    def __init__(
        self,
        preset: VelasPreset,
        filter_config: FilterConfig = None,
        symbol: str = "BTCUSDT",
        timeframe: str = "1h",
    ):
        self.preset = preset
        self.filter_config = filter_config or FilterConfig()
        self.symbol = symbol
        self.timeframe = timeframe
        self.indicator = VelasIndicator(preset)
    
    def calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """Расчёт RSI (Relative Strength Index)."""
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        
        avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)
    
    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Расчёт ADX (Average Directional Index)."""
        high = df["high"]
        low = df["low"]
        close = df["close"]
        
        # True Range
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Smoothed values (Wilder's smoothing)
        atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        plus_di = 100 * pd.Series(plus_dm).ewm(alpha=1/period, min_periods=period, adjust=False).mean() / atr
        minus_di = 100 * pd.Series(minus_dm).ewm(alpha=1/period, min_periods=period, adjust=False).mean() / atr
        
        # DX и ADX
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        
        return adx.fillna(0)
    
    def check_filters(
        self,
        df: pd.DataFrame,
        idx: int,
        is_long: bool,
    ) -> Dict[str, bool]:
        """
        Проверить все фильтры для бара.
        
        Returns:
            Dict с результатами каждого фильтра
        """
        results = {}
        cfg = self.filter_config
        
        # Volume filter
        if cfg.use_volume_filter:
            vol = df["volume"].iloc[idx]
            vol_sma = df["volume"].iloc[max(0, idx-cfg.volume_period+1):idx+1].mean()
            
            # Адаптивный множитель
            if cfg.use_adaptive_filters:
                atr = df["atr"].iloc[idx] if "atr" in df.columns else 0
                close = df["close"].iloc[idx]
                vol_mult = 1 + (atr / close * cfg.adaptive_vol_coeff) if close > 0 else cfg.volume_multiplier
            else:
                vol_mult = cfg.volume_multiplier
            
            results["volume"] = vol > vol_sma * vol_mult
        else:
            results["volume"] = True
        
        # RSI filter
        if cfg.use_rsi_filter:
            if "rsi" not in df.columns:
                rsi_series = self.calculate_rsi(df["close"], cfg.rsi_period)
            else:
                rsi_series = df["rsi"]
            
            rsi = rsi_series.iloc[idx]
            
            # Адаптивные уровни
            if cfg.use_adaptive_filters:
                atr = df["atr"].iloc[idx] if "atr" in df.columns else 0
                close = df["close"].iloc[idx]
                rsi_adj = (atr / close * cfg.adaptive_rsi_coeff) if close > 0 else 0
                long_level = min(100, max(0, 50 + rsi_adj))
                short_level = min(100, max(0, 50 - rsi_adj))
            else:
                long_level = cfg.rsi_long_level
                short_level = cfg.rsi_short_level
            
            if is_long:
                results["rsi"] = rsi > long_level
            else:
                results["rsi"] = rsi < short_level
        else:
            results["rsi"] = True
        
        # ADX filter
        if cfg.use_adx_filter:
            if "adx" not in df.columns:
                adx_series = self.calculate_adx(df, cfg.adx_period)
            else:
                adx_series = df["adx"]
            
            adx = adx_series.iloc[idx]
            
            # Адаптивный уровень
            if cfg.use_adaptive_filters:
                atr = df["atr"].iloc[idx] if "atr" in df.columns else 0
                close = df["close"].iloc[idx]
                adx_level = cfg.adx_level + (atr / close * cfg.adaptive_adx_coeff) if close > 0 else cfg.adx_level
            else:
                adx_level = cfg.adx_level
            
            results["adx"] = adx > adx_level
        else:
            results["adx"] = True
        
        # Session filter
        if cfg.use_session_filter:
            ts = df.index[idx] if isinstance(df.index[idx], datetime) else df["timestamp"].iloc[idx]
            if isinstance(ts, pd.Timestamp):
                ts = ts.to_pydatetime()
            
            time_str = ts.strftime("%H:%M")
            results["session"] = cfg.session_start <= time_str <= cfg.session_end
        else:
            results["session"] = True
        
        return results
    
    def all_filters_passed(self, filter_results: Dict[str, bool]) -> bool:
        """Проверить, прошли ли все фильтры."""
        return all(filter_results.values())
    
    def generate(self, df: pd.DataFrame) -> List[Signal]:
        """
        Сгенерировать сигналы для всего DataFrame.
        
        Args:
            df: DataFrame с колонками [timestamp, open, high, low, close, volume]
            
        Returns:
            Список сигналов (пустой если недостаточно данных)
        """
        # Проверка на пустой или маленький DataFrame
        if df is None or len(df) == 0:
            return []
        
        # Рассчитываем индикатор (может выбросить ValueError при недостатке данных)
        try:
            calc_df = self.indicator.calculate(df)
        except ValueError:
            # Недостаточно данных для расчёта индикатора
            return []
        
        # Добавляем RSI и ADX если нужны фильтры
        if self.filter_config.use_rsi_filter:
            calc_df["rsi"] = self.calculate_rsi(calc_df["close"], self.filter_config.rsi_period)
        if self.filter_config.use_adx_filter:
            calc_df["adx"] = self.calculate_adx(calc_df, self.filter_config.adx_period)
        
        signals = []
        in_position = 0  # 0=нет, 1=long, -1=short
        
        # Prepare triggers (смещённые на 0.3%)
        calc_df["long_prepare_trigger"] = calc_df["long_trigger"] * (1 - self.PREPARE_OFFSET_PERCENT / 100)
        calc_df["short_prepare_trigger"] = calc_df["short_trigger"] * (1 + self.PREPARE_OFFSET_PERCENT / 100)
        
        for idx in range(len(calc_df)):
            row = calc_df.iloc[idx]
            
            # Пропускаем если триггеры не рассчитаны (NaN)
            if pd.isna(row["long_trigger"]) or pd.isna(row["short_trigger"]):
                continue
            
            # Получаем timestamp
            if "timestamp" in calc_df.columns:
                ts = row["timestamp"]
            elif isinstance(calc_df.index[idx], pd.Timestamp):
                ts = calc_df.index[idx]
            else:
                ts = datetime.now()
            
            if isinstance(ts, pd.Timestamp):
                ts = ts.to_pydatetime()
            
            high = row["high"]
            low = row["low"]
            close = row["close"]
            
            # Проверка условий
            raw_long = high > row["long_trigger"]
            raw_short = low < row["short_trigger"]
            prepare_long = high > row["long_prepare_trigger"] and in_position != 1
            prepare_short = low < row["short_prepare_trigger"] and in_position != -1
            
            # Генерация сигналов
            if raw_long and in_position != 1:
                filters = self.check_filters(calc_df, idx, is_long=True)
                
                if self.all_filters_passed(filters):
                    signal = Signal(
                        timestamp=ts,
                        symbol=self.symbol,
                        timeframe=self.timeframe,
                        signal_type=SignalType.LONG,
                        entry_price=close,
                        preset_index=self.preset.index,
                        filters_passed=filters,
                        high_channel=row["high_channel"],
                        low_channel=row["low_channel"],
                        mid_channel=row["mid_channel"],
                        trigger_price=row["long_trigger"],
                        atr=row["atr"],
                    )
                    signals.append(signal)
                    in_position = 1
            
            elif raw_short and in_position != -1:
                filters = self.check_filters(calc_df, idx, is_long=False)
                
                if self.all_filters_passed(filters):
                    signal = Signal(
                        timestamp=ts,
                        symbol=self.symbol,
                        timeframe=self.timeframe,
                        signal_type=SignalType.SHORT,
                        entry_price=close,
                        preset_index=self.preset.index,
                        filters_passed=filters,
                        high_channel=row["high_channel"],
                        low_channel=row["low_channel"],
                        mid_channel=row["mid_channel"],
                        trigger_price=row["short_trigger"],
                        atr=row["atr"],
                    )
                    signals.append(signal)
                    in_position = -1
            
            # Противоположный сигнал закрывает позицию
            if raw_short and in_position == 1:
                filters = self.check_filters(calc_df, idx, is_long=False)
                if self.all_filters_passed(filters):
                    signal = Signal(
                        timestamp=ts,
                        symbol=self.symbol,
                        timeframe=self.timeframe,
                        signal_type=SignalType.SHORT,
                        entry_price=close,
                        preset_index=self.preset.index,
                        filters_passed=filters,
                        high_channel=row["high_channel"],
                        low_channel=row["low_channel"],
                        mid_channel=row["mid_channel"],
                        trigger_price=row["short_trigger"],
                        atr=row["atr"],
                    )
                    signals.append(signal)
                    in_position = -1
            
            elif raw_long and in_position == -1:
                filters = self.check_filters(calc_df, idx, is_long=True)
                if self.all_filters_passed(filters):
                    signal = Signal(
                        timestamp=ts,
                        symbol=self.symbol,
                        timeframe=self.timeframe,
                        signal_type=SignalType.LONG,
                        entry_price=close,
                        preset_index=self.preset.index,
                        filters_passed=filters,
                        high_channel=row["high_channel"],
                        low_channel=row["low_channel"],
                        mid_channel=row["mid_channel"],
                        trigger_price=row["long_trigger"],
                        atr=row["atr"],
                    )
                    signals.append(signal)
                    in_position = 1
        
        return signals
    
    def generate_single(self, df: pd.DataFrame) -> Optional[Signal]:
        """
        Проверить последний бар на наличие сигнала.
        
        Args:
            df: DataFrame с OHLCV данными
            
        Returns:
            Signal или None
        """
        signals = self.generate(df)
        if signals:
            return signals[-1]
        return None
