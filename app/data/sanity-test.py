import requests
import os

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

url = "https://www.alphavantage.co/query"
params = {
    "function": "TIME_SERIES_DAILY",  # Note: NOT "DAILY_ADJUSTED"
    "symbol": "AAPL",
    "outputsize": "compact",
    "apikey": API_KEY
}

r = requests.get(url, params=params)
print(r.status_code)
print(r.json())
