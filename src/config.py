import json
from pathlib import Path


def load_strategy(path: str | Path) -> dict:
    config_path = Path(path)
    with config_path.open(encoding="utf-8") as file:
        config = json.load(file)
    required = {
        "symbol",
        "market",
        "levels",
        "take_profit_percent",
        "max_levels",
        "entry",
        "indicators",
    }
    missing = required - config.keys()
    if missing:
        raise ValueError(f"Missing strategy fields: {', '.join(sorted(missing))}")
    entry = config["entry"]
    market = config["market"]
    if not market.get("timeframe") or market.get("check_interval_seconds", 0) <= 0:
        raise ValueError("market timeframe and positive check_interval_seconds are required")
    for field in ("required_signals", "optional_signals", "minimum_confirmations"):
        if field not in entry:
            raise ValueError(f"Missing entry field: {field}")

    signal_names = set(entry["required_signals"]) | set(entry["optional_signals"])
    missing_indicators = signal_names - set(config["indicators"])
    if missing_indicators:
        raise ValueError(
            "Missing indicator configuration: "
            + ", ".join(sorted(missing_indicators))
        )
    return config
