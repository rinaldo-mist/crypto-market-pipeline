select 
coin_id, 
currency, 
DATE(fetched_at) as fetched_at,
AVG(price) as avg_price, 
MAX(price) as max_price, 
MIN(price) as min_price, 
AVG(change_24h) as avg_change_24h, 
AVG(volume_24h) as avg_volume_24h
from {{ref('stg_crypto_prices')}}
group by 1,2,3