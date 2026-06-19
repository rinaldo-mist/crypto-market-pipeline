from datetime import datetime, timezone
from ingestion import coingecko_client, storage

def main():
    # 1. Fetch live prices — the SAME function the DAG calls (no duplicate logic)
    prices = coingecko_client.fetch_prices()

    # 2. Pick a storage backend. Local disk for dev — no GCP creds needed.
    backend = storage.LocalStorageBackend()

    # 3. No Airflow context here, so make the partition timestamp ourselves.
    partition_dt = datetime.now(timezone.utc)

    # 4. Write the records. write() returns the path it wrote to.
    path = backend.write(prices, partition_dt)

    # 5. Print feedback so a human running this knows it worked.
    print(f"Wrote {len(prices)} records to {path}")


if __name__ == "__main__":
    main()