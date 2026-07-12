from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'strava_backfill',
    default_args=default_args,
    description='Manual trigger DAG to process bulk export files into the medallion architecture',
    schedule_interval=None, # Manual trigger only
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['strava', 'backfill', 'manual'],
) as dag:

    # 1. API Backfill Ingestion
    ingest_all_api_data = BashOperator(
        task_id='ingest_all_api_data',
        bash_command='cd /opt/airflow && python ingestion/api_backfill.py',
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
    ingest_all_api_data >> validate_bronze_silver >> dbt_run
