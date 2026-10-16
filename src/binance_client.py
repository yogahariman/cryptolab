import os

from binance_sdk_spot.spot import ConfigurationRestAPI, Spot


TESTNET_URL = "https://testnet.binance.vision"


def create_client() -> Spot:
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        raise RuntimeError(
            "BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env"
        )

    configuration = ConfigurationRestAPI(
        api_key=api_key,
        api_secret=api_secret,
        base_path=TESTNET_URL,
        timeout=10000,
        retries=3,
        backoff=1500,
    )
    return Spot(config_rest_api=configuration)


def check_connection(client: Spot, symbol: str) -> tuple[dict, dict]:
    exchange_info_response = client.rest_api.exchange_info(symbol=symbol)
    account_response = client.rest_api.get_account()
    return exchange_info_response.data(), account_response.data()
