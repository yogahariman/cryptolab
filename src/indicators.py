def bollinger_bands(closes: list[float], period: int, stddev: float) -> dict:
    window = closes[-period:]
    mean = sum(window) / period
    variance = sum((value - mean) ** 2 for value in window) / period
    deviation = variance ** 0.5
    return {"middle": mean, "upper": mean + stddev * deviation, "lower": mean - stddev * deviation}


def stochastic(candles: list[dict], k_period: int, d_period: int) -> dict:
    if len(candles) < k_period + d_period - 1:
        raise ValueError("Not enough candles for stochastic calculation")
    values = []
    for index in range(k_period - 1, len(candles)):
        window = candles[index - k_period + 1:index + 1]
        highest = max(item["high"] for item in window)
        lowest = min(item["low"] for item in window)
        values.append(100.0 if highest == lowest else (candles[index]["close"] - lowest) / (highest - lowest) * 100)
    d_values = values[-d_period:]
    return {"k": values[-1], "d": sum(d_values) / len(d_values), "previous_k": values[-2], "previous_d": sum(values[-d_period-1:-1]) / d_period}


def ema(closes: list[float], period: int) -> float:
    result = sum(closes[:period]) / period
    multiplier = 2 / (period + 1)
    for close in closes[period:]:
        result = (close - result) * multiplier + result
    return result
