import json
from datetime import datetime
from typing import Protocol
from pathlib import Path
from google.cloud import storage as gcs

class StorageBackend(Protocol):
    def write(self, records: list[dict], partition_dt: datetime) -> str:
        ...

class LocalStorageBackend:
    def __init__(self, base_path: str = "data/bronze") -> None:
        self.base_path = Path(base_path)

    def write(self, records: list[dict], partition_dt: datetime) -> str:
        folder = self.base_path / "crypto_prices" / f"year={partition_dt.year}" / f"month={partition_dt.month:02d}" / f"day={partition_dt.day:02d}"
        folder.mkdir(parents=True, exist_ok=True)

        file_name = f"crypto_prices_{partition_dt.hour:02d}.json"
        file_path = folder / file_name

        with file_path.open("w", encoding="utf-8") as f:
            #json.dump(records, f, indent=2, default=str)
            f.write("\n".join(json.dumps(record, default=str) for record in records))

        return str(file_path)
    
class GCSStorageBackend:
    def __init__(self, bucket_name: str) -> None:
        self.bucket_name = bucket_name
        gcs_client = gcs.Client()
        self.bucket = gcs_client.bucket(bucket_name)

    def write(self, records: list[dict], partition_dt: datetime) -> str:
        folder = f"bronze/crypto_prices/year={partition_dt.year}/month={partition_dt.month:02d}/day={partition_dt.day:02d}"
        file_name = f"crypto_prices_{partition_dt.hour:02d}.json"
        blob_path = f"{folder}/{file_name}"
        blob = self.bucket.blob(blob_path)
        blob.upload_from_string(
            # json.dumps(records, default=str, indent=2),
            "\n".join(json.dumps(record, default=str) for record in records),
            content_type="application/json"
        )
        return f"gs://{self.bucket_name}/{blob_path}"