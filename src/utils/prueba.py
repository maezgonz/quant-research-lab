import os
import requests

# Get your free apikey at https://www.alphavantage.co/support/#api-key and set ALPHAVANTAGE_API_KEY
api_key = os.getenv("ALPHAVANTAGE_API_KEY", "demo")
url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey={api_key}'
r = requests.get(url, timeout=15)
data = r.json()

print(data)