from dexscreener import DexScreenerClient

if __name__ == "__main__":
    client = DexScreenerClient()

    token_addresses = [
        "WskzsKqEW3ZsmrhPAevfVZb6PuuLzWov9mJWZsfDePC",
        "2uvch6aviS6xE3yhWjVZnFrDw7skUtf6ubc7xYJEPpwj",
        "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
        "2LxZrcJJhzcAju1FBHuGvw929EVkX7R7Q8yA2cdp8q7b"
    ]

    try:
        prices = client.fetch_prices_dex(token_addresses)
        print("Prices fetched successfully:")
        for token, price_info in prices.items():
            print(f"{token}: Price - {price_info.price}, Liquidity - {price_info.liquidity}")
    except Exception as e:
        print(f"Error fetching prices: {str(e)}")

    try:
        overview = client.fetch_token_overview("So11111111111111111111111111111111111111112")
        print("Token overview fetched successfully:")
        print(overview)
    except Exception as e:
        print(f"Error fetching token overview: {str(e)}")
