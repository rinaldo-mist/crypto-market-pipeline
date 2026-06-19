import httpx
from ingestion import coingecko_client

def test_fetch_prices(respx_mock):
    # mock API response from CoinGecko
    # Arrange: prepare the mock response and the expected result
    currencies = ["usd","idr","cny","jpy","eur","sgd"]
    btc = {}
    for c in currencies:
        btc[c] = 30000
        btc[c+"_market_cap"] = 600000000000
        btc[c+"_24h_change"] = 5.0
        btc[c+"_24h_vol"] = 10000000000
    btc["last_updated_at"] = 1710000000
    fake_response = {
        "bitcoin": btc
    }

    # Act: mock the API call and call fetch_prices
    respx_mock.get("https://api.coingecko.com/api/v3/simple/price").mock(
        return_value=httpx.Response(200, json=fake_response)
    )
    result = coingecko_client.fetch_prices()

    # Assert: check that the result has the expected structure and values
    assert isinstance(result, list)
    assert len(result) == len(currencies)
    for i, record in enumerate(result):
        assert record["coin_id"] == "bitcoin"
        assert record["currency"] == currencies[i] # testing order
        assert {r["currency"] for r in result} == set(currencies) # testing contract
        assert record["price"] == 30000