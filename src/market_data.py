from binance_sdk_spot.rest_api.models import KlinesIntervalEnum


def fetch_candles(client, symbol: str, timeframe: str = "15m", limit: int = 250) -> list[dict]:
    interval = KlinesIntervalEnum(f"{timeframe}")
    response = client.rest_api.klines(symbol, interval, limit=limit)
    rows = response.data()
    candles = []
    for row in rows:
        values = row if isinstance(row, list) else row.model_dump()
        candles.append({
            "open_time": int(values[0]),
            "open": float(values[1]),
            "high": float(values[2]),
            "low": float(values[3]),
            "close": float(values[4]),
            "volume": float(values[5]),
            "close_time": int(values[6]),
        })
    return candles
