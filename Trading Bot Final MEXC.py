# -*- coding: utf-8 -*-
"""
Created on Sat Jun 28 20:51:35 2025

@author: HP
"""
import requests
import time
import hmac
import hashlib
import threading
import random
API_KEY = ''
SECRET_KEY = ''
SYMBOLS = ['NODEUSDT', 'COPPERUSDT', 'FRAGUSDT']
PAIRS = {} 
CHECK_INTERVAL = 0.05
MAX_REQUESTS_PER_SECOND = 10
BASE_URL = 'https://api.mexc.com'
ORDER_ENDPOINT = '/api/v3/order'
TIME_ENDPOINT = '/api/v3/time'
ORDERBOOK_ENDPOINT = '/api/v3/depth'
last_request_time = {}
def throttle(symbol):
    now = time.time()
    last_time = last_request_time.get(symbol, 0)
    wait_time = max(0, (1 / MAX_REQUESTS_PER_SECOND) - (now - last_time))
    if wait_time > 0:
        time.sleep(wait_time)
    last_request_time[symbol] = time.time()
def get_server_time():
    throttle('time')
    response = requests.get(BASE_URL + TIME_ENDPOINT)
    return response.json()['serverTime']
def create_signature(data_string, secret):
    return hmac.new(secret.encode(), data_string.encode(), hashlib.sha256).hexdigest()
def is_pair_live(symbol):
    try:
        throttle(symbol)
        res = requests.get(f"{BASE_URL}{ORDERBOOK_ENDPOINT}?symbol={symbol}&limit=1")
        if res.status_code == 200 and 'bids' in res.json():
            return True
        return False
    except Exception as e:
        print(f"Error checking {symbol} status:", e)
        return False
def place_market_order(symbol, amount):
    try:
        timestamp = get_server_time()
        params = {
            'symbol': symbol,
            'side': 'BUY',
            'type': 'MARKET',
            'quoteOrderQty': amount,
            'timestamp': timestamp
        }

        query_string = '&'.join([f"{key}={params[key]}" for key in params])
        signature = create_signature(query_string, SECRET_KEY)
        url = f"{BASE_URL}{ORDER_ENDPOINT}?{query_string}&signature={signature}"

        headers = {'X-MEXC-APIKEY': API_KEY}
        response = requests.post(url, headers=headers)
        return response.json()
    except Exception as e:
        return {"error": str(e)}
def monitor_symbol(symbol, amount):
    print(f"🔍 Monitoring {symbol}...")
    retry_count = 0
    while retry_count < 1000:
        if is_pair_live(symbol):
            print(f"{symbol} is live! Placing market order for {amount} USDT...")
            result = place_market_order(symbol, amount)
            print(f" Order Result for {symbol}:", result)
            break
        time.sleep(CHECK_INTERVAL + random.uniform(0.01, 0.03))
        retry_count += 1
    else:
        print(f"Timeout: {symbol} not launched after long wait.")
if __name__ == "__main__":
    print("🔧 Please enter USDT amount for each pair:")
    for symbol in SYMBOLS:
        try:
            amt = float(input(f"Enter USDT amount for {symbol}: "))
            PAIRS[symbol] = amt
        except ValueError:
            print(f"Invalid input for {symbol}, skipping.")
    threads = []
    for symbol, amount in PAIRS.items():
        t = threading.Thread(target=monitor_symbol, args=(symbol, amount))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    print(" Bot finished monitoring all pairs.")
