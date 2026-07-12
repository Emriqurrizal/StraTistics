from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'strava_incremental_sync',
    default_args=default_args,
    description='Daily sync of Strava activities, data quality validation, and dbt transformations',
    schedule_interval='0 2 * * *', # Runs daily at 2:00 AM
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['strava', 'daily', 'medallion'],
) as dag:

    # 1. Ingest from API (Bronze Layer)
    ingest_api_data = BashOperator(
        task_id='ingest_api_data',
        bash_command='cd /opt/airflow && python ingestion/daily_ingest.py',
    )

    # 2. Data Quality Check (Great Expectations)
    validate_bronze_silver = BashOperator(
        task_id='validate_bronze_silver',
        bash_command='cd /opt/airflow && python quality/run_validations.py',
    )

    # 3. Transform Data (dbt Silver and Gold Layers)
    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='cd /opt/airflow/dbt_strava && dbt run --profiles-dir .',
    )

    # Set dependencies
    ingest_api_data >> validate_bronze_silver >> dbt_run
