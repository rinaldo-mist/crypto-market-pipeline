import os

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator # no need if we are using cosmos
from cosmos import DbtTaskGroup, ProjectConfig, ProfileConfig, ExecutionConfig

from google.cloud import bigquery

from ingestion import coingecko_client, storage
from datetime import timedelta

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
dbt_profile = os.environ.get("DBT_PROFILE_TARGET")
storage_bucket = os.environ.get("STORAGE_BUCKET")

default_args = {
    "owner":"rs",
    "retries":3,
    "retry_delay": timedelta(hours=1),
    "email_on_failure":False
}

# TODO: define the three Cosmos config objects here:
#   project_config   = ProjectConfig(...)    -> "where is the dbt project?"
#   profile_config   = ProfileConfig(...)     -> "how do I connect?" (reuse profiles.yml)
#   execution_config = ExecutionConfig(...)   -> "how do I invoke dbt?"

project_config = ProjectConfig(
    dbt_project_path="/opt/airflow/dbt/crypto_pipeline"
)

profile_config = ProfileConfig(
    profile_name="crypto_pipeline",
    target_name=dbt_profile,
    profiles_yml_filepath="/opt/airflow/dbt/crypto_pipeline/profiles.yml"
)

execution_config = ExecutionConfig(
    dbt_executable_path="/opt/airflow/dbt_venv/bin/dbt" # dbt is in virtual environment to avoid dependency version conflicts with airflow
)

def _fetch_and_store(**context):
    # context from Airflow is a dict, contains key data_interval_start -> use this for partition_dt in write
    partition_dt = context["data_interval_start"]
    prices = coingecko_client.fetch_prices()
    storageAgent = storage.GCSStorageBackend(storage_bucket)
    return storageAgent.write(prices, partition_dt) # return string file path -> pass to next task via XCom

def _load_and_analyze(**context):
    # context from Airflow is a dict, contains key ti (task_id) -> use this for getting result from specific task, in this case, task "fetch_and_store"
    file_path = context["ti"].xcom_pull(task_ids="fetch_and_store") # get result from task_id "fetch_and_store" (see DAG)
    client = bigquery.Client()
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON, 
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND, 
        schema=[
                bigquery.SchemaField("coin_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("currency", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("price", "NUMERIC", mode="NULLABLE"),
                bigquery.SchemaField("market_cap", "NUMERIC", mode="NULLABLE"),
                bigquery.SchemaField("change_24h", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("volume_24h", "FLOAT64", mode="NULLABLE"),
                bigquery.SchemaField("last_updated", "INT64", mode="NULLABLE"),
                bigquery.SchemaField("fetched_at", "TIMESTAMP", mode="NULLABLE")
        ]
    )
    load_job = client.load_table_from_uri(
        file_path,
        f"{project_id}.crypto_raw.crypto_prices",
        job_config=job_config
        )
    load_job.result() # wait until job finished

with DAG(
    dag_id = "crypto_data_pipeline",
    schedule_interval=timedelta(hours=1),
    start_date=days_ago(1),
    catchup=False,
    default_args=default_args
) as dag:
    fetch_and_store = PythonOperator(
        task_id="fetch_and_store",
        python_callable=_fetch_and_store
    )
    load_and_analyze = PythonOperator(
        task_id="load_and_analyze",
        python_callable=_load_and_analyze
    )
    # dbt_build = BashOperator(
    #     task_id="dbt_build",
    #     bash_command=f"cd /opt/airflow/dbt/crypto_pipeline && dbt run --profiles-dir . --target {dbt_profile}"
    # )
    dbt_build = DbtTaskGroup(
        group_id="dbt_build",
        project_config=project_config,
        profile_config=profile_config,
        execution_config=execution_config
    )
    fetch_and_store >> load_and_analyze >> dbt_build