import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self._create_tables()
        columns = {row[1] for row in self.connection.execute("PRAGMA table_info(paper_positions)")}
        if "last_entry_price" not in columns:
            self.connection.execute("ALTER TABLE paper_positions ADD COLUMN last_entry_price REAL NOT NULL DEFAULT 0")
            self.connection.execute("UPDATE paper_positions SET last_entry_price = average_price WHERE last_entry_price = 0")
            self.connection.commit()

    def _create_tables(self) -> None:
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS signal_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                candle_close_time INTEGER NOT NULL,
                close_price REAL NOT NULL,
                bollinger_valid INTEGER NOT NULL,
                stochastic_valid INTEGER NOT NULL,
                ema_valid INTEGER NOT NULL,
                confirmations INTEGER NOT NULL,
                decision TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(symbol, timeframe, candle_close_time)
            )
        """)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS paper_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                status TEXT NOT NULL,
                total_quantity REAL NOT NULL,
                total_cost REAL NOT NULL,
                average_price REAL NOT NULL,
                last_entry_price REAL NOT NULL,
                current_level INTEGER NOT NULL,
                target_price REAL NOT NULL,
                opened_at TEXT NOT NULL,
                closed_at TEXT
            )
        """)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS paper_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                level INTEGER NOT NULL,
                side TEXT NOT NULL,
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                quote_amount REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(position_id) REFERENCES paper_positions(id)
            )
        """)
        self.connection.commit()

    def save_signal(self, symbol: str, timeframe: str, close_time: int, signal: dict) -> None:
        values = signal["signals"]
        created_at = datetime.now(timezone.utc).isoformat()
        self.connection.execute("""
            INSERT OR IGNORE INTO signal_logs (
                symbol, timeframe, candle_close_time, close_price,
                bollinger_valid, stochastic_valid, ema_valid,
                confirmations, decision, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol, timeframe, close_time, signal["close"],
            int(values.get("bollinger_bands", False)),
            int(values.get("stochastic", False)),
            int(values.get("ema_filter", False)),
            signal["confirmations"],
            "BUY" if signal["buy"] else "WAIT",
            created_at,
        ))
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def get_open_position(self, symbol: str):
        return self.connection.execute(
            "SELECT * FROM paper_positions WHERE symbol = ? AND status = 'OPEN' ORDER BY id DESC LIMIT 1",
            (symbol,),
        ).fetchone()

    def open_paper_position(self, symbol: str, price: float, amount: float, target_price: float) -> int:
        now = datetime.now(timezone.utc).isoformat()
        quantity = amount / price
        cursor = self.connection.execute(
            "INSERT INTO paper_positions (symbol, status, total_quantity, total_cost, average_price, last_entry_price, current_level, target_price, opened_at) VALUES (?, 'OPEN', ?, ?, ?, ?, 0, ?, ?)",
            (symbol, quantity, amount, price, price, target_price, now),
        )
        position_id = cursor.lastrowid
        self._save_trade(position_id, symbol, 0, "BUY", price, quantity, amount)
        self.connection.commit()
        return position_id

    def add_paper_level(self, position, symbol: str, level: int, price: float, amount: float, target_price: float) -> None:
        position_id, _, _, total_quantity, total_cost, _, _, _, _, _, _ = position
        quantity = amount / price
        new_quantity = total_quantity + quantity
        new_cost = total_cost + amount
        average = new_cost / new_quantity
        self.connection.execute(
            "UPDATE paper_positions SET total_quantity = ?, total_cost = ?, average_price = ?, last_entry_price = ?, current_level = ?, target_price = ? WHERE id = ?",
            (new_quantity, new_cost, average, price, level, target_price, position_id),
        )
        self._save_trade(position_id, symbol, level, "BUY", price, quantity, amount)
        self.connection.commit()

    def close_paper_position(self, position, price: float) -> None:
        position_id = position[0]
        self.connection.execute(
            "UPDATE paper_positions SET status = 'CLOSED', closed_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), position_id),
        )
        self._save_trade(position_id, position[1], position[7], "SELL", price, position[3], position[3] * price)
        self.connection.commit()

    def _save_trade(self, position_id, symbol, level, side, price, quantity, amount) -> None:
        self.connection.execute(
            "INSERT INTO paper_trades (position_id, symbol, level, side, price, quantity, quote_amount, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (position_id, symbol, level, side, price, quantity, amount, datetime.now(timezone.utc).isoformat()),
        )
