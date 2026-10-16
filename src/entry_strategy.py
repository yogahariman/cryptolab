from indicators import bollinger_bands, ema, stochastic


def evaluate_entry(candles: list[dict], config: dict) -> dict:
    closes = [item["close"] for item in candles]
    indicators = config["indicators"]
    signals = {}

    bb_cfg = indicators["bollinger_bands"]
    bb = bollinger_bands(closes, bb_cfg["period"], bb_cfg["stddev"])
    signals["bollinger_bands"] = closes[-1] <= bb["lower"]

    st_cfg = indicators["stochastic"]
    st = stochastic(candles, st_cfg["k_period"], st_cfg["d_period"])
    signals["stochastic"] = st["k"] < st_cfg["oversold"] and st["k"] > st["d"] and st["previous_k"] <= st["previous_d"]

    ema_cfg = indicators["ema_filter"]
    ema_value = ema(closes, ema_cfg["period"])
    signals["ema_filter"] = closes[-1] > ema_value

    required = config["entry"]["required_signals"]
    optional = config["entry"]["optional_signals"]
    confirmations = sum(signals.get(name, False) for name in required + optional)
    required_valid = all(signals.get(name, False) for name in required)
    minimum = config["entry"]["minimum_confirmations"]
    return {"signals": signals, "confirmations": confirmations, "buy": required_valid and confirmations >= minimum, "close": closes[-1], "bb": bb, "stochastic": st, "ema": ema_value}
