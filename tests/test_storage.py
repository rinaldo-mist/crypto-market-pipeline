from ingestion import storage
from datetime import datetime
from pathlib import Path
import json

def test_local_storage_write(tmp_path):
    # create a LocalStorageBackend instance with the temporary path
    storageAgent = storage.LocalStorageBackend(tmp_path)
    # AAA pattern: Arrange, Act, Assert
    # Arrange: prepare the test data and the storage agent
    records = [
        {"coin_id":"bitcoin","currency":"usd","price":30000},
        {"coin_id":"ethereum","currency":"usd","price":2000}
    ]
    partition_dt = datetime(2024, 6, 1, 12, 0, 0)
    # Act: write the records to storage
    result_path = storageAgent.write(records, partition_dt)
    # Assert: check that the file exists and has the expected content
    assert Path(result_path).exists()
    # each record is a line in the file
    assert Path(result_path).read_text().count("\n") + 1 == len(records)
    # content round-trip: read the file and parse the JSON lines back to dicts
    read_records = []
    with open(result_path, "r") as f:
        for line in f:
            read_records.append(json.loads(line.strip())) # use json.loads to convert string to dict
    assert read_records == records