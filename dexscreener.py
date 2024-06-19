import requests
from decimal import Decimal
from typing import Dict, List
from clients.common import PriceInfo, TokenOverview
from custom_exceptions import InvalidSolanaAddress, InvalidToken, NoPositionsError
from vars.constants import SOL_MINT
from utils.helpers import is_solana_address

class DexScreenerClient:
    """
    Client for DexScreener APIs
    """

    def __init__(self):
        self.base_url = "https://api.dexscreener.com/v1"

    @staticmethod
    def _validate_token_address(token_address: str):
        """
        Validates token address to be a valid Solana address

        Args:
            token_address (str): Token address to validate

        Raises:
            InvalidSolanaAddress: If token address is not a valid Solana address
        """
        if not is_solana_address(token_address):
            raise InvalidSolanaAddress(f"Invalid Solana address: {token_address}")

    def _make_api_call(self, method: str, endpoint: str, params: dict = None) -> requests.Response:
        """
        Makes an API call to DexScreener API.

        Args:
            method (str): HTTP method ('GET', 'POST', etc.)
            endpoint (str): API endpoint
            params (dict, optional): Query parameters

        Returns:
            requests.Response: Response object from the API call

        Raises:
            InvalidToken: If API call fails
        """
        url = self.base_url + endpoint
        try:
            response = requests.request(method, url, params=params)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise InvalidToken(f"Request failed: {e}")

    def fetch_prices_dex(self, token_addresses: List[str]) -> Dict[str, PriceInfo]:
        """
        Fetches token prices from DexScreener API.

        Args:
            token_addresses (List[str]): List of token addresses

        Returns:
            Dict[str, PriceInfo]: Mapping of token addresses to PriceInfo objects containing price and liquidity

        Raises:
            NoPositionsError: If no token addresses are provided
            InvalidToken: If API call fails or token data is not available
        """
        if not token_addresses:
            raise NoPositionsError("No token addresses provided")

        prices = {}
        for token_address in token_addresses:
            try:
                self._validate_token_address(token_address)
                endpoint = f"/tokens/{token_address}/prices"
                response = self._make_api_call("GET", endpoint)
                data = response.json()

                if data is None:
                    raise InvalidToken(f"Token {token_address} data is not available")

                prices[token_address] = PriceInfo(
                    price=Decimal(data["price"]),
                    liquidity=Decimal(data["liquidity"]),
                )

            except InvalidToken as e:
                raise e
            except Exception as e:
                raise InvalidToken(f"Failed to fetch prices for token {token_address}: {e}")

        return prices

    def fetch_token_overview(self, address: str) -> TokenOverview:
        """
        Fetches token overview from DexScreener API.

        Args:
            address (str): Token address

        Returns:
            TokenOverview: Token overview containing name, symbol, price, liquidity, and market cap

        Raises:
            InvalidSolanaAddress: If the provided address is not a valid Solana address
            InvalidToken: If API call fails or token data is not available
        """
        try:
            self._validate_token_address(address)
            endpoint = f"/tokens/{address}/overview"
            response = self._make_api_call("GET", endpoint)
            data = response.json()

            return TokenOverview(
                name=data["name"],
                symbol=data["symbol"],
                price=Decimal(data["price"]),
                liquidity=Decimal(data["liquidity"]),
                market_cap=Decimal(data["market_cap"]),
            )

        except InvalidToken as e:
            raise e
        except Exception as e:
            raise InvalidToken(f"Failed to fetch overview for token {address}: {e}")

    @staticmethod
    def find_largest_pool_with_sol(token_pairs, address):
        """
        Finds the largest pool with SOL token as the quote token.

        Args:
            token_pairs (list): List of token pairs
            address (str): Token address to match in baseToken

        Returns:
            dict: Entry with the largest liquidity in USD with SOL as quote token
        """
        max_entry = {}
        max_liquidity_usd = -1

        for entry in token_pairs:
            if entry.get("baseToken", {}).get("address") == address and entry["quoteToken"]["address"] == SOL_MINT:
                liquidity_usd = float(entry.get("liquidity", {}).get("usd", 0))
                if liquidity_usd > max_liquidity_usd:
                    max_liquidity_usd = liquidity_usd
                    max_entry = entry

        return max_entry
