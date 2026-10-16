from pathlib import Path
import time

from dotenv import load_dotenv

from binance_client import check_connection, create_client
from config import load_strategy
from entry_strategy import evaluate_entry
from market_data import fetch_candles
from database import Database
from paper_trader import PaperTrader


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    load_dotenv(ROOT / ".env")
    strategy = load_strategy(ROOT / "config" / "strategy.json")
    if not strategy.get("testnet", True):
        raise RuntimeError("Safety check failed: testnet must be true")

    print(f"CryptoLab configured for {strategy['symbol']}")
    print("Connecting to Binance Spot Testnet...")

    client = create_client()
    exchange_info, account = check_connection(client, strategy["symbol"])
    symbols = getattr(exchange_info, "symbols", []) or []
    if not symbols:
        raise RuntimeError(f"Symbol not found: {strategy['symbol']}")
    symbol_info = symbols[0]
    account_balances = getattr(account, "balances", []) or []
    balances = [
        item for item in account_balances
        if float(getattr(item, "free", 0) or 0)
        or float(getattr(item, "locked", 0) or 0)
    ]

    print(f"Symbol status: {getattr(symbol_info, 'status', 'unknown')}")
    print("Account connection: OK")
    print("Non-zero balances:")
    for balance in balances:
        print(
            f"  {balance.asset}: free={balance.free}, "
            f"locked={balance.locked}"
        )
    market = strategy["market"]
    timeframe = market["timeframe"]
    interval = market["check_interval_seconds"]
    processed_close_time = None
    database = Database(ROOT / "data" / "cryptolab.db")
    paper_trader = PaperTrader(database, strategy)
    print(f"Monitoring {strategy['symbol']} / {timeframe} every {interval}s")
    print("Signal-only mode: no order will be submitted.")

    try:
        while True:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking market...")
            candles = fetch_candles(client, strategy["symbol"], timeframe, 250)
            if len(candles) < 2:
                print("Not enough candles yet")
                time.sleep(interval)
                continue

            # The final candle is still open; evaluate the latest completed one.
            completed_candles = candles[:-1]
            paper_trader.update(strategy["symbol"], candles[-1]["close"])
            close_time = completed_candles[-1]["close_time"]
            if close_time != processed_close_time:
                signal = evaluate_entry(completed_candles, strategy)
                print(f"\nCandle close: {signal['close']}")
                for name, valid in signal["signals"].items():
                    print(f"  {name}: {'VALID' if valid else 'INVALID'}")
                print(f"Confirmations: {signal['confirmations']}")
                print(f"Decision: {'BUY signal' if signal['buy'] else 'WAIT'}")
                database.save_signal(strategy["symbol"], timeframe, close_time, signal)
                paper_trader.on_signal(strategy["symbol"], signal["close"], signal["buy"])
                print("Signal saved to SQLite.")
                processed_close_time = close_time
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    finally:
        database.close()


if __name__ == "__main__":
    main()
