from decimal import Decimal
from typing import Any

import requests

from clients.common import PriceInfo, TokenOverview
from custom_exceptions import InvalidSolanaAddress, InvalidTokens, NoPositionsError
from utils.helpers import is_solana_address
from vars.constants import SOL_MINT


class DexScreenerClient:
    """
    Handler class to assist with all calls to DexScreener API
    """

    @staticmethod
    def _validate_token_address(token_address: str):
        """
        Validates token address to be a valid solana address

        Args:
            token_address (str): Token address to validate

        Returns:
            None: If token address is valid

        Raises:
            NoPositionsError: If token address is empty
            InvalidSolanaAddress: If token address is not a valid solana address
        """
        if not token_address:
            raise NoPositionsError("Token address cannot be empty")

        if not is_solana_address(token_address):
            raise InvalidSolanaAddress(f"Invalid Solana address: {token_address}")

    def _validate_token_addresses(self, token_addresses: list[str]):
        """
        Validates token addresses to be valid solana addresses

        Args:
            token_addresses (list[str]): Token addresses to validate

        Returns:
            None: If token addresses are valid

        Raises:
            NoPositionsError: If token addresses are empty
            InvalidSolanaAddress: If any token address is not a valid solana address
        """
        if not token_addresses:
            raise NoPositionsError("No token addresses provided")

        for token_address in token_addresses:
            self._validate_token_address(token_address)

    @staticmethod
    def _validate_response(resp: requests.Response):
        """
        Validates response from API to be 200

        Args:
            resp (requests.Response): Response from API

        Returns:
            None: If response is 200

        Raises:
            InvalidTokens: If response is not 200
        """
        if resp.status_code != 200:
            raise InvalidTokens(f"Invalid response from API: {resp.status_code}")

    def _call_api(self, token_address: str) -> dict[str, Any]:
        """
        Calls DexScreener API for a single token

        Args:
            token_address (str): Token address for which to fetch data

        Returns:
            dict[str, Any]: JSON response from API

        Raises:
            InvalidTokens: If response is not 200
            NoPositionsError: If token address is empty
            InvalidSolanaAddress: If token address is not a valid solana address
        """
        self._validate_token_address(token_address)
        url = f"https://api.dexscreener.com/v1/tokens/{token_address}"
        resp = requests.get(url)
        self._validate_response(resp)
        return resp.json()

    def _call_api_bulk(self, token_addresses: list[str]) -> dict[str, Any]:
        """
        Calls DexScreener API for multiple tokens

        Args:
            token_addresses (list[str]): Token addresses for which to fetch data

        Returns:
            dict[str, Any]: JSON response from API

        Raises:
            InvalidTokens: If response is not 200
            NoPositionsError: If token addresses are empty
            InvalidSolanaAddress: If any token address is not a valid solana address
        """
        self._validate_token_addresses(token_addresses)
        url = "https://api.dexscreener.com/v1/tokens"
        params = {"addresses": ",".join(token_addresses)}
        resp = requests.get(url, params=params)
        self._validate_response(resp)
        return resp.json()

    def fetch_prices_dex(self, token_addresses: list[str]) -> dict[str, PriceInfo[Decimal, Decimal]]:
        """
        For a list of tokens fetches their prices via multi API ensuring each token has a price

        Args:
            token_addresses (list[str]): A list of tokens for which to fetch prices

        Returns:
            dict[str, PriceInfo[Decimal, Decimal]]: Mapping of token to a named tuple PriceInfo with price and liquidity in Decimal

        Raises:
            InvalidTokens: Raised if the API call was unsuccessful
            NoPositionsError: Raised if no tokens are provided
            InvalidSolanaAddress: Raised if any token address is invalid
        """
        self._validate_token_addresses(token_addresses)
        prices = {}
        for token_address in token_addresses:
            try:
                data = self._call_api(token_address)
                prices[token_address] = PriceInfo(
                    price=Decimal(data.get("price", 0)),
                    liquidity=Decimal(data.get("liquidity", {}).get("usd", 0))
                )
            except (InvalidTokens, InvalidSolanaAddress, NoPositionsError) as e:
                # Log or handle exception as per your application's needs
                # For now, we'll just continue fetching prices for other tokens
                continue
        return prices

    def fetch_token_overview(self, address: str) -> TokenOverview:
        """
        For a token fetches their overview via Dex API ensuring each token has a price

        Args:
            address (str): A token address for which to fetch overview

        Returns:
            TokenOverview: Overview with a lot of token information I don't understand

        Raises:
            InvalidTokens: Raised if the API call was unsuccessful
            InvalidSolanaAddress: Raised if the token address is invalid
        """
        self._validate_token_address(address)
        try:
            data = self._call_api(address)
            return TokenOverview(data)  # Assuming TokenOverview constructor accepts JSON data
        except (InvalidTokens, InvalidSolanaAddress, NoPositionsError) as e:
            raise e  # Propagate the exception to the caller

    @staticmethod
    def find_largest_pool_with_sol(token_pairs, address):
        """
        Finds the largest pool with SOL as the quote token

        Args:
            token_pairs (list[dict]): List of token pairs data
            address (str): Address to match for base token

        Returns:
            dict: Details of the largest pool with SOL as the quote token
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
