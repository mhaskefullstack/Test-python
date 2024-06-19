import requests
from decimal import Decimal
from typing import NamedTuple

class Config:
    BIRD_EYE_TOKEN = "451846c7a9bc440d933652aba468b9e9" 

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
        """
        Internal method to make API calls with appropriate headers based on method type.
        """
        query_method = {
            "GET": requests.get,
            "POST": requests.post,
        }.get(method.upper())
        
        if not query_method:
            raise ValueError(f'Unrecognized method "{method}" passed for query - {query_url}')

        resp = query_method(query_url, *args, headers=self._headers, **kwargs)
        return resp

    def fetch_prices(self, token_addresses: list[str]) -> dict[str, NamedTuple]:
        """
        Fetches prices for a list of tokens from BirdEye API.

        Args:
            token_addresses (list[str]): A list of token addresses for which to fetch prices.

        Returns:
            dict[str, NamedTuple]: Mapping of token addresses to NamedTuple containing price and liquidity.

        Raises:
            ValueError: If no tokens are provided.
            Exception: If the API call was unsuccessful.
        """
        if not token_addresses:
            raise ValueError("No tokens provided")

        prices = {}
        for token_address in token_addresses:
            url = f"https://api.birdeye.so/v1/tokens/{token_address}/price"
            try:
                response = self._make_api_call("GET", url)
                response.raise_for_status()
                data = response.json()
                prices[token_address] = {
                    "price": Decimal(data.get("price", 0)),
                    "liquidity": Decimal(data.get("liquidity", 0)),
                }
            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to fetch price for token {token_address}: {str(e)}")

        return prices

    def fetch_token_overview(self, address: str) -> dict:
        """
        Fetches token overview for a token from BirdEye API.

        Args:
            address (str): The token address for which to fetch overview.

        Returns:
            dict: Token overview data.

        Raises:
            ValueError: If an invalid Solana address is passed.
            Exception: If the API call was unsuccessful.
        """
        try:
            # Check if the address is a valid Solana address
            PublicKey(address)
        except ValueError:
            raise ValueError(f"Invalid Solana address: {address}")

        url = f"https://api.birdeye.so/v1/tokens/{address}"
        try:
            response = self._make_api_call("GET", url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch token overview for {address}: {str(e)}")
