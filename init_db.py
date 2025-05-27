import requests
import time
from crypto_analyzer import CryptoDataManager

# API Configuration
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
CRYPTOPANIC_URL = "https://cryptopanic.com/api/v1/posts/"
API_KEY = "716e8f410469cf6d77baaa48dd00821822e4ab97"

# List of coins to track
COIN_IDS = [
    "bitcoin",
    "trump",
    "ethereum",
    "solana",
    "cardano",
    "dogecoin",
    "ripple",
    "polkadot",
    "litecoin",
    "chainlink",
    "uniswap",
]


def fetch_price_data():
    """Fetch price data from CoinGecko"""
    params = {"vs_currency": "usd", "ids": ",".join(COIN_IDS)}
    try:
        response = requests.get(COINGECKO_URL, params=params)
        response.raise_for_status()
        print("✅ Fetched price data successfully")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch price data: {e}")
        return []


def fetch_news():
    """Fetch news from CryptoPanic"""
    params = {
        "auth_token": API_KEY,
        "currencies": ",".join([coin.upper() for coin in COIN_IDS]),
    }
    try:
        response = requests.get(CRYPTOPANIC_URL, params=params)
        response.raise_for_status()
        print("✅ Fetched news data successfully")
        return response.json().get("results", [])
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch news data: {e}")
        return []


def initialize_database(data_points=12):
    """
    Initialize the database with multiple data points
    Args:
        data_points (int): Number of data points to collect (each 5 minutes apart)
    """
    print(f"Starting database initialization with {data_points} data points...")

    # Initialize the CryptoDataManager
    manager = CryptoDataManager(coin_ids=COIN_IDS)
    print("✅ CryptoDataManager initialized")

    # Collect initial data points
    for i in range(data_points):
        print(f"\nCollecting data point {i+1}/{data_points}")

        # Fetch and store price data
        prices = fetch_price_data()
        if prices:
            manager.store_price_data(prices)
            print(f"✅ Stored price data for {len(prices)} coins")

        # Fetch and store news data
        news = fetch_news()
        if news:
            manager.store_news_data(news)
            print(f"✅ Stored {len(news)} news articles")

        # Wait 5 minutes before next data point (except for last iteration)
        if i < data_points - 1:
            print("Waiting 5 minutes before next data collection...")
            time.sleep(300)  # 5 minutes

    # Initialize the model
    print("\nFitting scaler...")
    manager.fit_scaler()

    print("\nTraining model...")
    manager.fit_model()

    return manager


if __name__ == "__main__":
    print("🚀 Starting database initialization process...")

    # Initialize database with 12 data points (1 hour of data)
    manager = initialize_database(data_points=12)

    print("\n✅ Database initialization complete!")
    print("You can now start your Flask backend server.")
