FROM apache/airflow:2.9.2
# for pip install
RUN pip install --no-cache-dir \
    httpx google-cloud-storage google-cloud-bigquery astronomer-cosmos \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.2/constraints-3.12.txt"
# for dbt virtual environment -> venv
RUN python -m venv /opt/airflow/dbt_venv && \
    /opt/airflow/dbt_venv/bin/pip install --no-cache-dir dbt-bigquery