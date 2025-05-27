from flask import Flask, jsonify, Response
from flask_cors import CORS
import requests
import json
import time
from threading import Thread
from crypto_analyzer import CryptoDataManager

app = Flask(__name__)
CORS(app)

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
CRYPTOPANIC_URL = "https://cryptopanic.com/api/v1/posts/"
API_KEY = "716e8f410469cf6d77baaa48dd00821822e4ab97"

coin_ids = ["bitcoin", "ethereum", "solana", "cardano", "dogecoin", "ripple", "polkadot", "litecoin", "chainlink", "uniswap"]

# Initialize the analyzer
analyzer = CryptoDataManager(coin_ids=coin_ids)

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

def create_analysis_response(prices, news, analyzer):
    """Create response with price, news, and analysis data"""
    response = {
        'prices': prices,
        'news': news,
        'analysis': {},
        'model_ready': analyzer.is_scaler_fitted
    }
    
    if analyzer.is_scaler_fitted:
        # Add analysis for each coin
        for price in prices:
            analysis = analyzer.predict_movement(price['id'])
            if analysis:
                response['analysis'][price['id']] = analysis
    
    return response

def initialize_analyzer():
    """Initialize the analyzer with any available data"""
    while not analyzer.is_scaler_fitted:
        try:
            print("Attempting to initialize analyzer...")
            prices = fetch_price_data()
            news = fetch_news()
            
            if prices:
                analyzer.store_price_data(prices)
            if news:
                analyzer.store_news_data(news)
            
            # Try to fit with whatever data we have
            analyzer.fit_scaler()
            analyzer.fit_model()
            print("✅ Initial model training complete")
            break
        except Exception as e:
            print(f"⚠️ Initial training incomplete (will retry in 5 seconds): {e}")
            time.sleep(5)

@app.route("/")
def home():
    """Home route - provides API information"""
    return jsonify({
        "message": "🚀 Crypto Analysis API is running!",
        "status": "active",
        "endpoints": {
            "/crypto-data": "Get current crypto prices, news, and analysis",
            "/crypto-stream": "Real-time streaming crypto data (SSE)",
        },
        "supported_coins": coin_ids,
        "model_status": "ready" if analyzer.is_scaler_fitted else "initializing"
    })

@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_ready": analyzer.is_scaler_fitted,
        "timestamp": int(time.time())
    })

@app.route("/crypto-data", methods=["GET"])
def get_crypto_data():
    prices = fetch_price_data()
    news = fetch_news()
    
    # Store data for analysis
    if prices:
        analyzer.store_price_data(prices)
    if news:
        analyzer.store_news_data(news)
    
    # Generate response with analysis
    response = create_analysis_response(prices, news, analyzer)
    return jsonify(response)

@app.route("/crypto-stream")
def crypto_stream():
    def generate():
        while True:
            try:
                prices = fetch_price_data()
                news = fetch_news()
                
                # Store and analyze data
                if prices:
                    analyzer.store_price_data(prices)
                if news:
                    analyzer.store_news_data(news)
                
                # If model isn't fitted yet, try to fit it
                if not analyzer.is_scaler_fitted:
                    try:
                        analyzer.fit_scaler()
                        analyzer.fit_model()
                        print("✅ Model training complete during stream")
                    except Exception as e:
                        print(f"⚠️ Model training incomplete: {e}")
                
                # Generate response with analysis
                response = create_analysis_response(prices, news, analyzer)
                yield f"data: {json.dumps(response)}\n\n"
                
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
    print("Initializing analyzer...")
    # Start analyzer initialization in a separate thread
    init_thread = Thread(target=initialize_analyzer)
    init_thread.start()
    
    # Start the Flask app
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)