"""
VELAS Backtest Metrics - метрики оценки торговой стратегии.

Метрики:
- Win Rate (общий и по TP уровням)
- Sharpe Ratio
- Maximum Drawdown
- Profit Factor
- Equity Curve
- Expectancy
- Recovery Factor
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import numpy as np
import pandas as pd

from .trade import Trade, TradeResult, TradeStatus


@dataclass
class BacktestMetrics:
    """Полный набор метрик бэктеста."""
    
    # Базовые
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    breakeven_trades: int = 0
    
    # Win Rate
    win_rate: float = 0.0           # Общий win rate
    win_rate_tp1: float = 0.0       # Win rate достижения TP1
    win_rate_tp2: float = 0.0       # Win rate достижения TP2
    win_rate_tp3: float = 0.0       # и т.д.
    win_rate_tp4: float = 0.0
    win_rate_tp5: float = 0.0
    win_rate_tp6: float = 0.0
    
    # PnL
    total_pnl_percent: float = 0.0
    avg_win_percent: float = 0.0
    avg_loss_percent: float = 0.0
    max_win_percent: float = 0.0
    max_loss_percent: float = 0.0
    
    # Risk metrics
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown_percent: float = 0.0
    max_drawdown_duration: int = 0  # В барах
    profit_factor: float = 0.0
    
    # Дополнительные
    expectancy: float = 0.0         # Математическое ожидание
    recovery_factor: float = 0.0    # PnL / MaxDD
    avg_trade_duration: float = 0.0 # Средняя длительность в барах
    avg_rr_ratio: float = 0.0       # Средний Risk/Reward
    
    # Equity
    final_equity: float = 0.0
    peak_equity: float = 0.0
    
    # Серии
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "breakeven_trades": self.breakeven_trades,
            "win_rate": round(self.win_rate, 2),
            "win_rate_tp1": round(self.win_rate_tp1, 2),
            "win_rate_tp2": round(self.win_rate_tp2, 2),
            "win_rate_tp3": round(self.win_rate_tp3, 2),
            "win_rate_tp4": round(self.win_rate_tp4, 2),
            "win_rate_tp5": round(self.win_rate_tp5, 2),
            "win_rate_tp6": round(self.win_rate_tp6, 2),
            "total_pnl_percent": round(self.total_pnl_percent, 2),
            "avg_win_percent": round(self.avg_win_percent, 2),
            "avg_loss_percent": round(self.avg_loss_percent, 2),
            "max_win_percent": round(self.max_win_percent, 2),
            "max_loss_percent": round(self.max_loss_percent, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "sortino_ratio": round(self.sortino_ratio, 2),
            "max_drawdown_percent": round(self.max_drawdown_percent, 2),
            "max_drawdown_duration": self.max_drawdown_duration,
            "profit_factor": round(self.profit_factor, 2),
            "expectancy": round(self.expectancy, 4),
            "recovery_factor": round(self.recovery_factor, 2),
            "avg_trade_duration": round(self.avg_trade_duration, 1),
            "avg_rr_ratio": round(self.avg_rr_ratio, 2),
            "final_equity": round(self.final_equity, 2),
            "peak_equity": round(self.peak_equity, 2),
            "max_consecutive_wins": self.max_consecutive_wins,
            "max_consecutive_losses": self.max_consecutive_losses,
        }
    
    def is_acceptable(
        self,
        min_win_rate: float = 40.0,
        min_win_rate_tp1: float = 70.0,
        min_sharpe: float = 1.0,
        max_drawdown: float = 15.0,
        min_profit_factor: float = 1.5,
    ) -> Tuple[bool, List[str]]:
        """
        Проверить, соответствуют ли метрики требованиям.
        
        Returns:
            (passed, list of failed criteria)
        """
        failed = []
        
        if self.win_rate < min_win_rate:
            failed.append(f"Win Rate {self.win_rate:.1f}% < {min_win_rate}%")
        
        if self.win_rate_tp1 < min_win_rate_tp1:
            failed.append(f"Win Rate TP1 {self.win_rate_tp1:.1f}% < {min_win_rate_tp1}%")
        
        if self.sharpe_ratio < min_sharpe:
            failed.append(f"Sharpe Ratio {self.sharpe_ratio:.2f} < {min_sharpe}")
        
        if abs(self.max_drawdown_percent) > max_drawdown:
            failed.append(f"Max DD {abs(self.max_drawdown_percent):.1f}% > {max_drawdown}%")
        
        if self.profit_factor < min_profit_factor:
            failed.append(f"Profit Factor {self.profit_factor:.2f} < {min_profit_factor}")
        
        return len(failed) == 0, failed


def calculate_win_rate(trades: List[Trade]) -> Tuple[float, Dict[str, float]]:
    """
    Рассчитать Win Rate (общий и по TP уровням).
    
    Args:
        trades: Список закрытых сделок
        
    Returns:
        (общий win rate, dict с win rate по TP уровням)
    """
    if not trades:
        return 0.0, {}
    
    closed_trades = [t for t in trades if t.result is not None]
    if not closed_trades:
        return 0.0, {}
    
    total = len(closed_trades)
    
    # Общий win rate
    winners = sum(1 for t in closed_trades if t.result.is_profitable)
    win_rate = (winners / total) * 100
    
    # Win rate по TP уровням
    tp_rates = {}
    for tp_idx in range(1, 7):
        reached = sum(
            1 for t in closed_trades 
            if any(h.index == tp_idx for h in t.result.tp_hits)
        )
        tp_rates[f"tp{tp_idx}"] = (reached / total) * 100
    
    return win_rate, tp_rates


def calculate_sharpe_ratio(
    returns: List[float],
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """
    Рассчитать Sharpe Ratio.
    
    Sharpe = (mean_return - risk_free) / std_return * sqrt(periods)
    
    Args:
        returns: Список доходностей (в процентах)
        risk_free_rate: Безрисковая ставка (годовая, в процентах)
        periods_per_year: Количество периодов в году
    """
    if len(returns) < 2:
        return 0.0
    
    returns_arr = np.array(returns)
    
    mean_return = np.mean(returns_arr)
    std_return = np.std(returns_arr, ddof=1)
    
    if std_return == 0:
        return 0.0
    
    # Приводим risk-free к периоду
    rf_per_period = risk_free_rate / periods_per_year
    
    sharpe = (mean_return - rf_per_period) / std_return * np.sqrt(periods_per_year)
    
    return float(sharpe)


def calculate_sortino_ratio(
    returns: List[float],
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """
    Рассчитать Sortino Ratio (учитывает только downside риск).
    
    Sortino = (mean_return - risk_free) / downside_std * sqrt(periods)
    """
    if len(returns) < 2:
        return 0.0
    
    returns_arr = np.array(returns)
    
    mean_return = np.mean(returns_arr)
    
    # Downside deviation - std только отрицательных возвратов
    negative_returns = returns_arr[returns_arr < 0]
    if len(negative_returns) == 0:
        return float("inf")  # Нет убыточных сделок
    
    downside_std = np.std(negative_returns, ddof=1)
    
    if downside_std == 0:
        return float("inf")
    
    rf_per_period = risk_free_rate / periods_per_year
    
    sortino = (mean_return - rf_per_period) / downside_std * np.sqrt(periods_per_year)
    
    return float(sortino)


def calculate_max_drawdown(equity_curve: List[float]) -> Tuple[float, int]:
    """
    Рассчитать максимальную просадку.
    
    Args:
        equity_curve: Кривая эквити (список значений)
        
    Returns:
        (max drawdown в процентах, длительность в барах)
    """
    if len(equity_curve) < 2:
        return 0.0, 0
    
    equity = np.array(equity_curve)
    
    # Бегущий максимум
    running_max = np.maximum.accumulate(equity)
    
    # Просадки
    drawdowns = (equity - running_max) / running_max * 100
    
    max_dd = float(np.min(drawdowns))
    
    # Длительность максимальной просадки
    dd_duration = 0
    current_duration = 0
    in_dd = False
    
    for i in range(len(equity)):
        if equity[i] < running_max[i]:
            current_duration += 1
            in_dd = True
        else:
            if in_dd:
                dd_duration = max(dd_duration, current_duration)
                current_duration = 0
                in_dd = False
    
    # Если ещё в просадке
    if in_dd:
        dd_duration = max(dd_duration, current_duration)
    
    return max_dd, dd_duration


def calculate_profit_factor(trades: List[Trade]) -> float:
    """
    Рассчитать Profit Factor.
    
    PF = сумма прибылей / сумма убытков
    
    PF > 1 = прибыльная стратегия
    PF > 2 = хорошая стратегия
    """
    if not trades:
        return 0.0
    
    closed_trades = [t for t in trades if t.result is not None]
    
    gross_profit = sum(
        t.result.total_pnl_percent 
        for t in closed_trades 
        if t.result.total_pnl_percent > 0
    )
    
    gross_loss = abs(sum(
        t.result.total_pnl_percent 
        for t in closed_trades 
        if t.result.total_pnl_percent < 0
    ))
    
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    
    return gross_profit / gross_loss


def calculate_equity_curve(
    trades: List[Trade],
    initial_capital: float = 10000.0,
) -> pd.DataFrame:
    """
    Построить кривую эквити.
    
    Args:
        trades: Список сделок (с результатами)
        initial_capital: Начальный капитал
        
    Returns:
        DataFrame с колонками [timestamp, equity, drawdown, trade_pnl]
    """
    data = []
    equity = initial_capital
    peak_equity = initial_capital
    
    # Сортируем по времени закрытия
    closed_trades = sorted(
        [t for t in trades if t.result is not None],
        key=lambda t: t.result.exit_timestamp
    )
    
    # Начальная точка
    if closed_trades:
        first_ts = closed_trades[0].entry_timestamp
        data.append({
            "timestamp": first_ts,
            "equity": initial_capital,
            "drawdown": 0.0,
            "trade_pnl": 0.0,
        })
    
    for trade in closed_trades:
        pnl_amount = equity * (trade.result.total_pnl_percent / 100)
        equity += pnl_amount
        peak_equity = max(peak_equity, equity)
        
        drawdown = (equity - peak_equity) / peak_equity * 100 if peak_equity > 0 else 0
        
        data.append({
            "timestamp": trade.result.exit_timestamp,
            "equity": equity,
            "drawdown": drawdown,
            "trade_pnl": trade.result.total_pnl_percent,
        })
    
    return pd.DataFrame(data)


def calculate_all_metrics(
    trades: List[Trade],
    initial_capital: float = 10000.0,
    risk_free_rate: float = 0.0,
) -> BacktestMetrics:
    """
    Рассчитать все метрики бэктеста.
    
    Args:
        trades: Список сделок
        initial_capital: Начальный капитал
        risk_free_rate: Безрисковая ставка (годовая)
        
    Returns:
        BacktestMetrics
    """
    metrics = BacktestMetrics()
    
    closed_trades = [t for t in trades if t.result is not None]
    
    if not closed_trades:
        return metrics
    
    metrics.total_trades = len(closed_trades)
    
    # Разделяем на winners/losers
    winners = [t for t in closed_trades if t.result.total_pnl_percent > 0]
    losers = [t for t in closed_trades if t.result.total_pnl_percent < 0]
    breakeven = [t for t in closed_trades if t.result.total_pnl_percent == 0]
    
    metrics.winning_trades = len(winners)
    metrics.losing_trades = len(losers)
    metrics.breakeven_trades = len(breakeven)
    
    # Win Rate
    win_rate, tp_rates = calculate_win_rate(closed_trades)
    metrics.win_rate = win_rate
    metrics.win_rate_tp1 = tp_rates.get("tp1", 0.0)
    metrics.win_rate_tp2 = tp_rates.get("tp2", 0.0)
    metrics.win_rate_tp3 = tp_rates.get("tp3", 0.0)
    metrics.win_rate_tp4 = tp_rates.get("tp4", 0.0)
    metrics.win_rate_tp5 = tp_rates.get("tp5", 0.0)
    metrics.win_rate_tp6 = tp_rates.get("tp6", 0.0)
    
    # PnL статистика
    all_pnls = [t.result.total_pnl_percent for t in closed_trades]
    win_pnls = [t.result.total_pnl_percent for t in winners]
    loss_pnls = [t.result.total_pnl_percent for t in losers]
    
    metrics.total_pnl_percent = sum(all_pnls)
    metrics.avg_win_percent = np.mean(win_pnls) if win_pnls else 0.0
    metrics.avg_loss_percent = np.mean(loss_pnls) if loss_pnls else 0.0
    metrics.max_win_percent = max(win_pnls) if win_pnls else 0.0
    metrics.max_loss_percent = min(loss_pnls) if loss_pnls else 0.0
    
    # Equity curve
    equity_df = calculate_equity_curve(closed_trades, initial_capital)
    equity_curve = equity_df["equity"].tolist()
    
    metrics.final_equity = equity_curve[-1] if equity_curve else initial_capital
    metrics.peak_equity = max(equity_curve) if equity_curve else initial_capital
    
    # Risk metrics
    metrics.sharpe_ratio = calculate_sharpe_ratio(all_pnls, risk_free_rate)
    metrics.sortino_ratio = calculate_sortino_ratio(all_pnls, risk_free_rate)
    
    max_dd, dd_duration = calculate_max_drawdown(equity_curve)
    metrics.max_drawdown_percent = max_dd
    metrics.max_drawdown_duration = dd_duration
    
    metrics.profit_factor = calculate_profit_factor(closed_trades)
    
    # Expectancy
    if metrics.total_trades > 0:
        metrics.expectancy = (
            (metrics.win_rate / 100 * metrics.avg_win_percent) +
            ((100 - metrics.win_rate) / 100 * metrics.avg_loss_percent)
        )
    
    # Recovery Factor
    if abs(metrics.max_drawdown_percent) > 0:
        pnl_amount = initial_capital * (metrics.total_pnl_percent / 100)
        dd_amount = initial_capital * (abs(metrics.max_drawdown_percent) / 100)
        metrics.recovery_factor = pnl_amount / dd_amount if dd_amount > 0 else 0.0
    
    # Средняя длительность
    durations = [t.result.duration_bars for t in closed_trades]
    metrics.avg_trade_duration = np.mean(durations) if durations else 0.0
    
    # Risk/Reward ratio
    if abs(metrics.avg_loss_percent) > 0:
        metrics.avg_rr_ratio = abs(metrics.avg_win_percent / metrics.avg_loss_percent)
    
    # Серии побед/поражений
    metrics.max_consecutive_wins, metrics.max_consecutive_losses = _calculate_streaks(
        [t.result.is_profitable for t in closed_trades]
    )
    
    return metrics


def _calculate_streaks(results: List[bool]) -> Tuple[int, int]:
    """Рассчитать максимальные серии побед/поражений."""
    if not results:
        return 0, 0
    
    max_wins = 0
    max_losses = 0
    current_wins = 0
    current_losses = 0
    
    for is_win in results:
        if is_win:
            current_wins += 1
            current_losses = 0
            max_wins = max(max_wins, current_wins)
        else:
            current_losses += 1
            current_wins = 0
            max_losses = max(max_losses, current_losses)
    
    return max_wins, max_losses


def generate_metrics_report(metrics: BacktestMetrics) -> str:
    """Сгенерировать текстовый отчёт по метрикам."""
    lines = [
        "=" * 50,
        "ОТЧЁТ БЭКТЕСТИНГА",
        "=" * 50,
        "",
        "📊 СДЕЛКИ",
        f"  Всего сделок: {metrics.total_trades}",
        f"  Прибыльных: {metrics.winning_trades} ({metrics.win_rate:.1f}%)",
        f"  Убыточных: {metrics.losing_trades}",
        f"  В ноль: {metrics.breakeven_trades}",
        "",
        "🎯 WIN RATE ПО TP",
        f"  TP1: {metrics.win_rate_tp1:.1f}%",
        f"  TP2: {metrics.win_rate_tp2:.1f}%",
        f"  TP3: {metrics.win_rate_tp3:.1f}%",
        f"  TP4: {metrics.win_rate_tp4:.1f}%",
        f"  TP5: {metrics.win_rate_tp5:.1f}%",
        f"  TP6: {metrics.win_rate_tp6:.1f}%",
        "",
        "💰 PnL",
        f"  Общий PnL: {metrics.total_pnl_percent:+.2f}%",
        f"  Средний выигрыш: {metrics.avg_win_percent:+.2f}%",
        f"  Средний убыток: {metrics.avg_loss_percent:.2f}%",
        f"  Макс. выигрыш: {metrics.max_win_percent:+.2f}%",
        f"  Макс. убыток: {metrics.max_loss_percent:.2f}%",
        "",
        "📈 РИСК-МЕТРИКИ",
        f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}",
        f"  Sortino Ratio: {metrics.sortino_ratio:.2f}",
        f"  Max Drawdown: {metrics.max_drawdown_percent:.2f}%",
        f"  Profit Factor: {metrics.profit_factor:.2f}",
        f"  Expectancy: {metrics.expectancy:.4f}%",
        f"  Recovery Factor: {metrics.recovery_factor:.2f}",
        "",
        "📉 СЕРИИ",
        f"  Макс. побед подряд: {metrics.max_consecutive_wins}",
        f"  Макс. убытков подряд: {metrics.max_consecutive_losses}",
        "",
        "💵 КАПИТАЛ",
        f"  Финальный эквити: ${metrics.final_equity:,.2f}",
        f"  Пик эквити: ${metrics.peak_equity:,.2f}",
        "",
        "=" * 50,
    ]
    
    return "\n".join(lines)
