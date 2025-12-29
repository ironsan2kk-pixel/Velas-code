"""
VELAS State Manager - персистентное состояние системы.

Использует SQLite для хранения:
- Открытых позиций
- Истории сигналов
- Истории сделок
- Настроек системы

Обеспечивает:
- Восстановление состояния после рестарта
- Логирование событий
- Синхронизацию между компонентами
"""

import sqlite3
import json
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    """Статус системы."""
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class StateConfig:
    """Конфигурация state manager."""
    
    db_path: str = "data/velas.db"
    auto_commit: bool = True
    journal_mode: str = "WAL"  # Write-Ahead Logging для производительности


class StateManager:
    """
    Менеджер состояния системы.
    
    Хранит:
    - Позиции (positions)
    - Сигналы (signals)
    - История (history)
    - Настройки (settings)
    - Логи (events)
    
    Использование:
        state = StateManager("data/velas.db")
        
        # Сохраняем позицию
        state.save_position(position_dict)
        
        # Загружаем все позиции
        positions = state.get_open_positions()
        
        # Сохраняем настройку
        state.set_setting("trading_mode", "paper")
    """
    
    def __init__(self, config: StateConfig = None):
        """
        Args:
            config: Конфигурация или путь к БД
        """
        self.config = config or StateConfig()
        self.db_path = Path(self.config.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
    
    def _init_db(self) -> None:
        """Инициализировать базу данных."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Настройки производительности
            cursor.execute(f"PRAGMA journal_mode = {self.config.journal_mode}")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA cache_size = 10000")
            cursor.execute("PRAGMA temp_store = MEMORY")
            
            # Таблица позиций
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    preset_id TEXT,
                    direction TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    current_price REAL NOT NULL,
                    tp_prices TEXT,
                    sl_price REAL NOT NULL,
                    current_sl REAL NOT NULL,
                    quantity REAL NOT NULL,
                    notional_value REAL NOT NULL,
                    leverage INTEGER DEFAULT 10,
                    status TEXT DEFAULT 'open',
                    tp_hits TEXT,
                    position_remaining REAL DEFAULT 100,
                    realized_pnl REAL DEFAULT 0,
                    entry_time TEXT NOT NULL,
                    last_update TEXT NOT NULL,
                    extra_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица сигналов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    tp_prices TEXT,
                    sl_price REAL NOT NULL,
                    preset_index INTEGER,
                    strength TEXT,
                    filters_passed TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    processed_at TEXT,
                    extra_data TEXT
                )
            """)
            
            # Таблица истории сделок
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    position_id TEXT NOT NULL,
                    signal_id TEXT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    notional_value REAL NOT NULL,
                    pnl_percent REAL NOT NULL,
                    pnl_amount REAL NOT NULL,
                    tp_hits TEXT,
                    exit_reason TEXT NOT NULL,
                    entry_time TEXT NOT NULL,
                    exit_time TEXT NOT NULL,
                    duration_minutes INTEGER,
                    extra_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица настроек
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица событий/логов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    symbol TEXT,
                    message TEXT NOT NULL,
                    data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Индексы
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_symbol ON history(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at)")
            
            conn.commit()
            logger.info(f"Database initialized: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Получить соединение с БД."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # ========== Positions ==========
    
    def save_position(self, position: dict) -> bool:
        """
        Сохранить или обновить позицию.
        
        Args:
            position: Словарь с данными позиции
            
        Returns:
            True если успешно
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO positions (
                        id, symbol, timeframe, preset_id, direction,
                        entry_price, current_price, tp_prices, sl_price, current_sl,
                        quantity, notional_value, leverage, status, tp_hits,
                        position_remaining, realized_pnl, entry_time, last_update, extra_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    position.get("id", ""),
                    position.get("symbol", ""),
                    position.get("timeframe", ""),
                    position.get("preset_id", ""),
                    position.get("direction", "long"),
                    position.get("entry_price", 0),
                    position.get("current_price", 0),
                    json.dumps(position.get("tp_prices", [])),
                    position.get("sl_price", 0),
                    position.get("current_sl", 0),
                    position.get("quantity", 0),
                    position.get("notional_value", 0),
                    position.get("leverage", 10),
                    position.get("status", "open"),
                    json.dumps(position.get("tp_hits", [])),
                    position.get("position_remaining", 100),
                    position.get("realized_pnl", 0),
                    position.get("entry_time", datetime.now().isoformat()),
                    position.get("last_update", datetime.now().isoformat()),
                    json.dumps(position.get("extra_data", {})),
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving position: {e}")
            return False
    
    def get_position(self, position_id: str) -> Optional[dict]:
        """Получить позицию по ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM positions WHERE id = ?", (position_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_position(row)
            return None
    
    def get_position_by_symbol(self, symbol: str) -> Optional[dict]:
        """Получить открытую позицию по символу."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM positions WHERE symbol = ? AND status = 'open'",
                (symbol,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_position(row)
            return None
    
    def get_open_positions(self) -> List[dict]:
        """Получить все открытые позиции."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM positions WHERE status = 'open'")
            rows = cursor.fetchall()
            
            return [self._row_to_position(row) for row in rows]
    
    def delete_position(self, position_id: str) -> bool:
        """Удалить позицию."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM positions WHERE id = ?", (position_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting position: {e}")
            return False
    
    def _row_to_position(self, row: sqlite3.Row) -> dict:
        """Конвертировать строку БД в словарь позиции."""
        return {
            "id": row["id"],
            "symbol": row["symbol"],
            "timeframe": row["timeframe"],
            "preset_id": row["preset_id"],
            "direction": row["direction"],
            "entry_price": row["entry_price"],
            "current_price": row["current_price"],
            "tp_prices": json.loads(row["tp_prices"]) if row["tp_prices"] else [],
            "sl_price": row["sl_price"],
            "current_sl": row["current_sl"],
            "quantity": row["quantity"],
            "notional_value": row["notional_value"],
            "leverage": row["leverage"],
            "status": row["status"],
            "tp_hits": json.loads(row["tp_hits"]) if row["tp_hits"] else [],
            "position_remaining": row["position_remaining"],
            "realized_pnl": row["realized_pnl"],
            "entry_time": row["entry_time"],
            "last_update": row["last_update"],
            "extra_data": json.loads(row["extra_data"]) if row["extra_data"] else {},
        }
    
    # ========== Signals ==========
    
    def save_signal(self, signal: dict) -> int:
        """
        Сохранить сигнал.
        
        Returns:
            ID сигнала в БД
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO signals (
                        signal_id, symbol, timeframe, signal_type,
                        entry_price, tp_prices, sl_price, preset_index,
                        strength, filters_passed, status, extra_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal.get("signal_id", ""),
                    signal.get("symbol", ""),
                    signal.get("timeframe", ""),
                    signal.get("signal_type", ""),
                    signal.get("entry_price", 0),
                    json.dumps(signal.get("tp_prices", [])),
                    signal.get("sl_price", 0),
                    signal.get("preset_index", 0),
                    signal.get("strength", "normal"),
                    json.dumps(signal.get("filters_passed", {})),
                    signal.get("status", "pending"),
                    json.dumps(signal.get("extra_data", {})),
                ))
                
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Error saving signal: {e}")
            return 0
    
    def update_signal_status(self, signal_id: str, status: str) -> bool:
        """Обновить статус сигнала."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE signals 
                    SET status = ?, processed_at = ?
                    WHERE signal_id = ?
                """, (status, datetime.now().isoformat(), signal_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating signal status: {e}")
            return False
    
    def get_pending_signals(self) -> List[dict]:
        """Получить необработанные сигналы."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM signals WHERE status = 'pending' ORDER BY created_at")
            rows = cursor.fetchall()
            
            return [self._row_to_signal(row) for row in rows]
    
    def get_recent_signals(self, limit: int = 50) -> List[dict]:
        """Получить последние сигналы."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM signals ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            
            return [self._row_to_signal(row) for row in rows]
    
    def _row_to_signal(self, row: sqlite3.Row) -> dict:
        """Конвертировать строку БД в словарь сигнала."""
        return {
            "id": row["id"],
            "signal_id": row["signal_id"],
            "symbol": row["symbol"],
            "timeframe": row["timeframe"],
            "signal_type": row["signal_type"],
            "entry_price": row["entry_price"],
            "tp_prices": json.loads(row["tp_prices"]) if row["tp_prices"] else [],
            "sl_price": row["sl_price"],
            "preset_index": row["preset_index"],
            "strength": row["strength"],
            "filters_passed": json.loads(row["filters_passed"]) if row["filters_passed"] else {},
            "status": row["status"],
            "created_at": row["created_at"],
            "processed_at": row["processed_at"],
            "extra_data": json.loads(row["extra_data"]) if row["extra_data"] else {},
        }
    
    # ========== History ==========
    
    def save_trade_history(self, trade: dict) -> int:
        """Сохранить закрытую сделку в историю."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Рассчитываем длительность
                entry_time = datetime.fromisoformat(trade.get("entry_time", datetime.now().isoformat()))
                exit_time = datetime.fromisoformat(trade.get("exit_time", datetime.now().isoformat()))
                duration = int((exit_time - entry_time).total_seconds() / 60)
                
                cursor.execute("""
                    INSERT INTO history (
                        position_id, signal_id, symbol, timeframe, direction,
                        entry_price, exit_price, quantity, notional_value,
                        pnl_percent, pnl_amount, tp_hits, exit_reason,
                        entry_time, exit_time, duration_minutes, extra_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade.get("position_id", ""),
                    trade.get("signal_id", ""),
                    trade.get("symbol", ""),
                    trade.get("timeframe", ""),
                    trade.get("direction", ""),
                    trade.get("entry_price", 0),
                    trade.get("exit_price", 0),
                    trade.get("quantity", 0),
                    trade.get("notional_value", 0),
                    trade.get("pnl_percent", 0),
                    trade.get("pnl_amount", 0),
                    json.dumps(trade.get("tp_hits", [])),
                    trade.get("exit_reason", ""),
                    trade.get("entry_time", ""),
                    trade.get("exit_time", ""),
                    duration,
                    json.dumps(trade.get("extra_data", {})),
                ))
                
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Error saving trade history: {e}")
            return 0
    
    def get_trade_history(
        self,
        symbol: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[dict]:
        """Получить историю сделок."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if symbol:
                cursor.execute("""
                    SELECT * FROM history 
                    WHERE symbol = ?
                    ORDER BY exit_time DESC 
                    LIMIT ? OFFSET ?
                """, (symbol, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM history 
                    ORDER BY exit_time DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_trade_stats(self, symbol: str = None) -> dict:
        """Получить статистику сделок."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            where_clause = "WHERE symbol = ?" if symbol else ""
            params = (symbol,) if symbol else ()
            
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl_amount > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(pnl_amount) as total_pnl,
                    AVG(pnl_percent) as avg_pnl_percent,
                    MAX(pnl_percent) as max_win_percent,
                    MIN(pnl_percent) as max_loss_percent,
                    AVG(duration_minutes) as avg_duration_minutes
                FROM history {where_clause}
            """, params)
            
            row = cursor.fetchone()
            
            total = row["total_trades"] or 0
            wins = row["winning_trades"] or 0
            
            return {
                "total_trades": total,
                "winning_trades": wins,
                "losing_trades": total - wins,
                "win_rate": round(wins / total * 100, 2) if total > 0 else 0,
                "total_pnl": round(row["total_pnl"] or 0, 2),
                "avg_pnl_percent": round(row["avg_pnl_percent"] or 0, 2),
                "max_win_percent": round(row["max_win_percent"] or 0, 2),
                "max_loss_percent": round(row["max_loss_percent"] or 0, 2),
                "avg_duration_minutes": round(row["avg_duration_minutes"] or 0, 1),
            }
    
    # ========== Settings ==========
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Сохранить настройку."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                value_str = json.dumps(value) if not isinstance(value, str) else value
                
                cursor.execute("""
                    INSERT OR REPLACE INTO settings (key, value, updated_at)
                    VALUES (?, ?, ?)
                """, (key, value_str, datetime.now().isoformat()))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Получить настройку."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            
            if row:
                try:
                    return json.loads(row["value"])
                except json.JSONDecodeError:
                    return row["value"]
            
            return default
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Получить все настройки."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            rows = cursor.fetchall()
            
            settings = {}
            for row in rows:
                try:
                    settings[row["key"]] = json.loads(row["value"])
                except json.JSONDecodeError:
                    settings[row["key"]] = row["value"]
            
            return settings
    
    def delete_setting(self, key: str) -> bool:
        """Удалить настройку."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM settings WHERE key = ?", (key,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting setting {key}: {e}")
            return False
    
    # ========== Events ==========
    
    def log_event(
        self,
        event_type: str,
        message: str,
        symbol: str = None,
        data: dict = None,
    ) -> None:
        """Записать событие."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO events (event_type, symbol, message, data)
                    VALUES (?, ?, ?, ?)
                """, (
                    event_type,
                    symbol,
                    message,
                    json.dumps(data) if data else None,
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging event: {e}")
    
    def get_events(
        self,
        event_type: str = None,
        symbol: str = None,
        limit: int = 100,
    ) -> List[dict]:
        """Получить события."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            if event_type:
                conditions.append("event_type = ?")
                params.append(event_type)
            
            if symbol:
                conditions.append("symbol = ?")
                params.append(symbol)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            params.append(limit)
            
            cursor.execute(f"""
                SELECT * FROM events {where_clause}
                ORDER BY created_at DESC LIMIT ?
            """, params)
            
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                event = dict(row)
                if event.get("data"):
                    try:
                        event["data"] = json.loads(event["data"])
                    except json.JSONDecodeError:
                        pass
                events.append(event)
            
            return events
    
    # ========== System Status ==========
    
    def set_system_status(self, status: SystemStatus) -> None:
        """Установить статус системы."""
        self.set_setting("system_status", status.value)
        self.log_event("system", f"Status changed to {status.value}")
    
    def get_system_status(self) -> SystemStatus:
        """Получить статус системы."""
        value = self.get_setting("system_status", "stopped")
        try:
            return SystemStatus(value)
        except ValueError:
            return SystemStatus.STOPPED
    
    # ========== Cleanup ==========
    
    def cleanup_old_events(self, days: int = 30) -> int:
        """Удалить старые события."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM events 
                    WHERE created_at < datetime('now', ?)
                """, (f'-{days} days',))
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error cleaning up events: {e}")
            return 0
    
    def vacuum(self) -> None:
        """Оптимизировать БД."""
        try:
            with self._get_connection() as conn:
                conn.execute("VACUUM")
                logger.info("Database vacuumed")
        except Exception as e:
            logger.error(f"Error vacuuming database: {e}")
