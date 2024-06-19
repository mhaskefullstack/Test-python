import requests
from typing import NamedTuple, List, Dict
from decimal import Decimal
from solana.publickey import PublicKey

class PriceInfo(NamedTuple):
    price: Decimal
    liquidity: Decimal

class TokenOverview(NamedTuple):
    name: str
    symbol: str
    price: Decimal
    liquidity: Decimal
    market_cap: Decimal
    # Add more fields as required

class NoPositionsError(Exception):
    pass

class InvalidToken(Exception):
    pass

class InvalidSolanaAddress(Exception):
    pass

def is_solana_address(input_string: str) -> bool:
    try:
        PublicKey(input_string)
        return True
    except ValueError:
        return False

class BirdEyeClient:
    """
    Handler class to assist with all calls to BirdEye API
    """

    @property
    def _headers(self):
        return {
            "accept": "application/json",
            "x-chain": "solana",
            "X-API-KEY": Config.BIRD_EYE_TOKEN,
        }

    def _make_api_call(self, method: str, query_url: str, *args, **kwargs) -> requests.Response:
        match method.upper():
            case "GET":
                query_method = requests.get
            case "POST":
                query_method = requests.post
            case _:
                raise ValueError(f'Unrecognized method "{method}" passed for query - {query_url}')
        resp = query_method(query_url, *args, headers=self._headers, **kwargs)
        return resp

    def fetch_prices(self, token_addresses: List[str]) -> Dict[str, PriceInfo]:
        if not token_addresses:
            raise NoPositionsError("No token addresses provided")

        url = "https://public-api.birdeye.so/v1/multi_price"
        response = self._make_api_call("GET", url, params={"addresses": ",".join(token_addresses)})

        if response.status_code != 200:
            raise InvalidToken("Failed to fetch token prices")

        data = response.json()
        prices = {}

        for token in token_addresses:
            token_data = data.get(token)
            if token_data:
                prices[token] = PriceInfo(
                    price=Decimal(token_data["price"]),
                    liquidity=Decimal(token_data["liquidity"])
                )
            else:
                raise InvalidToken(f"Token {token} data is not available")

        return prices

    def fetch_token_overview(self, address: str) -> TokenOverview:
        if not is_solana_address(address):
            raise InvalidSolanaAddress(f"Invalid Solana address: {address}")

        url = f"https://public-api.birdeye.so/v1/token/{address}"
        response = self._make_api_call("GET", url)

        if response.status_code != 200:
            raise InvalidToken(f"Failed to fetch token overview for {address}")

        data = response.json()
        
        return TokenOverview(
            name=data["name"],
            symbol=data["symbol"],
            price=Decimal(data["price"]),
            liquidity=Decimal(data["liquidity"]),
            market_cap=Decimal(data["market_cap"]),
            # Add more fields as required
        )
