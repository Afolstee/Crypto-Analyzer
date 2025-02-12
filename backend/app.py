from flask import Flask, jsonify, Response
from flask_cors import CORS
import requests
import json
import time
from threading import Thread

app = Flask(__name__)
CORS(app)

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
CRYPTOPANIC_URL = "https://cryptopanic.com/api/v1/posts/"
API_KEY = "716e8f410469cf6d77baaa48dd00821822e4ab97"

coin_ids = ["bitcoin", "ethereum", "solana", "cardano", "dogecoin", "ripple", "polkadot", "litecoin", "chainlink", "uniswap"]

def fetch_price_data():
    params = {"vs_currency": "usd", "ids": ",".join(coin_ids)}
    response = requests.get(COINGECKO_URL, params=params)
    if response.status_code == 200:
        print("✅ Fetched price data successfully")
        return response.json()
    else:
        print(f"❌ Failed to fetch price data. Status code: {response.status_code}")
        return []

def fetch_news():
    params = {"auth_token": API_KEY, "currencies": ",".join([coin.upper() for coin in coin_ids])}
    response = requests.get(CRYPTOPANIC_URL, params=params)
    if response.status_code == 200:
        print("✅ Fetched news data successfully")
        return response.json().get("results", [])
    else:
        print(f"❌ Failed to fetch news data. Status code: {response.status_code}")
        return []

@app.route("/crypto-data", methods=["GET"])
def get_crypto_data():
    prices = fetch_price_data()
    news = fetch_news()
    return jsonify({"prices": prices, "news": news})

@app.route("/crypto-stream")
def crypto_stream():
    def generate():
        while True:
            try:
                prices = fetch_price_data()
                news = fetch_news()
                data = json.dumps({"prices": prices, "news": news})
                yield f"data: {data}\n\n"
                time.sleep(5)
            except Exception as e:
                print(f"Error in stream: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                time.sleep(5)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked",
            "Access-Control-Allow-Origin": "*"
        }
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)