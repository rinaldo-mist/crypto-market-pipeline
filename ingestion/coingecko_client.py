import httpx
from datetime import datetime, timezone

BASE_URL = "https://api.coingecko.com/api/v3"
# API_KEY = go to .env and add to docker compose, then access via os.environ.get("API_KEY") - but for this API, we can just use it without API key for demo purpose, see https://www.coingecko.com/en/api/pricing

# template :
# f"https://api.coingecko.com/api/v3/simple/price?vs_currencies=usd&ids=bitcoin&x_cg_demo_api_key={API_KEY}"

currencies = ["usd","idr","cny","jpy","eur","sgd"]

def fetch_coins():
    PATH = "/coins/list"
    response = httpx.get(BASE_URL+PATH)
    data = response.json()
    return [item["id"] for item in data]

def fetch_prices():
    #ids = fetch_coins() - ideal for retrieving all cryptocurrencies
    ids = ["bitcoin","ethereum","solana","binancecoin"]
    PATH = "/simple/price"
    CURRENCIES = ",".join(currencies)
    CRYPTO_IDS = ",".join(ids)
    params = {
                "vs_currencies":CURRENCIES, 
                "ids":CRYPTO_IDS,
                "include_market_cap":"true",
                "include_24hr_change":"true",
                "include_24hr_vol":"true",
                "include_last_updated_at":"true"
            }
    try:
        response = httpx.get(BASE_URL+PATH, params=params)
        response.raise_for_status()

        resp_body = response.json()
        nowtime = datetime.now(timezone.utc)

        result = []

        for k, v in resp_body.items():
            for currency in currencies:
                tmp = {}
                tmp["coin_id"] = k
                tmp["currency"] = currency
                tmp["price"] = v[currency]
                tmp["market_cap"] = v[currency+"_market_cap"]
                tmp["change_24h"] = v[currency+"_24h_change"]
                tmp["volume_24h"] = v[currency+"_24h_vol"]
                tmp["last_updated"] = v["last_updated_at"]
                tmp["fetched_at"] = nowtime
                result.append(tmp)

        return result
    except httpx.HTTPStatusError as ex:
        raise RuntimeError(f"Error response : {ex.response.status_code} with message {ex.response.text}") from ex
    except httpx.RequestError as ex:
        raise RuntimeError(f"Request error : {ex.request.url}") from ex