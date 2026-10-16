# CryptoLab

Binance Spot trading bot foundation using JSON configuration and SQLite state.

The default configuration uses Binance Spot Testnet. Keep API keys in environment variables, never in Git.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export BINANCE_API_KEY="your-key"
export BINANCE_API_SECRET="your-secret"
```

This initial version only validates configuration and prepares the project structure. Live order execution will be added after reconciliation and risk checks are tested.
